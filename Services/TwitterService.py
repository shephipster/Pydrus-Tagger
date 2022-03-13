import requests
import os
from dotenv import load_dotenv

load_dotenv()

TWITTER_URL = "https://api.twitter.com/2/tweets/{}"
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

def create_headers(bearer_token = BEARER_TOKEN):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    return headers

def create_url(id):
    url = f'https://api.twitter.com/2/tweets/{id}?tweet.fields=entities'
    return url

def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def getTags(data):
    tags = set()

    if "hashtags" in data['entities'].keys():
        res = data['entities']['hashtags']
        for tag in res:
            tags.add(tag['tag'])    
    return tags

def getTagsFromId(id):
    url = create_url(id)
    headers = create_headers(BEARER_TOKEN)
    data = connect_to_endpoint(url, headers)

    #Check in case a tweet was deleted/not authorized
    if 'errors' in data.keys():
        return set()

    tags = getTags(data['data'])
    return tags