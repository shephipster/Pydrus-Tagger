import requests
import re
import os

URL = "https://iqdb.org"
FILE_LIMIT = 8192000 #limit is 8192KB
MAX_DIM = (7500,7500)
LIKENESS_LIMIT = 80 #result must be at least this % similar to be counted

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
    dataRegex = "title=\"Rating: \w [Score: \d* Tags:[\w\s\(\)\:]*\""
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

    return tagList

def getUrls(te:str):
    #Split te into entries
    urls = list()
    entries = re.findall('match</th>.*similarity', te)
    for entry in entries:
        parsedEntry = parseEntry(entry)
        if parsedEntry['likeness'] > LIKENESS_LIMIT:
            for url in parsedEntry['urls']:
                urls.append(url)
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

def getInfo(file):
    #urls
    r = getFromFile(file)
    rt = refineText(r)    
    if rt == None:
        #It needs to be skipped
        return None

    allUrls = getUrls(rt)
    allTags = getTags(rt)
    return {
        'tags': allTags,
        'urls': allUrls
    }