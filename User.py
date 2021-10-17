class User:
    id: int
    tags: list
    blacklist: list
    tagCombos: list
    notify: bool
    name: str
    lastPing: float
    pingDelay: int
    specifyTags: bool

    def __init__(self, id):
        self.id = id
        self.tags = []
        self.blacklist = []
        self.notify = True
        self.name = ""
        self.lastPing = 0
        self.pingDelay = 60
        self.specifyTags = True
        self.tagCombos = []

    def setId(self, id: int):
        self.id = id
    
    def setTags(self, tags: list):
        self.tags = tags

    def setBlacklist(self, blacklist: list):
        self.blacklist = blacklist

    def setNotify(self, notify:bool):
        self.notify = notify

    def setName(self, name:str):
        self.name = name

    def setLastPint(self, lastPing: float):
        self.lastPing = lastPing

    def setPingDelay(self, pingDelay:int):
        self.pingDelay = pingDelay

    def setSpecifyTags(self, specifyTags: bool):
        self.specifyTags = specifyTags

    def setFromDict(self, id, dict):
        self.id = id
        self.tags = dict['tags']
        self.blacklist = dict['blacklist']
        self.notify = dict['notify']
        self.name = dict['name']
        self.lastPing = dict['lastPing']
        self.specifyTags = dict['specifyTags']
        self.tagCombos = dict['combos']