import HydrusApi
import sauceNaoApi

image = HydrusApi.getImageById(8523)
print(image)
body = sauceNaoApi.fetchFileFromSauceNao(image)
print(body)
links = sauceNaoApi.getLinks(body)
tags = sauceNaoApi.getTagsFromLinks(links)
print(tags, links)