import requests
import pandas as pd
import json
import ast  # Abstract syntax trees
import yaml
from pprint import pprint # format JSON response
import os

# Tutorial: https://developer.twitter.com/en/docs/tutorials/how-to-analyze-the-sentiment-of-your-own-tweets

def create_twitter_url():
    handle = "jessicagarson"
    max_results = 100  # between 1 and 100
    mrf = "max_results={}".format(max_results)
    q = "query=from:{}".format(handle)
    url = "https://api.twitter.com/2/tweets/search/recent?{}&{}".format(
        mrf, q
    )
    return url

# Reads in YAML file and saves contents
def process_yaml():
    with open('config.yaml') as file:
        return yaml.safe_load(file)
      
# Take in config file and return bearer_token
def create_bearer_token(data):
  return data['search_tweets_api']['bearer_token']

# To connect to Twitter API
# Format headers to pass into bearer_token + url
# Connect to Twitter API using request package to make GET request
# Returns: JSON of the GET request
def twitter_auth_and_connect(bearer_token, url):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    response = requests.request('GET', url, headers = headers)
    return response.json()
  
# Input: JSON of GET request
# Returns: AST of data (dictionary?)
def lang_data_shape(res_json):
    data_only = res_json["data"]
    doc_start = '"documents": {}'.format(data_only)
    str_json = "{" + doc_start + "}"
    dump_doc = json.dumps(str_json)
    doc = json.loads(dump_doc)
    return ast.literal_eval(doc)
  
# Set up URLs for retriving data from languages and sentiment endpoints
# Credentials passed in to authenticate Azure endpoints
def connect_to_azure(data):
    azure_url = "https://week.cognitiveservices.azure.com/"
    language_api_url = "{}text/analytics/v2.1/languages".format(azure_url)
    sentiment_url = "{}text/analytics/v2.1/sentiment".format(azure_url)
    subscription_key = data["azure"]["subscription_key"]
    return language_api_url, sentiment_url, subscription_key
  
# Create header for connecting to Azure by passing in subscription key into
# format needed to make request 
def azure_header(subscription_key):
    return {"Ocp-Apim-Subscription-Key": subscription_key}
  
# Make POST request to Azure API to generate languages for Tweets
# Returns: JSON response
def generate_languages(headers, language_api_url, documents):
    response = requests.post(language_api_url, headers=headers, json=documents)
    return response.json()
  
# Only want abbreviations of the language, getting iso6391Name which contains 
# abbreviations of the languages
# Turn Tweet data into data frame and attach abbreviation for languages of your
# Tweets to that same data frame 
# Returns: Tweet data into JSON format
def combine_lang_data(documents, with_languages):
    langs = pd.DataFrame(with_languages["documents"])
    lang_iso = [x.get("iso6391Name")
                for d in langs.detectedLanguages if d for x in d]
    data_only = documents["documents"]
    tweet_data = pd.DataFrame(data_only)
    tweet_data.insert(2, "language", lang_iso, True)
    json_lines = tweet_data.to_json(orient="records")
    return json_lines
  
# Obtain sentiment scores
# Returns: AST in right format to call Azure sentiment endpoint
def add_document_format(json_lines):
    docu_format = '"' + "documents" + '"'
    json_docu_format = "{}:{}".format(docu_format, json_lines)
    docu_align = "{" + json_docu_format + "}"
    jd_align = json.dumps(docu_align)
    jl_align = json.loads(jd_align)
    return ast.literal_eval(jl_align)
  
# Make POST request to predefined sentiment endpoint 
def sentiment_scores(headers, sentiment_url, document_format):
  response = requests.post(sentiment_url, headers=headers, json=document_format)
  return response.json()

# Turn JSON response from Azure sentiment endpoint into DF and calculate mean
def mean_score(sentiments):
    sentiment_df = pd.DataFrame(sentiments["documents"])
    return sentiment_df["score"].mean()
  
def week_logic(week_score):
    if week_score > 0.75 or week_score == 0.75:
        print("You had a positive week")
    elif week_score > 0.45 or week_score == 0.45:
        print("You had a neutral week")
    else:
        print("You had a negative week, I hope it gets better")
  
def main():
    url = create_twitter_url()
    data = process_yaml()
    bearer_token = create_bearer_token(data)
    res_json = twitter_auth_and_connect(bearer_token, url)
    documents = lang_data_shape(res_json)
    language_api_url, sentiment_url, subscription_key = connect_to_azure(data)
    headers = azure_header(subscription_key)
    with_languages = generate_languages(headers, language_api_url, documents)
    json_lines = combine_lang_data(documents, with_languages)
    document_format = add_document_format(json_lines)
    sentiments = sentiment_scores(headers, sentiment_url, document_format)
    week_score = mean_score(sentiments)
    print(week_score)
    week_logic(week_score)
  

if __name__ == '__main__':
    main()
