import HydrusApi
import sauceNaoApi
import sys


fileLoc = HydrusApi.getImageById(sys.argv[1])
tags = sauceNaoApi.getAllTagsFromFile(fileLoc)
print(tags)