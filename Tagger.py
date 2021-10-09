import DanbooruService
import TwitterService
import GelbooruService

class Tagger:

    def getGelbooruTags(references):
        allTags = set()
        for r in references:
            tags = GelbooruService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags

    def getDanbooruTags(references):
        allTags = set()
        for r in references:
            tags = DanbooruService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags

    #Sankaku doesn't seem to have a publicly available API, so unless I can find/fake one this is dead in the water
    def getSankakuTags(references):
        # for r in references:
        #     print(r)
        return


    def getTwitterTags(references):
        allTags = set()
        for r in references:
            tags = TwitterService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags



    def getPixivTags(references):
        # for r in references:
        #     print(r)
        return