import Services.sauceNaoApi as sauceNaoApi

def getTagsByURL(url):
	tags = sauceNaoApi.getAllTagsFromUrl(url)
	return tags

def containsCombo(tagsList, comboTags):
	for tag in comboTags:
		if tag not in tagsList:
			return False
	return True

def containsBlacklist(tagsList, blacklist):
	for tag in tagsList:
		if tag in blacklist:
			return True
	return False