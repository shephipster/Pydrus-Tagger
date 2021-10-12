import HydrusApi
import sauceNaoApi
import sys
import time
import os



"""
    Takes the given id, pulls the file with that id from Hydrus, gets tags for it using sauceNao, then adds the tags
    Logs including tags, urls, and ids saved to /tempFiles/logs.txt
"""
def fillInfo(id):

    open('tempFiles/logs.txt', 'a')

    image = HydrusApi.getImageById(id)
    #make sure we can actually look the image up.
    #accepted formats are jpg, gif, png, jpeg, bmp
    valid = False
    valid = image.endswith('.jpg') or image.endswith('.png') or image.endswith('.jpeg') or image.endswith('.gif') or image.endswith('.bmp')
    if not valid:
        #not a valid format, skip it
        print(f"============File ID {id} was of invalid format and skipped===============", file = open('tempFiles/logs.txt', 'a'))
        return
    
    file_size = os.path.getsize(image)
    valid = file_size < sauceNaoApi.FILE_SIZE_LIMIT_IN_BYTES
    if not valid:
        #not a valid format, skip it
        print(f"================File ID {id} was of too large a size and skipped=====================", file = open('tempFiles/logs.txt', 'a'))
        return

    
    print(f'================File ID: {id}=================', file = open('tempFiles/logs.txt', 'a'))
    try:
        allInfo = sauceNaoApi.getAllFromFile(image)
        links = allInfo['links']
        tags = allInfo['tags']
        print( f'Tags:{tags}\nUrls:{links}')

        for key in links.keys():
            group = links[key]
            for entry in group:
                url = entry[0]
                HydrusApi.addKnownURLToFile(id, url)

        for tag in tags:
            HydrusApi.addTag(id, tag)

        print('=============================================', file = open('tempFiles/logs.txt', 'a'))
    except sauceNaoApi.OutOfSearchesException:
        print('OUT OF SEARCHES! Check at https://saucenao.com/user.php?page=search-usage ', file = open('tempFiles/logs.txt', 'a'))
        print('Ran into an error involcing searches. Check https://saucenao.com/user.php?page=search-usage to see if you have searches available')


def main(start, amount):
    stop = start + amount
    for i in range(start, stop):
        fillInfo(i)
        time.sleep(5)   #sleep just to make sure we don't exceede saucenao limits


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))