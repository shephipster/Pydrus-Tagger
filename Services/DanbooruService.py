#Handles requests and actually getting the tags from Danbooru given either a url or an id
import requests

import os
import aiohttp
import random
from dotenv import load_dotenv
load_dotenv()

DANBOORU_URL = "https://danbooru.donmai.us"
#DANBOORU_URL = "https://testbooru.donmai.us"    #This is the test server, use this one for now
API_KEY = os.getenv('DANBOORU_API_KEY')
USERNAME = os.getenv('DANBOORU_USERNAME')

async def validateLogin():
    url = f"https://{USERNAME}:{API_KEY}@danbooru.donmai.us/profile.json?"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            json_load = await r.json()
            r.close()
            return json_load

async def getTagsFromId(id):
    url = 'https://danbooru.donmai.us/posts/{0}'.format(str(id) + ".json")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            respJson = await r.json()
            r.close()

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
    # login_results = await validateLogin()
    # print(login_results)
    tagList = ""
    for tag in tags[0]:
        tagList += tag + " "

    tagList = tagList[:-1]
    url = "" + DANBOORU_URL + f"/posts.json?&tags=" + tagList + f"+random%3A500&api_key={API_KEY}&login={USERNAME}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            json_load = await r.json()
            r.close()
            return json_load


async def getRandomPostWithTags(*tags):    
    respJson = await getRandomSetWithTags(*tags)
    randPost = random.randint(0, len(respJson) -1 )
    post = respJson[randPost]
    return post