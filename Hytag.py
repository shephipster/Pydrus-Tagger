from Hydrus.ProcessedFilesIO import ProcessedFilesIO
import sys
import Hydrus.HydrusApi as HydrusApi
import Services.sauceNaoApi as sauceNaoApi
import time

logFile = "/tempFiles/logs.txt"
fio = ProcessedFilesIO("./tempFiles/processedHashes.txt")

def isValidFile(fileMeta):
    if fileMeta['size'] > sauceNaoApi.FILE_SIZE_LIMIT_IN_BYTES:
        return False

    if fileMeta['mime'] not in ["image/png", "image/jpg", "image/jpeg", "image/bmp", "image/gif", "image/webp"]:
        return False

    return True

def processFile(data, id, hash):
    #print(f'processing {id}')
    tags = data['tags']
    urls = data['links']
    #print(f'================File ID: {id}=================', file = open('tempFiles/logs.txt', 'a',encoding='utf-8'))
    #print(f'Hash: {hash}', file = open('tempFiles/logs.txt', 'a',encoding='utf-8'))

    #print(f'Tags: {tags}', file = open('tempFiles/logs.txt', 'a',encoding='utf-8'))
    for key in urls.keys():
            group = urls[key]
            for entry in group:
                url = entry[0]
                HydrusApi.addKnownURLToFile(id, url)
                HydrusApi.uploadURL(url)    #This one might can replace the addKnown, but for now just do this

    #print(f'Urls: {urls}', file = open('tempFiles/logs.txt', 'a', encoding='utf-8'))
    for tag in tags:
            HydrusApi.addTag(id, tag)

    #print('=============================================', file = open('tempFiles/logs.txt', 'a', encoding="utf-8"))
    #print(f'{id} processed')

def reverseProcesses(calls):
    """Does the same thing as normal, except it starts from the last file in the system and goes to the first.
        Good if you've run this for a fair bit and/or are past the halfway point"""
    currCount = 0
    PAGE_SIZE = 250
    processedNewFile = False
    #Starter page of any size, just to get which ids exist in the system
    lastID = HydrusApi.getLastId()
    page = HydrusApi.getReversePage(lastID, PAGE_SIZE)
    print("Finding first new file...", end='\r')
    while(currCount < calls):

        if(len(page) == 0):
            #ran through the entire database, finish
            print("All files have been processed!")
            fio.save()
            break

        for id in page:
            fileMeta = HydrusApi.getMeta(id)
            fileHash = fileMeta['hash']

            if fio.hashInFile(fileHash):
                #print(f'{fileHash} known, skipping')
                continue

            elif not isValidFile(fileMeta):
                #not a valid file, add to list and skip
                #print(f'{fileHash} not valid, skipping')
                fio.addHash(fileHash)
                continue

            if(not processedNewFile):
                processedNewFile = True
                print("Reached new files, starting processing")


            try:
                #print(f'{fileHash} ({id}) in progress')
                image = HydrusApi.getImageById(id)
                data = sauceNaoApi.getAllFromFile(image)
                processFile(data, id, fileHash)
                currCount += 1
                
            except Exception as e:
                print(f"Minor hickup with file {fileHash}\n", e)
            finally:
                print(f"====        {currCount}/{calls}        ====", end='\r')
                fio.addHash(fileHash)

            if currCount >= calls:
                fio.save()
                break

            elif (currCount % 100 == 0 and not currCount == 0):
                print("Letting Hydrus catch up...", end='\r')
                fio.save()
                time.sleep(90)                
            elif(currCount % 10 == 0 and not currCount == 0):
                #give the Hydrus client some time to handle the uploaded urls
                fio.save()
                time.sleep(15)
                
        
        #ran out of pages, get next one
        page = HydrusApi.getReversePage( HydrusApi.getReverseNextPageStart(page), PAGE_SIZE)
        #print(f'New Page')


def process(calls):
    currCount = 0
    PAGE_SIZE = 250
    processedNewFile = False
    #Starter page of any size, just to get which ids exist in the system
    page = HydrusApi.getPage(0, PAGE_SIZE)
    print("Finding first new file...", end='\r')
    while(currCount < calls):

        if(len(page) == 0) :
            #ran through the entire database, finish
            print("All files have been processed!")
            fio.save()
            break

        for id in page:
            fileMeta = HydrusApi.getMeta(id)
            fileHash = fileMeta['hash']

            if fio.hashInFile(fileHash):
                #print(f'{fileHash} known, skipping')
                continue

            elif not isValidFile(fileMeta):
                #not a valid file, add to list and skip
                #print(f'{fileHash} not valid, skipping')
                fio.addHash(fileHash)
                continue

            if(not processedNewFile):
                processedNewFile = True
                print("Reached new files, starting processing")


            try:
                #print(f'{fileHash} ({id}) in progress')
                image = HydrusApi.getImageById(id)
                data = sauceNaoApi.getAllFromFile(image)
                processFile(data, id, fileHash)
                currCount += 1
                
            except Exception as e:
                print(f"Minor hickup with file {fileHash}\n", e)
            finally:
                print(f"====        {currCount}/{calls}        ====", end='\r')
                fio.addHash(fileHash)

            if currCount >= calls:
                fio.save()
                break

            elif (currCount % 100 == 0 and not currCount == 0):
                print("Letting Hydrus catch up...", end='\r')
                fio.save()
                time.sleep(90)                
            elif(currCount % 10 == 0 and not currCount == 0):
                #give the Hydrus client some time to handle the uploaded urls
                fio.save()
                time.sleep(15)
                
        
        #ran out of pages, get next one
        page = HydrusApi.getPage( HydrusApi.getNextPageStart(page), PAGE_SIZE)
        #print(f'New Page')

if __name__ == "__main__":

    if len(sys.argv) == 1:
        apiCalls = 25
    elif len(sys.argv) == 2:
        apiCalls = int(sys.argv[1])
        reverse = False
    else:
        apiCalls = int(sys.argv[1])
        reverse = True
    try:
        if reverse:
            reverseProcesses(apiCalls)
        else:
            process(apiCalls)
        print("====================================COMPLETE====================================")
    except Exception as e:
        print(e)
        fio.save()