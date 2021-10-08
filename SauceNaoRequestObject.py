class SauceNaoRequestObject:
    def __init__(self, key):
        self.output_type = 2
        self.api_key = key
        self.testmode = True
        self.dbmask = 0
        self.dbmaski = 0
        self.db = 999
        self.numres = 16
        self.dedupe = 2
        self.url = ""

    def setUrl(self, url):
        self.url = url
    
    def getKey(self):
        return self.api_key

    def getOutputType(self):
        return self.output_type
    
    def getTestmode(self):
        return self.testmode

    def getDbmask(self):
        return self.dbmask

    def getDbmaski(self):
        return self.dbmask

    def getDb(self):
        return self.db

    def getNumres(self):
        return self.numres

    def getDedupe(self):
        return self.dedupe

    def getUrl(self):
        return self.url