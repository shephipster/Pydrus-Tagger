import requests
#import os
#from dotenv import load_dotenv

#load_dotenv()

GELBOORU_URL = "http://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&id={0}{1}"

#Don't think the key is needed for GET
#GELBOORU_KEY = os.getenv('GELBOORU_API_KEY')

def getTagsFromId(id):
    #finalString = GELBOORU_URL.format(GELBOORU_KEY, id)
    finalString = GELBOORU_URL.format(id, '')
    resp = requests.get(finalString)
    respJson = resp.json()

    tags = set()

    #Gelbooru returns the results as an array since you can technically look up multiple things at once. This is to future-proof
    #things and prevent duplicate tags while getting them all, just in case this Service allows multiple concurrent lookups
    for entry in respJson:
        tagList = str.split(entry['tags'])
        for tag in tagList:
            tags.add(tag)

    return tags
