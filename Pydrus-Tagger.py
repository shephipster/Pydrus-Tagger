import HydrusApi
import sauceNaoApi
import sys
import time
import os
from Tagger import Tagger
from datetime import datetime

DELAY = 2 #Change to 5 if you are using a free SauceNao account, you may overload your 30s API call limit otherwise

"""
    Takes the given id, pulls the file with that id from Hydrus, gets tags for it using sauceNao, then adds the tags
    Logs including tags, urls, and ids saved to /tempFiles/logs.txt
    Returns if there was a successful call to SauceNao's api, false if no call was made or exceeded call limits
"""
def fillInfo(id):

    open('tempFiles/logs.txt', 'a', encoding="utf-8")

    image = HydrusApi.getImageById(id)
    #make sure we can actually look the image up.
    #accepted formats are jpg, gif, png, jpeg, bmp
    valid = False
    valid = image.endswith('.jpg') or image.endswith('.png') or image.endswith('.jpeg') or image.endswith('.gif') or image.endswith('.bmp')
    if not valid:
        #not a valid format, skip it
        print(f"============File ID {id} was of invalid format and skipped===============", file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))
        return False
    
    file_size = os.path.getsize(image)
    valid = file_size < sauceNaoApi.FILE_SIZE_LIMIT_IN_BYTES
    if not valid:
        #not a valid format, skip it
        print(f"================File ID {id} was of too large a size and skipped=====================", file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))
        return False

    
    print(f'================File ID: {id}=================', file = open('tempFiles/logs.txt', 'a'))
    try:
        allInfo = sauceNaoApi.getAllFromFile(image)
        links = allInfo['links']
        tags = allInfo['tags']
        print( f'Tags:{tags}\nUrls:{links}', file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))

        for key in links.keys():
            group = links[key]
            for entry in group:
                url = entry[0]
                HydrusApi.addKnownURLToFile(id, url)

        for tag in tags:
            HydrusApi.addTag(id, tag)

        print('=============================================', file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))
        return True
    except sauceNaoApi.OutOfSearchesException:
        print('OUT OF SEARCHES! Check at https://saucenao.com/user.php?page=search-usage ', file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))
        print('Ran into an error involcing searches. Check https://saucenao.com/user.php?page=search-usage to see if you have searches available')
        return False
    except sauceNaoApi.ImageNotAcceptedException:
        print('The image was not accepted for some reason. If a file is too large or of the wrong format it will be skipped, so')
        print('this is usually indicitive of something on SauceNao servers')
        print('Image failed to load into sauceNao, this is usually on their end', file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))
        return False


def main(start, amount):
    calls = 0
    id = start
    time_start = datetime.now()
    begin = time.perf_counter()
    print(f'Starting tagging service at {time_start.strftime("%H:%M:%S")}')
    while calls < amount:
        if fillInfo(id):
            calls += 1
            time.sleep(DELAY)   #sleep just to make sure we don't exceede saucenao limits
        id += 1
    time_stop = datetime.now()
    end = time.perf_counter()
    elapsed_time = end - begin
    elapsed_seconds = int(elapsed_time)
    elapsed_minutes = int(elapsed_seconds / 60)
    elapsed_seconds = elapsed_seconds % 60
    time_string = f'{elapsed_minutes}m:{elapsed_seconds}s'
    print(f'Stopped tagging service at {time_stop.strftime("%H:%M:%S")}')
    print(f'Elapsed time: {time_string} seconds')
    print(f'Finished making {amount} api calls. Stopped at id {id-1}.\nIf you want to continue, you should start at {id}')
    return id

""" Goes through the entirety of the Hydrus library and cleans tags
    This means that hashtags are removed and percent-encoding is undone
"""
def cleanTags(start, count):
    id = start
    iter = 0
    while(iter < count):
        if(iter % 100 == 0):
            print(iter)
        if HydrusApi.fileExists(id):
            tags = HydrusApi.getTags(id)
            for t in tags:
                cleanTag = Tagger.getCleanTag(t)
                HydrusApi.updateTag(id, t, cleanTag)
        id += 1
        iter += 1
    return

def loopMain(start, count, iters):
    oldId = start
    for i in range(0, iters):
        newId = main(oldId, count)
        if i != iters - 1:
            time.sleep(60)
        oldId = newId

if __name__ == "__main__":
    #main(int(sys.argv[1]), int(sys.argv[2]))
    #cleanTags(int(sys.argv[1]), int(sys.argv[2]))
    loopMain(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

