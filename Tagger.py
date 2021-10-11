import DanbooruService
import TwitterService
import GelbooruService
import E621Service
import YandereService

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

    def getTwitterTags(references):
        allTags = set()
        for r in references:
            tags = TwitterService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags

    def getE621Tags(references):
        allTags = set()
        for r in references:
            tags = E621Service.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags

    def getYandereTags(references):
        allTags = set()
        for r in references:
            tags = YandereService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags