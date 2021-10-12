import os
import requests

from PIL import Image

from dotenv import load_dotenv
load_dotenv()

#This is assuming that Hydrus is running on the same machine
HYDRUS_URL = "http://127.0.0.1:45869/"
HYDRUS_KEY = os.getenv('HYDRUS_API_KEY')

header = {
    'Hydrus-Client-API-Access-Key': HYDRUS_KEY,
    'User-Agent' : "Pydrus-Client/1.0.0"
}

#Loads in the file and then saves it to a temp file. Returns the temp file
def getImageById(id):
    url = HYDRUS_URL + f"get_files/file?file_id={id}"
    res = requests.get(url, headers=header)

    fileType = getFileType(res.headers['Content-Type'])
    cwd = os.getcwd()
    fileName = f'{cwd}\\tempFiles\\temp{fileType}'

    if not os.path.exists('tempFiles'):
        os.makedirs('tempFiles')

    with open(fileName, 'wb') as tmp:
        for chunk in res.iter_content(128):
            tmp.write(chunk)
    return fileName

def getFileType(contentType):
    switcher = {
        'image/jpeg': '.jpg',
        'image/gif': '.gif',
        'image/png': '.png',
        'image/tiff': '.tiff',

        'application/zip':'.zip',

        'video/mpeg': '.mpeg',
        'video/mp4': '.mp4',
        'video/webm': '.webm',

        'text/html': '.html'
    }
    return switcher.get(contentType)

""" Returns the metadata of the file.
    Key values are: file_id, hash, size, mime, ext, width, height, 
        duration, has_audio, num_frames, num_words, is_inbox, is_local,
        is_trashed, known_urls[], service_names_to_statuses_to_tags,
        services_names_to_statuses_to_display_tags

        0- current, 1- pending, 2- deleted, 3-petitioned
        service_names_to_statuses_to_tags: {
            my tags: {
                0: []
                2: []
            }
            my tag repository: {
                0: []
                1: []
            }
        }

        service_names_to_statuses_to_display_tags: {
            my tags: {
                0: []
                2: []
            }
            my tag repository: {
                0: []
                1: []
            }
        }

        technically it takes a list, so need to use %5B for [,
        %5D for ], and %5C for ','
"""
def getMetaData(*ids):
    encodedIds = "%5B"
    for id in ids:
        encodedIds += str(id) + "%2C"
    encodedIds = encodedIds[:-3] + "%5D"

    url = HYDRUS_URL + "get_files/file_metadata?file_ids=" + encodedIds + "&detailed_url_information=true"

    res = requests.get(url, headers=header)
    return res

def getMeta(id):
    data = getMetaData(id)
    jsonData = data.json()
    meta = jsonData['metadata'][0]
    return meta
    

"""0- current, 1- pending, 2- deleted, 3-petitioned"""
def getTags(id):
    meta = getMeta(id)
    service_names_to_statuses_to_tags = meta['service_names_to_statuses_to_tags']['all known tags']['0']
    return service_names_to_statuses_to_tags

def getUrls(id):
    meta = getMeta(id)
    known_urls = meta['known_urls']
    return known_urls

""" Tags the tags and adds them to the local tag service"""
def addTags(id, *tags):
    hash = getMeta(id)['hash']
    url = HYDRUS_URL + "add_tags/add_tags"

    """ No idea why we couldn't just use *tags, or why taglist is going 2D
        but if we want to use it in the body this needs to be done
    """
    tagList = []
    for t in tags:
        tagList.append(t)
    tagList = tagList[0]
    """ The permitted 'actions' are:

    0 - Add to a local tag service.
    1 - Delete from a local tag service.
    2 - Pend to a tag repository.
    3 - Rescind a pend from a tag repository.
    4 - Petition from a tag repository. (This is special)
    5 - Rescind a petition from a tag repository."""

    body = {
        "hash": hash,
        "service_names_to_tags": {
            "my tags": tagList
        }
    }

    res = requests.post(url, json=body, headers=header)
    return res

def addKnownURLToFile(id, url):
    hash = getMeta(id)['hash']
    #Having to guess, but think known urls fall under tags
    targetUrl = HYDRUS_URL + "add_urls/associate_url"

    payload = {
        "hash": hash,
        "url_to_add": url
    }

    res = requests.post(targetUrl, json=payload, headers=header)
    return res

def addTag(id, tag):
    hash = getMeta(id)['hash']
    url = HYDRUS_URL + "add_tags/add_tags"
    tagList = [tag]

    body = {
        "hash": hash,
        "service_names_to_tags": {
            "my tags": tagList
        }
    }
    res = requests.post(url, json=body, headers=header)
    return res