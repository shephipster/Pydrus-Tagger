import os
import requests
import io

from dotenv import load_dotenv
load_dotenv()

#This is assuming that Hydrus is running on the same machine
HYDRUS_URL = os.getenv("HYDRUS_URL")
HYDRUS_KEY = os.getenv('HYDRUS_API_KEY')
#4096 caused errors, but 1024 seems to be acceptable.
#Lower it if you have problems until the connection stops dropping
PAGE_SIZE = 1024

header = {
    'Hydrus-Client-API-Access-Key': HYDRUS_KEY,
    'User-Agent': "Pydrus-Client/1.0.0"
}

# Overhaul of the API, going to clean this up and make the function names make a lot more sense
# This is basically a 1-to-1 python copy of https://hydrusnetwork.github.io/hydrus/developer_api.html
# also check out https://gitlab.com/cryzed/hydrus-api , the "official" Python Hydrus API
### Access Management

# GET /api_version


def get_api_version():
    """ Returns, in this order, the api_version and hydrus_version of the connected instance """
    url = HYDRUS_URL + "api_version"
    res = requests.get(url, headers=header)
    json = res.json()
    api_version, hydrus_version = json['version'], json['hydrus_version']
    return api_version, hydrus_version
# GET /request_new_permissions


def request_new_permissions(name: str, basic_permissions: list):
    """ Takes a name and a list of permissions"""
    pass


def get_permission_list(import_urls=False, import_files=False, add_tags=False, search_for_files=False, manage_pages=False, manage_cookies=False, manage_database=False):
    """ 
    Helps to get the list of basic_permissiosn for request_new_permissions. Pass True for the permissions you need/want
    Returns a list of basic_permissions that can be passed directly to request_new_permissions
    """
    basic_permissions = []
    if import_urls:
        basic_permissions.append(0)
    if import_files:
        basic_permissions.append(1)
    if add_tags:
        basic_permissions.append(2)
    if search_for_files:
        basic_permissions.append(3)
    if manage_pages:
        basic_permissions.append(4)
    if manage_cookies:
        basic_permissions.append(5)
    if manage_database:
        basic_permissions.append(6)
    return basic_permissions
# GET /session_key


def get_session_key():
    """ Returns a string of a new session key in hex """
    pass
# GET /verify_access_key


def verify_access_key():
    """ Returns a dictionary that contains the error code (if any) and the permission info (if no error)
        Format is {'error_code', 'basic_permissions','human_decscription'}
    """
    pass
# GET /get_services


def get_services():
    """ Returns a dictionary of all the file and tag services, including their name and service key"""
    pass
### Adding Files
# POST /add_files/add_file


def add_file_by_path(path_to_file: str):
    """ Adds a file to the client for importing, given a string representation of the path to the file"""
    pass


def add_file_by_stream(data: bytes):
    """ Adds a file to the client for importing, given the raw file (via its bytes representation)
        
        Args:
            data(bytes): A bytes sequence that is the entirety of the file to be sent to Hydrus

        Returns:
            result(dict): A dictionary detailing the result of the operation. Format is as follows:
            {
                "status": 1/2/3/4/7,
                "hash": "1234567890abcdef...",
                "note": ""
            }
            
        Notes:
            status: One of the following values, as an integer
                1: File was successfully imported
                2: File already in database
                3: File previously deleted
                4: File failed to import
                7: File vetoed
            hash: A string representation of the SHA256 hash in hexadecimal
            note: A string representation of any notes Hydrus returns. An error will have the full traceback here
    """
    pass
# POST /add_files/delete_files


def delete_files(file_service_name: str = "", file_service_key: str = "", reason: str = "", *hashes: str):
    """ Deletes a set of files from given services
    Args:
        file_service_name(str): The name of the file_service to delete the file(s) from. May be left blank to delete from all local files
        file_service_key(str): Hexadecimal string of the service to delete the file(s) from. May be left blank to delete from all local files
        reason(str): A string explaining why the file was deleted. May be left blank
        *hashes(str): A sequence of hexadecimal strings denoting which file(s) are to be deleted.

    Returns:
        result: True if the operation completed with no issue, false otherwise
    """
    pass

# POST /add_files/undelete_files


def undelete_files(file_service_name: str = "", file_service_key: str = "", *hashes: str):
    """ Deletes a set of files from given services
    Args:
        file_service_name(str): The name of the file_service to recover the file(s) from.
        file_service_key(str): Hexadecimal string of the service to recover the file(s) from.
        *hashes(str): A sequence of hexadecimal strings denoting which file(s) to be recovered.

    Returns:
        result: True if the operation completed with no issue, false otherwise
    """
    pass
# POST /add_files/archive_files


def archive_files(*hashes: str):
    """ Archives file(s) 
    Args:
        *hashes(str): A sequence of strings that are the hexadecimal SHA256 hashes of the files to archive

    Returns:
        result: True if the operation completed with no issue, false otherwise
    """
    pass
# POST /add_files/unarchive_files


def unarchive_files(*hashes: str):
    """ Unarchives file(s) 
    Args:
        *hashes(str): A sequence of strings that are the hexadecimal SHA256 hashes of the files to unarchive

    Returns:
        result: True if the operation completed with no issue, false otherwise
    """
    pass
### Adding Tags
# GET /add_tags/clean_tags


def clean_tags(*tags: str):
    """ Asks the client about how it will see certain tags and cleans them
    Cleaning mostly involves removing whitespace, dealing with 'system', hypen-started tags, and things that start with ':', such as " :) "
    Args:
        *tags(str): A list of tags you wish to have cleaned. 

    Returns:
        a list of all the tags in their cleaned state in sorted order
    """
    pass
# GET /add_tags/get_tag_services


def get_tag_services():
    """ Returns a list of the local tags and tag repository services 
    Returns:
        a list of of the local tags services, and a list of the tag repositories
    """
    pass
# GET /add_tags/search_tags


def search_tags(tag: str):
    """
    Searchs the client for specific tags that contain a specific tag as a substring
    Returns:
        a list of all the tags that contain the substring, with content of
        {
            "value": str,
            "count": int
        }
    """
    pass
# POST /add_tags/add_tags
### Adding URLs
# GET /add_urls/get_url_files


def get_url_files(url: str):
    """Ask the client about a URL's files
    Returns:{
        "normalized_url":str,
        "url_file_statuses":[
            {
                "status":int,
                "hash": str,
                "note": str
            }
        ]
    }
    """
    pass
# GET /add_urls/get_url_info


def get_url_info(url: str):
    """Ask the client for information about a URL
    Returns:{
        "normalized_url":str,
        "url_type": int,
        "url_type_string" : str,
        "match_name" : str,
        "can_parse": true
    }
    """
    pass
# POST /add_urls/add_url


def add_url(url: str, destination_page_key: str = "", destination_page_name: str = "", show_destination_page:bool=False, 
    service_names_to_additional_tags: dict = {}, service_keys_to_additional_tags:dict={}, filterable_tags:list=[]):
    """ Add a url to Hydrus to be imported, identical to drag-and-dropping the url into the client
    Params:
        url(str): The url for the client to import
        destination_page_key(str): The key of a specific page to add the url to, may be left blank
        desitnation_page_name(str): The name of a specific page to add the url to, may be left blank
        show_destination_page(bool): Tells the client if it should change the ui to focus on the destination page
        service_names_to_additional_tags(dict): Selective tags to add to all files imported from the url
        service_keys_to_additional_tags(dict): selective tags to give to any files imported from this url
        filterable_tags(list): tags to be filtered by any tag import options that applies to the url

    Returns:
        {
            "human_result_text": str,
            "normalized_url": str
        }
    """
    pass
# POST /add_urls/associate_url
def associate_url(url_to_add:str="", urls_to_add:list=[], url_to_delete:str="", urls_to_delete:list=[], hash:str="", hashes:list=[], file_id:int=-1, file_ids:list=[]):
    """ 
    Manage which URLs the client considers to be associated with which files. All parameters are optional, but you must include at least one url and one hash.
    It is recommended to use a single hash at a time, but multiple may be done at once.
    Params:
        url_to_add: (an url you want to associate with the file(s))
        urls_to_add: (a list of urls you want to associate with the file(s))
        url_to_delete: (an url you want to disassociate from the file(s))
        urls_to_delete: (a list of urls you want to disassociate from the file(s))
        hash: (an SHA256 hash for a file in 64 characters of hexadecimal)
        hashes: (a list of SHA256 hashes)
        file_id: (a numerical file id)
        file_ids: (a list of numerical file ids)

    Returns: True if successful, false otherwise
    """
    pass
### Adding Notes
# POST /add_notes/set_notes
# POST /add_notes/delete_notes
# Managing Cookies and HTTP Headers
# GET /manage_cookies/get_cookies
# POST /manage_cookies/set_cookies
# POST /manage_headers/set_user_agent
### Managing Pages
# GET /manage_pages/get_pages
# GET /manage_pages/get_page_info
# POST /manage_pages/add_files
# POST /manage_pages/focus_page
### Searching Files
# GET /get_files/search_files
# GET /get_files/file_metadata
# GET /get_files/file
# GET /get_files/thumbnail
### Managing the Database
# POST /manage_database/lock_on
# POST /manage_database/lock_off
# GET /manage_database/mr_bones


###########################    LEGACY CODE: Only here so older code doesn't break on an update      ##########################################
def getAllFileIds():
    """ Returns a sorted list of all the file ids the client has"""
    url = HYDRUS_URL + f"get_files/search_files?"
    res = requests.get(url, headers=header)
    ids = res.json()['file_ids']
    return sorted(ids)


def getAllFileHashes():
    """ Returns a sorted list of all the file hashes the client has"""
    url = HYDRUS_URL + "get_files/search_files?&return_hashes=true"
    res = requests.get(url, headers=header)
    hashes = res.json()['hashes']
    return sorted(hashes)


def getAllMainFileData():
    """ Returns a set of all the main data for all files the client has. This is a good amount of information so be
    a bit sparing in using this. Main data includes {'file_id', 'hash', 'size', 'width', 'height', 'mime'} """
    ids = getAllFileIds()
    pagedIds = list()
    data = dict()
    length = len(ids)
    count = 0

    for i in range(0, length, PAGE_SIZE):
        pagedIds.append(ids[i:i+PAGE_SIZE])

    for page in pagedIds:
        meta = getMetaData(*page).json()['metadata']
        for entry in meta:
            data[count] = {
                'file_id': entry['file_id'],
                "hash": entry['hash'],
                "size": entry['size'],
                "width": entry['width'],
                "height": entry['height'],
                "mime": entry['mime']
            }
            count = count + 1
    return data


def getPage(start, range):
    """ Returns a list of all the ids the client has that fall in a certain range (smaller ids to larger). Useful for pagination to an extent"""
    allIds = getAllFileIds()
    page = list(filter(lambda id: id >= start, allIds))[:range]
    return page


def getNextPageStart(lastPage: list):
    """ Returns the first file id in what would be the next page given a previous page list. Useful for pagination to an extent"""
    return getPage(lastPage[-1], 2)[-1]


def getReversePage(start, range):
    """ Returna a list of all the ids the client has that fall in a certain range, going in reverse (larger ids to smaller)"""
    allIds = getAllFileIds()
    page = list(filter(lambda id: id > start, allIds))[:range]
    return page


def getReverseNextPageStart(lastPage):
    """ Returns the first file id in what would be the next page given a previous reverse page list. Useful for pagination to an extent"""
    return getReversePage(lastPage[0], 2)[-1]


def getLastId():
    """ Returns the last/largest file id in the system. Useful in the event you're navigating by ids instead of hash, but don't do that"""
    url = HYDRUS_URL + f"get_files/search_files?tags=[\"system:limit=1\"]"
    res = requests.get(url, headers=header)
    body = res.json()
    id = body['file_ids'][0]
    return id


def getImageById(id):
    """ Returns a string file path to a copy of a file in the system. Finds the image with the given id and, if it exists
    makes a local copy called temp(.gif/.jpg/.png...) and then returns the path to that temp file."""

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
    """ Returns the file ending of a file given the contentType. """
    switcher = {
        'image/jpeg': '.jpg',
        'image/gif': '.gif',
        'image/png': '.png',
        'image/tiff': '.tiff',

        'application/zip': '.zip',

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
    """ Gets a list of all the meta data for all given files by their id"""
    encodedIds = "%5B"
    for id in ids:
        encodedIds += str(id) + "%2C"
    encodedIds = encodedIds[:-3] + "%5D"

    url = HYDRUS_URL + "get_files/file_metadata?file_ids=" + \
        encodedIds + "&detailed_url_information=true"

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


def uploadURL(url, title="Pydrus"):
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
        return  # same thing, why bother

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
    res = requests.post(url, json=body)
    return


def fileExists(id):
    res = getMetaData(id)
    if res.status_code != 200:
        return False
    else:
        return True

def getImageBytesByHash(hash):
    url = HYDRUS_URL + f"get_files/file?hash={hash}"
    res = requests.get(url, headers=header)

    if(res.headers['Content-Type'] == "text/html"):
        if (res.headers['Content-Length'] == '44' or res.headers['Content-Length'] == '25'):
            return None

    return io.BytesIO(res.content)

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


def getMetaFromHash(hash):
    url = HYDRUS_URL + "get_files/file_metadata?hashes=%5B%22" + \
        hash + "%22%5D&detailed_url_information=true"
    res = requests.get(url, headers=header)

    if(res.headers['Content-Type'] == "text/html"):
        if (res.headers['Content-Length'] == '44' or res.headers['Content-Length'] == '25'):
            return None

    return res.json()['metadata'][0]

def getAllFilesOfType(fileType:str):
    url = HYDRUS_URL + 'get_files/search_files?tags=%5B%22system%3Afiletype%20is%20'+ fileType +'%22%5D&return_hashes=true'
    res = requests.get(url, headers=header)

    if(res.headers['Content-Type'] == "text/html"):
        if (res.headers['Content-Length'] == '44' or res.headers['Content-Length'] == '25'):
            return None

    return res.json()['hashes']

def addHashesToPage(pageTitle='Pydrus', *hashes):
    key = getPageKey(pageTitle)
    body = {
        "page_key": key,
        "hashes": [*hashes]
    }
    url = HYDRUS_URL + 'manage_pages/add_files'

    res = requests.post(url, headers=header, json=body)
    return

def getPageKey(pageTitle):
    #Either focus the page or create it if it doesn't exist
    uploadURL("https://hydrusnetwork.github.io/hydrus/developer_api.html", title=pageTitle) 
    #need to send some page to Hydrus, might as well use the API guide

    url = HYDRUS_URL + 'manage_pages/get_pages'
    res = requests.get(url, headers=header)
    pages = res.json()['pages']['pages']
    for page in pages:
        if page['name'] == pageTitle:
            return page['page_key']

    return None #if the page was neither created nor found