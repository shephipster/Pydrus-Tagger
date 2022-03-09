#Connects to a Hydrus client and tries to generate a list of files that likely do NOT need to be processed by HyTagUi
#Great for if you've already added files straight from a source or, say accidentally delete your hashFiles.txt file
#while organizing your folders like some sort of simpleton...
import Hydrus.HydrusApi as HydrusApi
import Hydrus.ProcessedFilesIO as Pio
import os

hashFile = './tempFiles/processedHashes.txt'
needWorkFile = './tempFiles/needWork.txt'

def main():
    totalFiles = len(HydrusApi.getAllFileIds())

    if not os.path.exists(hashFile):
        with open(hashFile, 'a') as file:
            file.write("")

    if not os.path.exists(hashFile):
        with open(needWorkFile, 'a') as file:
            file.write("")

    ids = HydrusApi.getAllFileIds()
    curr = 1
    for id in ids:
        print(f"Processing file: {curr} / {totalFiles}   (%{(curr / totalFiles) * 100})\r", end='')
        processFile(id)
        curr += 1

def processFile(id):
    metaData = HydrusApi.getMeta(id)
    numTagSites = 0
    tagSitesRegex = ['gelbooru', 'pixiv', 'sankakucomplex', 'e621', 'danbooru']
    if len(metaData['known_urls']) > 0:
        for url in metaData['known_urls']:
            for site in tagSitesRegex:
                if url.find(site):
                    numTagSites += 1
    if numTagSites > 0:
        print(f"{metaData['hash']}", file=open(hashFile, 'a', encoding="UTF-8"))
    else:
        print(f"{metaData['hash']}", file=open(needWorkFile, 'a', encoding="UTF-8"))
    
if __name__ == "__main__":
    main()