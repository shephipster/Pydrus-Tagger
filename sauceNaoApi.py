import requests
import os
import sys

from dotenv import load_dotenv
from Tagger import Tagger
from SauceNaoRequestObject import SauceNaoRequestObject


load_dotenv()

SAUCE_NAO_BASE = "https://saucenao.com/search.php"
API_KEY = os.getenv('SAUCE_NAO_API_KEY')
LIMIT = float(os.getenv('THRESHOLD'))

#runner method
def test():    
    snro = SauceNaoRequestObject(API_KEY)
    print(snro.getKey())

#Main runner, takes the url as a param and returns the set of all tags (no duplicates)
def getAllTags():
    if( len(sys.argv) < 2):
        print("Usage: python3 sauceNaoApi.py <url>")
    else:
        resp = fetchFromSauceNao(sys.argv[1])
        refs = getLinks(resp)
        dTags = Tagger.getDanbooruTags(refs["danbooru"])
        gTags = Tagger.getGelbooruTags(refs["gelbooru"])
        sTags = Tagger.getSankakuTags(refs["sankaku"])
        tTags = Tagger.getTwitterTags(refs["twitter"])
        pTags = Tagger.getPixivTags(refs["pixiv"])

        tags = set()

        #Add all tags to a set to prevent duplicates
        for t in dTags:
            tags.add(t)
        for t in gTags:
            tags.add(t)
        # for t in sTags:
        #      tags.add(t)
        for t in tTags:
            tags.add(t)
        # for t in pTags:
        #     tags.add(t)

        return tags


#Retrieve a response body from SauceNao after looking up the url
def fetchFromSauceNao(url):
    snro = SauceNaoRequestObject(API_KEY)
    snro.setUrl(url)

    payload = {'db': snro.getDb(), 'output_type': snro.getOutputType(), 
    'testmode':snro.getTestmode(), 'numres': snro.getNumres(), 
    'url': snro.getUrl(), 'api_key': snro.getKey()}

    r = requests.get(SAUCE_NAO_BASE, params = payload)

    responseJson = r.json()
    return responseJson

#Takes the json body of a saucenao request and returns a dict of all found (link: id)
def getLinks(body):
    pixivReferences = []
    danbooruReferences = []
    gelbooruReferences = []
    sankakuReferences = []
    twitterReferences = []

    results = body["results"]
    for r in results:
        if( float(r["header"]["similarity"]) > LIMIT):
            #Close enough of a match, start pulling urls and ids
            for u in r["data"]["ext_urls"]:
                if(u.__contains__("pixiv.net")):
                    pixivReferences.append( (u, r["data"]["pixiv_id"]) )
                elif(u.__contains__("twitter.com")):
                    twitterReferences.append( (u, r["data"]["tweet_id"]) )
                elif(u.__contains__("danbooru.donmai.us")):
                    danbooruReferences.append( (u, r["data"]["danbooru_id"]) )
                elif(u.__contains__("gelbooru.com")):
                    gelbooruReferences.append( (u, r["data"]["gelbooru_id"]) )
                elif(u.__contains__("chan.sankakucomplex.com")):
                    sankakuReferences.append( (u, r["data"]["sankaku_id"]) )

    references = {
        "pixiv": pixivReferences,
        "danbooru": danbooruReferences,
        "gelbooru": gelbooruReferences,
        "sankaku": sankakuReferences,
        "twitter": twitterReferences
    }

    return references


#Define an object that stores all the api data for a Danbooru request
class DanbooruRequestObject:
    def __init__(self, key):
        self.api_key = key

def main():
    tags = getAllTags()
    print(tags)


if __name__ == "__main__":
    main()