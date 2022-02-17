import os
import requests

from PIL import Image

from dotenv import load_dotenv
load_dotenv()

#This is assuming that Hydrus is running on the same machine
HYDRUS_URL = os.getenv("HYDRUS_URL")
HYDRUS_KEY = os.getenv('HYDRUS_API_KEY')

header = {
    'Hydrus-Client-API-Access-Key': HYDRUS_KEY,
    'User-Agent' : "Pydrus-Client/1.0.0"
}

def getAllFileIds():
    url = HYDRUS_URL + f"get_files/search_files?"
    res = requests.get(url, headers=header)
    ids = res.json()['file_ids']
    return sorted(ids)

def getAllFileHashes():
    ids = getAllFileIds()
    hashes = []
    for id in ids:
        hash = getMeta(id)['hash']
        print("%s : %s" % (id, hash))
        hashes.append(hash)


def getPage(start, range):
    allIds = getAllFileIds()
    page = list(filter(lambda id: id >= start, allIds))[:range]
    return page

def getNextPageStart(lastPage):
    return getPage(lastPage[-1], 2)[-1]

def getReversePage(start, range):
    allIds = getAllFileIds()
    page = list(filter(lambda id: id > start, allIds))[:range]
    return page

def getReverseNextPageStart(lastPage):
    return getReversePage(lastPage[0], 2)[-1]

def getLastId():
    url = HYDRUS_URL + f"get_files/search_files?tags=[\"system:limit=1\"]"
    res = requests.get(url, headers=header)
    body = res.json()
    id = body['file_ids'][0]
    return id

#Loads in the file and then saves it to a temp file. Returns the temp file
def getImageById(id):

    #commented out to save on API calls to Hydrus, P-Tagger handles this check
    # if getLastId() < id:
    #     return None

    url = HYDRUS_URL + f"get_files/file?file_id={id}"
    res = requests.get(url, headers=header)

    if(res.headers['Content-Type'] == "text/html"):
        if (res.headers['Content-Length'] == '44' or res.headers['Content-Length'] == '25'):
            return None

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
    service_names_to_statuses_to_tags = meta['service_names_to_statuses_to_tags']['all known tags']
    if '0' in service_names_to_statuses_to_tags.keys():
        tags = service_names_to_statuses_to_tags['0']
        #For some reason, some seem to have it all in 2, even though that's deleted stuff
    elif '2' in service_names_to_statuses_to_tags.keys():
        tags = service_names_to_statuses_to_tags['2']
    return tags

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

def addTagByHash(hash, tag):
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

def addKnownURLToFileByHash(hash, url):
    #Having to guess, but think known urls fall under tags
    targetUrl = HYDRUS_URL + "add_urls/associate_url"

    payload = {
        "hash": hash,
        "url_to_add": url
    }

    res = requests.post(targetUrl, json=payload, headers=header)
    return res

def uploadURL(url, title = "Pydrus"):
    """ Uploads a URL to Hydrus to let installed parsers do the work """
    hydrus_url = HYDRUS_URL + "add_urls/add_url"
    body = {
        "url": url,
        "destination_page_name": title
    }

    res = requests.post(hydrus_url, json=body, headers=header)
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

""" Deletes a tag and adds the new one
    Mostly useful for tag 'cleaning', removing
    hashtags from Twitter and percent-encoded tags
    This does NOT push tags to PTR
"""
def updateTag(id, oldTag, newTag):

    if oldTag == newTag:
        return #same thing, why bother

    hash = getMeta(id)['hash']
    url = HYDRUS_URL + "add_tags/add_tags"
    body = {
        "hash": hash,
        "service_names_to_tags": {
            "my tags": {
                "0": newTag,
                "1": oldTag
            }
        }
    }
    return

def fileExists(id):
    res = getMetaData(id)
    if res.status_code != 200:
        return False
    else:
        return True

def getImageByHash(hash):

    #commented out to save on API calls to Hydrus, P-Tagger handles this check
    # if getLastId() < id:
    #     return None

    url = HYDRUS_URL + f"get_files/file?hash={hash}"
    res = requests.get(url, headers=header)

    if(res.headers['Content-Type'] == "text/html"):
        if (res.headers['Content-Length'] == '44' or res.headers['Content-Length'] == '25'):
            return None

    fileType = getFileType(res.headers['Content-Type'])
    cwd = os.getcwd()
    fileName = f'{cwd}\\tempFiles\\temp{fileType}'

    if not os.path.exists('tempFiles'):
        os.makedirs('tempFiles')

    with open(fileName, 'wb') as tmp:
        for chunk in res.iter_content(128):
            tmp.write(chunk)
    return fileName