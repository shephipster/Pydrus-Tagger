import os
import requests
import sauceNaoApi

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