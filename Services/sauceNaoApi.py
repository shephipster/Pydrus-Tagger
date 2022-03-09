import requests
import os

from dotenv import load_dotenv
from Utilities.Tagger import Tagger


load_dotenv()

SAUCE_NAO_BASE = "https://saucenao.com/search.php"
API_KEY = os.getenv('SAUCE_NAO_API_KEY')
LIMIT = float(os.getenv('THRESHOLD'))
#8Mb = 8388608, 
FILE_SIZE_LIMIT_IN_BYTES = 20000000 #20mb

#Main runner, takes the url as a param and returns the set of all tags (no duplicates)
def getAllTagsFromUrl(url):
        resp = fetchURLFromSauceNao(url)
        refs = getLinks(resp)

        #supported DBs
        """ 
            - H-Magazines
            - H-Game CG
            - DoujinshiDB
            X pixiv
            - nico nico
            ✓ danbooru
            - drawr
            - nijie
            ✓ yande.re
            - shutterstock
            - fakku
            - H-Misc nH
            - 2D-market
            - MediBang
            - Anime
            - H-Anime
            - Movies
            - Shows
            ✓ Gelbooru
            - Konachan
            X Sankaku
            - Anime-Pictures.net
            ✓ e621
            - Idol Complex
            - bcy.net
            - PortalGraphics.net
            - deviantArt
            - Pawoo
            - Madokami
            - MangaDex
            - H-Misc eH
            - ArtStation
            - FurAffinity
            ✓ Twitter
            - Furry Network
        """

        dTags = Tagger.getDanbooruTags(refs["danbooru"])
        gTags = Tagger.getGelbooruTags(refs["gelbooru"])
        tTags = Tagger.getTwitterTags(refs["twitter"])
        eTags = Tagger.getE621Tags(refs["e621"])
        yTags = Tagger.getYandereTags(refs["yandere"])

        tags = set()

        #Add all tags to a set to prevent duplicates
        for t in dTags:
            tags.add(t)
        for t in gTags:
            tags.add(t)
        for t in tTags:
            tags.add(t)
        for t in eTags:
            tags.add(t)
        for t in yTags:
            tags.add(t)

        return tags

def getAllTagsFromFile(file):

    body = fetchFileFromSauceNao(file)
    links = getLinks(body)
    return getTagsFromLinks(links)

def getTagsFromLinks(links):
    tags = set()
    dTags = Tagger.getDanbooruTags(links["danbooru"])
    gTags = Tagger.getGelbooruTags(links["gelbooru"])
    tTags = Tagger.getTwitterTags(links["twitter"])
    eTags = Tagger.getE621Tags(links["e621"])
    yTags = Tagger.getYandereTags(links["yandere"])

    for t in dTags:
        tags.add(t)
    for t in gTags:
        tags.add(t)
    for t in tTags:
        tags.add(t)
    for t in eTags:
        tags.add(t)
    for t in yTags:
        tags.add(t)

    return tags

def fetchFileFromSauceNao(file):
    snro = {
        'output_type': 2,
        'key': API_KEY,
        'testmode': True,
        'dbmask': 0,
        'dbmaski': 0,
        'db': 999,
        'numres': 16,
        'dedupe': 2,
        'url': "",
    }

    payload = {'db': snro['db'], 'output_type': snro['output_type'], 
    'testmode':snro['testmode'], 'numres': snro['numres'], 
    'api_key': snro['key']}

    body = { 
        'file': (os.path.basename(file), open(file, 'rb'))
     } 

    r = requests.post(SAUCE_NAO_BASE, params = payload, files=body)

    responseJson = r.json()
    if responseJson['header']['status'] == -2:
        #Ran out of searched, throw error
        raise OutOfSearchesException

    if responseJson['header']['status'] == -4:
        #For some reason the image was not accepted
        #I've not figured out why this happens sometimes with perfectly valid files, but it just does
        raise ImageNotAcceptedException

    if responseJson['header']['status'] == -6:
        #Image was too small in dimensions, not allowed
        raise ImageNotAcceptedException


    return responseJson



#Retrieve a response body from SauceNao after looking up the url
def fetchURLFromSauceNao(url):
    snro = {
        'output_type': 2,
        'key': API_KEY,
        'testmode': True,
        'dbmask': 0,
        'dbmaski': 0,
        'db': 999,
        'numres': 16,
        'dedupe': 2,
        'url': url,
    }

    payload = {'db': snro['db'], 'output_type': snro['output_type'], 
    'testmode':snro['testmode'], 'numres': snro['numres'], 
    'api_key': snro['key'], 'url': snro['url']}

    r = requests.get(SAUCE_NAO_BASE, params = payload)

    responseJson = r.json()
    return responseJson

def getAllFromFile(path):
    body = fetchFileFromSauceNao(path)
    links = getLinks(body)
    tags = getTagsFromLinks(links)
    results = {
        "links": links,
        "tags": tags
    }
    return results


#Takes the json body of a saucenao request and returns a dict of all found (link: id)
def getLinks(body):
    pixivReferences = []
    danbooruReferences = []
    gelbooruReferences = []
    sankakuReferences = []
    twitterReferences = []
    e621References = []
    yandereReferences = []
    animePicturesReferences = []
    remainingReferences = []

    results = body["results"]

    for r in results:
        if( float(r["header"]["similarity"]) >= LIMIT):
            data = r["data"]
            if 'ext_urls' in data.keys():
            #Close enough of a match, start pulling urls and ids
                for u in data["ext_urls"]:
                    if(u.__contains__("pixiv.net")):
                        pixivReferences.append( (u, data["pixiv_id"]) )
                    elif(u.__contains__("twitter.com")):
                        twitterReferences.append( (u, data["tweet_id"]) )
                    elif(u.__contains__("danbooru.donmai.us")):
                        danbooruReferences.append( (u, data["danbooru_id"]) )
                    elif(u.__contains__("gelbooru.com")):
                        gelbooruReferences.append( (u, data["gelbooru_id"]) )
                    elif(u.__contains__("chan.sankakucomplex.com")):
                        sankakuReferences.append( (u, data["sankaku_id"]) )
                    elif(u.__contains__("e621.net")):
                        e621References.append( (u, data["e621_id"]))
                    elif(u.__contains__("yande.re")):
                        yandereReferences.append( (u, data["yandere_id"]))
                    elif(u.__contains__("anime-pictures.net")):
                        animePicturesReferences.append( (u, data["anime-pictures_id"]))
                    else:
                        remainingReferences.append(u)

    references = {
        "pixiv": pixivReferences,
        "danbooru": danbooruReferences,
        "gelbooru": gelbooruReferences,
        "sankaku": sankakuReferences,
        "twitter": twitterReferences,
        "e621": e621References,
        "yandere": yandereReferences,
        "animePictures": animePicturesReferences,
        "remainingReferences": remainingReferences
    }

    return references

class OutOfSearchesException(Exception):
    pass

class ImageNotAcceptedException(Exception):
    pass
