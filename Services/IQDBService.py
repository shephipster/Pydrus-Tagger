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

def bestMatch(rt:str):
    refine = rt[rt.index('<a href='): rt.index('</table>')]
    return refine

def additionalMatches(rt:str):
    #There might not be any additional matches
    start = rt.find('Additional')
    if start == -1:
        return ""
    end = rt.find('id=\"show1\"')
    refine = rt[start:end]
    return refine

def getUrls(te:str):
    splUrl = re.findall('href=\"[htps:]*//[\w\.-]+[/\w\.\?\=\&]+\"', te)
    splLikeness = re.findall('\d{1,2}%', te)
    likenessCount = 0
    print(splLikeness)
    urls = list()
    for entry in range(len(splUrl)):
        splUrl[entry] = splUrl[entry][6:-1]
        if splUrl[entry][0:2] == '//':
            splUrl[entry] = splUrl[entry][2:]
            if int(splLikeness[likenessCount][:-1]) >= LIKENESS_LIMIT:
                likenessCount += 1
                urls.append(splUrl[entry])
    return urls

def getUrlsFromUrl(url):
    resp = getFromUrl(url)
    rt = refineText(resp)
    if rt == None:
        #It needs to be skipped
        return None
    bm = bestMatch(rt)
    am = additionalMatches(rt)
    allUrls = getUrls(bm) + getUrls(am)
    return allUrls

def getUrlsFromFile(file):
    resp = getFromFile(file)
    rt = refineText(resp)
    if rt == None:
        #It needs to be skipped
        return None
    bm = bestMatch(rt)
    am = additionalMatches(rt)
    allUrls = getUrls(bm) + getUrls(am)
    return allUrls

def getInfo(refined: str):
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
    

    urls = getUrls(refined)

    return tagList, urls

def getBestInfoFromUrl(url):
    r = getFromUrl(url)
    rt = refineText(r)
    best = bestMatch(rt)
    bestTags, bestUrls = getInfo(best)
    return bestTags, bestUrls

def getBestInfoFromFile(file):
    r = getFromFile(file)
    rt = refineText(r)
    best = bestMatch(rt)
    bestTags, bestUrls = getInfo(best)
    return bestTags, bestUrls

def getAllInfoFromUrl(url):
    r = getFromUrl(url)
    rt = refineText(r)
    if rt == None:
        #It needs to be skipped
        return None
    best = bestMatch(rt)
    additional = additionalMatches(rt)
    bestTags, bestUrls = getInfo(best)
    addTags, addUrls = getInfo(additional)
    allTags = bestTags + addTags
    allUrls = bestUrls + addUrls
    return {
        'tags': allTags,
        'urls': allUrls
    }

def getAllInfoFromFile(file):
    r = getFromFile(file)
    rt = refineText(r)
    if rt == None:
        #It needs to be skipped
        return None
    best = bestMatch(rt)
    additional = additionalMatches(rt)
    bestTags, bestUrls = getInfo(best)
    addTags, addUrls = getInfo(additional)
    allTags = bestTags + addTags
    allUrls = bestUrls + addUrls
    return {
        'tags': allTags,
        'urls': allUrls
    }
 