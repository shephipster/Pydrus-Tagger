import requests
# import os
from dotenv import load_dotenv

load_dotenv()

#so while there is a mildly extensive API for e621, turns out you can literally just put .json
#at the end of the id and call it a day
E621_URL = "https://e621.net/posts/{}.json"

#Keys only needed if writing. Only calling GET, so don't need them.
#E621_KEY = os.getenv('E621_API_KEY') 
#E621_LOGIN = os.getenv('E621_LOGIN')

def getTagsFromId(id):
    tags = set()
    finalString = E621_URL.format(id)

    #params = {'login': E621_LOGIN, 'api_key': E621_KEY}
    headers = {
        'User-Agent': 'PydrusTagger/1.0 (by shephipster)'
    }
    resp = requests.get(finalString, headers=headers)
    respJson = resp.json()
    post = respJson['post']
    postTags = post['tags']

    for type in postTags:
        for tag in postTags[f'{type}']:
            tags.add(tag)

    return tags
