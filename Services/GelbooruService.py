import requests
import random
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
    tagStr = ""

    if 'post' in respJson:
        items = respJson['post'][0].items()
        for i in items:
            if('tags' in i):
                tagStr = i[1]

    tags = set()

    #Gelbooru returns the results as an array since you can technically look up multiple things at once. This is to future-proof
    #things and prevent duplicate tags while getting them all, just in case this Service allows multiple concurrent lookups
    tagList = str.split(tagStr)
    for tag in tagList:
        tags.add(tag)

    return tags

def getRandomPostWithTags(*tags):
    tagList = ""
    for tag in tags[0]:
        tagList += tag + " "
    tagList = tagList[:-1]
    resp = requests.get("http://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=9999&tags=" + tagList)
    respJson = resp.json()
    if 'post' in respJson.keys():
        randPost = random.randint(0, len(respJson['post']) - 1)
        post = respJson['post'][randPost]
        return post
    else:
        print("Tag not found")
        return None