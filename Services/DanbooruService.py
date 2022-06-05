#Handles requests and actually getting the tags from Danbooru given either a url or an id

import os
import aiohttp
import random

import requests

DANBOORU_URL = "https://danbooru.donmai.us/"
#DANBOORU_URL = "https://testbooru.donmai.us"    #This is the test server, use this one for now
API_KEY = os.getenv('DANBOORU_API_KEY')
USERNAME = os.getenv('DANBOORU_USERNAME')

async def getTagsFromId(id):
    url = 'https://danbooru.donmai.us/posts/{0}'.format(str(id) + ".json")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as r:
            respJson = await r.json()

    tags = str.split(respJson["tag_string"])
    return tags

def getTagsFromIdSync(id):
    url = 'https://danbooru.donmai.us/posts/{0}'.format(str(id) + ".json")          
    respJson = requests.get(url).json()

    tags = str.split(respJson["tag_string"])
    return tags

def getTagsFromUrl(url):
    #TODO
    return

async def getRandomSetWithTags(*tags):
    tagList = ""
    for tag in tags[0]:
        tagList += tag + " "
    tagList = tagList[:-1]
    url = "" + DANBOORU_URL + f"/posts.json?tags=&random&api_key={API_KEY}&login={USERNAME}&tags=" + tagList
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as r:
            return await r.json()

async def getRandomPostWithTags(*tags):    
    respJson = await getRandomSetWithTags(*tags)
    randPost = random.randint(0, len(respJson) -1 )
    post = respJson[randPost]
    return post