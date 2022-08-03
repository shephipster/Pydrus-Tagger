import json
from requests import get


def getFromUrl(url:str):
    content = get(url, {'is_embed':True})
    meta_data = get(url, {'meta': True})
    meta_data = json.loads(meta_data.text)
    return content, meta_data