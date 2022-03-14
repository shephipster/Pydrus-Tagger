import Hydrus.HydrusApi as HydrusApi
import Services.IQDBService as IQDB
import sys

def processFile(data, hash):
        tags = data['tags']
        urls = data['urls']
        for url in urls:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url
            HydrusApi.addKnownURLToFileByHash(hash, url)
            HydrusApi.uploadURL(str(url), title="PyQDB")
        for tag in tags:
            HydrusApi.addTagByHash(hash, tag)

if __name__ == "__main__":
    fileHash = sys.argv[1]
    file = HydrusApi.getImageByHash(fileHash)
    data = IQDB.getInfo(file)
    processFile(data, fileHash)