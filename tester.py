import HydrusApi
import sauceNaoApi
import TwitterService

image = HydrusApi.getImageByHash('ede1574617453eb6d399759125c3a2576ed1fc113a36fd97992485a97abf3b24')
data = sauceNaoApi.getAllTagsFromFile(image)
#NoneType is not iterable
print(data)
