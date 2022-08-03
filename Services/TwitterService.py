import requests
import os
from dotenv import load_dotenv
import re

from PIL import Image, ImageOps, ImageFilter
from requests import get
from io import BytesIO
import concurrent.futures
from time import time as timer

load_dotenv()

TWITTER_URL = "https://api.twitter.com/2/tweets/{}"
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

def create_headers(bearer_token = BEARER_TOKEN):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    return headers

def create_url(id):
    url = f'https://api.twitter.com/2/tweets/{id}?tweet.fields=entities'
    return url

def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def getTags(data):
    tags = set()

    if "hashtags" in data['entities'].keys():
        res = data['entities']['hashtags']
        for tag in res:
            tags.add(tag['tag'])    
    return tags

def getTagsFromId(id):
    url = create_url(id)
    headers = create_headers(BEARER_TOKEN)
    data = connect_to_endpoint(url, headers)

    #Check in case a tweet was deleted/not authorized
    if 'errors' in data.keys():
        return set()

    tags = getTags(data['data'])
    return tags

def get_tweet_meta_from_link(url:str):
    meta = {}
    id = re.match('https?://twitter.com/[a-zA-Z0-9_]+/status/([0-9]+)', url)
    if id != None:           
        id = id.group(1)
        url = f'https://api.twitter.com/2/tweets/{id}?tweet.fields=attachments,author_id,context_annotations,created_at,entities,geo,id,in_reply_to_user_id,lang,possibly_sensitive,public_metrics,referenced_tweets,source,text,withheld&expansions=attachments.media_keys&media.fields=duration_ms,height,media_key,preview_image_url,public_metrics,type,url,width,alt_text,variants'
        headers = create_headers()
        data = connect_to_endpoint(url, headers)
        
        meta.update(id=id)
        meta.update(raw_data=data)     
        return meta
        
        
def tweetType(tweet): # Are we dealing with a Video, Image, or Text tweet?
    if 'extended_entities' in tweet:
        if 'video_info' in tweet['extended_entities']['media'][0]:
            out = "Video"
        else:
            out = "Image"
    else:
        out = "Text"

    return out 

#Taken from https://github.com/dylanpdx/BetterTwitFix/blob/891db049af0de4d40df3eaabe67d12952a036224/combineImg/__init__.py under the DWTFYW license

# find the highest res image in an array of images
def findImageWithMostPixels(imageArray):
    maxPixels = 0
    maxImage = None
    for image in imageArray:
        pixels = image.size[0] * image.size[1]
        if pixels > maxPixels:
            maxPixels = pixels
            maxImage = image
    return maxImage

def getTotalImgSize(imageArray): # take the image with the most pixels, multiply it by the number of images, and return the width and height
    maxImage = findImageWithMostPixels(imageArray)
    if (len(imageArray) == 1):
        return (maxImage.size[0], maxImage.size[1])
    elif (len(imageArray) == 2):
        return (maxImage.size[0] * 2, maxImage.size[1])
    else:
        return (maxImage.size[0] * 2, maxImage.size[1]*2)

def scaleImageIterable(args):
    image = args[0]
    targetWidth = args[1]
    targetHeight = args[2]
    pad=args[3]
    if pad:
        image = image.convert('RGBA')
        newImg = ImageOps.pad(image, (targetWidth, targetHeight),color=(0, 0, 0, 0))
    else:
        newImg = ImageOps.fit(image, (targetWidth, targetHeight)) # scale + crop
    return newImg

def scaleAllImagesToSameSize(imageArray,targetWidth,targetHeight,pad=True): # scale all images in the array to the same size, preserving aspect ratio
    newImageArray = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        newImageArray = [executor.submit(scaleImageIterable, (image, targetWidth, targetHeight,pad)) for image in imageArray]
        newImageArray = [future.result() for future in newImageArray]
    return newImageArray

def blurImage(image, radius):
    return image.filter(ImageFilter.GaussianBlur(radius=radius))

def combineImages(imageArray, totalWidth, totalHeight,pad=True):
    x = 0
    y = 0
    if (len(imageArray) == 1): # if there is only one image, just return it
        if imageArray[0].mode == 'RGB':
            return imageArray[0].convert('RGBA')
        return imageArray[0]
    # image generation is needed
    topImg = findImageWithMostPixels(imageArray)
    newImage = Image.new("RGBA", (totalWidth, totalHeight),(0, 0, 0, 0))
    imageArray = scaleAllImagesToSameSize(imageArray,topImg.size[0],topImg.size[1],pad)
    if (len(imageArray) == 2): # if there are two images, combine them horizontally
        for image in imageArray:
            newImage.paste(image, (x, y))
            x += image.size[0]
    elif (len(imageArray) == 3): # the elusive 3 image upload
        # if there are three images, combine the first two horizontally, then combine the last one vertically
        imageArray[2] = scaleAllImagesToSameSize([imageArray[2]],totalWidth,topImg.size[1],pad)[0] # take the last image, treat it like an image array and scale it to the total width, but same height as all individual images
        for image in imageArray[0:2]:
            newImage.paste(image, (x, y))
            x += image.size[0]
        y += imageArray[0].size[1]
        x = 0
        newImage.paste(imageArray[2], (x, y))
    elif (len(imageArray) == 4): # if there are four images, combine the first two horizontally, then combine the last two vertically
        for image in imageArray[0:2]:
            newImage.paste(image, (x, y))
            x += image.size[0]
        y += imageArray[0].size[1]
        x = 0
        for image in imageArray[2:4]:
            newImage.paste(image, (x, y))
            x += image.size[0]
    else:
        for image in imageArray:
            newImage.paste(image, (x, y))
            x += image.size[0]
    return newImage

def saveImage(image, name):
    image.save(name)

# combine up to four images into a single image
def genImage(imageArray):
    totalSize=getTotalImgSize(imageArray)
    combined = combineImages(imageArray, *totalSize)
    combinedBG = combineImages(imageArray, *totalSize,False)
    combinedBG = blurImage(combinedBG,50)
    finalImg = Image.alpha_composite(combinedBG, combined)
    finalImg = ImageOps.pad(finalImg, totalSize, color=(0, 0, 0, 0))
    finalImg = finalImg.convert('RGB')
    return finalImg

def downloadImage(url):
    getStuff = get(url)
    getStuff = getStuff.content
    return Image.open(BytesIO(getStuff))

def genImageFromURL(urlArray):
    # this method avoids storing the images in disk, instead they're stored in memory
    # no cache means that they'll have to be downloaded again if the image is requested again
    # TODO: cache?
    start = timer()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        imageArray = [executor.submit(downloadImage, url) for url in urlArray]
        imageArray = [future.result() for future in imageArray]
    print(f"Images downloaded in: {timer() - start}s")
    start = timer()
    finalImg = genImage(imageArray)
    print(f"Image generated in: {timer() - start}s")
    return finalImg