import DanbooruApi

class Tagger:

    def getGelbooruTags(references):
        # for r in references:
        #     print(r)
        return

    def getDanbooruTags(references):
        allTags = set()
        for r in references:
            tags = DanbooruApi.getTagsFromId(r[1])
            for t in tags:
                allTags.add(t)
        return allTags

    def getTwitterTags(references):
        # for r in references:
        #     print(r)
        return

    def getSankakuTags(references):
        # for r in references:
        #     print(r)
        return

    def getPixivTags(references):
        # for r in references:
        #     print(r)
        return