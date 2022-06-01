#Handles requests and actually getting the tags from Danbooru given either a url or an id

from urllib import response
import requests
import random

DANBOORU_URL = "https://danbooru.donmai.us/"
#DANBOORU_URL = "https://testbooru.donmai.us"    #This is the test server, use this one for now

def getTagsFromId(id):
    resp = requests.get('https://danbooru.donmai.us/posts/{0}'.format(str(id) + ".json"))
    respJson = resp.json()
    tags = str.split(respJson["tag_string"])
    return tags

def getTagsFromUrl(url):
    #TODO
    return

def getRandomSetWithTags(*tags):
    tagList = ""
    for tag in tags[0]:
        tagList += tag + " "
    tagList = tagList[:-1]
    resp = requests.get("" + DANBOORU_URL + "/posts.json?tags=" + tagList)
    respJson = resp.json()
    return respJson

def getRandomPostWithTags(*tags):    
    tagList = ""
    for tag in tags[0]:
        tagList += tag + " "
    tagList = tagList[:-1]
    resp = requests.get("" + DANBOORU_URL + "/posts.json?tags=" + tagList)
    respJson = resp.json()
    randPost = random.randint(0, len(respJson) -1 )
    post = respJson[randPost]
    return post