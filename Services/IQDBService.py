import requests
import re
import os
import hashlib
import requests
import io
from . import DanbooruService, GelbooruService, E621Service


URL = "https://iqdb.org"
FILE_LIMIT = 8192000 #limit is 8192KB
MAX_DIM = (7500,7500)
LIKENESS_LIMIT = 80 #result must be at least this % similar to be counted

def getFromDiscordFile(fp):
    body = {
        'file': fp
    }
    r = requests.post(URL, files=body)
    return r

def getFromFile(file):  
    body = { 
        'file': (os.path.basename(file), open(file, 'rb'))
    }
    r = requests.post(URL, files=body)
    return r

def getFromUrl(url):
    #takes a url and returns the html result from IQDB
    payload = {
        'url': url
    }
    r = requests.get(URL, params=payload)
    return r

def refineText(r: requests.Response):
    text = r.text
    start = text.find('<th>Best match</th>')

    if start == -1:
        #there was no best match, return nothing
        return None

    end = text.find('Not the right one?')
    refinedText = text[start:end]
    return refinedText

def getTags(refined: str):
    dataRegex = "title=\"Rating: \w Score: \d Tags:[\sa-zA-Z0-9_\-\(\)]+\""
    ratingRegex = "Rating: \w"
    tagsRegex = "Tags: [\w\d _\(\)\:]*"

    data = re.findall(dataRegex, refined)
    if len(data) == 0:
        #empty data, most likely dealing with additional matches when there were none
        return [], []

    tags = re.findall(tagsRegex, data[0])
    tagList = tags[0][6:].split(' ')
  
    ratingLetter = re.findall(ratingRegex, data[0])
    ratingChar = ratingLetter[0][-1:]

    if ratingChar == 'e':
        tagList.append('rating: explicit')
    elif ratingChar == 's':
        tagList.append('rating: safe')
    else:
        tagList.append('rating: questionable')

    tagSet = set()
    for tag in tagList:
        tagSet.add(tag)
        
    return tagSet

def getUrls(te:str):
    #Split te into entries
    urls = set()
    entries = re.findall('match</th>.*similarity', te)
    for entry in entries:
        parsedEntry = parseEntry(entry)
        if parsedEntry['likeness'] > LIKENESS_LIMIT:
            for url in parsedEntry['urls']:
                urls.add(url)
    return urls

def parseEntry(entry:str):
    urls = re.findall('href=\"[htps:]*//[\w\.-]+[/\w\.\?\=\&]+\"', entry)
    for i in range(len(urls)):
        urls[i] = urls[i][6:-1]
        if urls[i][0:2] == "//":
            urls[i] = urls[i][2:]
    likenessStr = re.findall('\d{1,2}%', entry)[0]
    likeness = int(likenessStr[:-1])
    entry = {
        'urls': urls,
        'likeness': likeness
    }
    return entry

def getInfoDiscordFile(fp:io.BufferedIOBase):
    #urls
    r = getFromDiscordFile(fp)
    rt = refineText(r)    
    if rt == None:
        redirection = getSauceNaoLink(r)
        return {
            'error': True,
            'sauceNao_redirect': redirection
        }

    urls = getUrls(rt)
    tags = getTags(rt)
    
    #now that we have urls, pull tags from those sites
    url:str
    for url in urls:
        if url.find('danbooru') != -1:
            #get the id from the url and then pass it to DanbooruService
            id = re.findall('\d+', url)[0]
            danTags = DanbooruService.getTagsFromId(id)
            for tag in danTags:
                tags.add(tag)
        elif url.find('gelbooru') != -1:
            md5 = re.findall('md5=[\d|\w]+', url)[0]
            md5 = md5[4:]
            gelTags = GelbooruService.getTagsFromMD5(md5)
            for tag in gelTags:
                tags.add(tag)
        elif url.find('e621') != -1:
            print(url)
            
    
    return {
        'tags': tags,
        'urls': urls
    }

def getInfoFile(file):
    #urls
    r = getFromFile(file)
    rt = refineText(r)    
    if rt == None:
        return rt

    urls = getUrls(rt)
    tags = getTags(rt)
    
    #now that we have urls, pull tags from those sites
    url:str
    for url in urls:
        if url.find('danbooru') != -1:
            #get the id from the url and then pass it to DanbooruService
            id = re.findall('\d+', url)[0]
            danTags = DanbooruService.getTagsFromId(id)
            for tag in danTags:
                tags.add(tag)
        elif url.find('gelbooru') != -1:
            md5 = re.findall('md5=[\d|\w]+', url)[0]
            md5 = md5[4:]
            gelTags = GelbooruService.getTagsFromMD5(md5)
            for tag in gelTags:
                tags.add(tag)
        elif url.find('e621') != -1:
            print(url)
            
    
    return {
        'tags': tags,
        'urls': urls
    }

def getInfoUrl(url):
    r = getFromUrl(url)
    rt = refineText(r)
    if rt == None:
        r = requests.get(f'{url}', stream=True)
        file = r.raw.read()      
        md5 = hashlib.md5(file)
        return GelbooruService.checkMD5(md5)

    urls = getUrls(rt)
    tags = getTags(rt)
    
    #now that we have urls, pull tags from those sites
    url:str
    for url in urls:
        if url.find('danbooru') != -1:
            #get the id from the url and then pass it to DanbooruService
            id = re.findall('\d+', url)[0]
            danTags = DanbooruService.getTagsFromId(id)
            for tag in danTags:
                tags.add(tag)
        elif url.find('gelbooru') != -1:
            md5 = re.findall('md5=[\d|\w]+', url)[0]
            md5 = md5[4:]
            gelTags = GelbooruService.getTagsFromMD5(md5)
            for tag in gelTags:
                tags.add(tag)
        elif url.find('e621') != -1:
            print(url)
            
    
    return {
        'tags': tags,
        'urls': urls
    }
    
def getSauceNaoLink(res:requests.Response):
    text = res.text
    regex = "saucenao.com/search.php\?db=999&dbmaski=32768&url=(https://iqdb.org/thu/[\w\d]+.\w{3})"
    url = re.findall(regex, text)[0]
    url = "https://saucenao.com/search.php?db=999&dbmaski=32768&url=" + url
    return url

if __name__ == "__main__":
    data = getInfoUrl('https://cdn.discordapp.com/attachments/896265813630255138/965379505675980871/unknown.png')
    tags = data['tags']
    urls = data['urls']
    print(f'Tags: {tags}')