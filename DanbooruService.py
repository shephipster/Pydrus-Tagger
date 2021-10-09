#Handles requests and actually getting the tags from Danbooru given either a url or an id

import requests

DANBOORU_URL = "https://danbooru.donmai.us/posts/{0}"

def getTagsFromId(id):
    resp = requests.get(DANBOORU_URL.format(str(id) + ".json"))
    respJson = resp.json()
    tags = str.split(respJson["tag_string"])
    return tags

def getTagsFromUrl(url):
    #TODO
    return