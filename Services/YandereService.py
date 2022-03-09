import requests
#import os
import sys
from dotenv import load_dotenv

load_dotenv()

#for some reason you can't search by id, but the id is a tag and
# you can search by tags... Makes no sense, but whatever
YANDERE_URL = "http://yande.re/post.json?tags=id:{}"

#Don't think the key is needed for GET
#YANDERE_KEY = os.getenv('YANDERE_API_KEY')

def getTagsFromId(id):
    #finalString = YANDERE_URL.format(YANDEREU_KEY, id)
    finalString = YANDERE_URL.format(id, '')
    resp = requests.get(finalString)
    respJson = resp.json()

    tags = set()

    for entry in respJson:
        tagList = str.split(entry['tags'])
        for tag in tagList:
            tags.add(tag)

    return tags