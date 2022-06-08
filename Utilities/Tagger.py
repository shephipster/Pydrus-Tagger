from Services import DanbooruService, TwitterService, GelbooruService, E621Service, YandereService


class Tagger:

    #Tags in a list of tags and cleans items up
    #For example, %27 changed back to ' and remove # from twitter
    def getCleanTag(tag):
        cleanTag = str(tag)
        #HTML
        cleanTag = cleanTag.replace("#", '')
        cleanTag = cleanTag.replace("%21", '!')
        cleanTag = cleanTag.replace('%23', '#')
        cleanTag = cleanTag.replace('%24', '$')
        cleanTag = cleanTag.replace('%25', '%')
        cleanTag = cleanTag.replace('%26', '&')
        cleanTag = cleanTag.replace('%27', '\'')
        cleanTag = cleanTag.replace('%28', '(')
        cleanTag = cleanTag.replace('%29', ')')
        cleanTag = cleanTag.replace('%2A', '*')
        cleanTag = cleanTag.replace('%2B', '+')
        cleanTag = cleanTag.replace('%2C', ',')
        cleanTag = cleanTag.replace('%2F', '/')
        cleanTag = cleanTag.replace('%3A', ':')
        cleanTag = cleanTag.replace('%3B', ';')
        cleanTag = cleanTag.replace('%3D', '=')
        cleanTag = cleanTag.replace('%3F', '?')
        cleanTag = cleanTag.replace('%40', '@')
        cleanTag = cleanTag.replace('%5B', '[')
        cleanTag = cleanTag.replace('%5D', ']')
        #PHP
        cleanTag = cleanTag.replace('&039;', '\'')
        cleanTag = cleanTag.replace('&amp;', '&')
        cleanTag = cleanTag.replace('&quot;', '\"')
        cleanTag = cleanTag.replace('&lt;', '<')
        cleanTag = cleanTag.replace('&gt;', '>')
        cleanTag = cleanTag.lower()
        return cleanTag

    def getGelbooruTags(references):
        allTags = set()
        for r in references:
            tags = GelbooruService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(Tagger.getCleanTag(t))
        return allTags

    def getDanbooruTags(references):
        allTags = set()
        for r in references:
            tags = DanbooruService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(Tagger.getCleanTag(t))
        return allTags

    def getTwitterTags(references):
        allTags = set()
        for r in references:
            tags = TwitterService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(Tagger.getCleanTag(t))
        return allTags

    def getE621Tags(references):
        allTags = set()
        for r in references:
            tags = E621Service.getTagsFromId(r[1])
            for t in tags:
                allTags.add(Tagger.getCleanTag(t))
        return allTags

    def getYandereTags(references):
        allTags = set()
        for r in references:
            tags = YandereService.getTagsFromId(r[1])
            for t in tags:
                allTags.add(Tagger.getCleanTag(t))
        return allTags
