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

    def setName(self, name):
        self.name = name

    def setFromDict(self, id, dict:dict):
        if 'id' in dict.keys():
            self.id = dict['id']
        else:
            self.id = id

        if 'tags' in dict.keys():
            self.tags = dict['tags']
        else:
            self.tags = []

        if 'blacklist' in dict.keys():
            self.blacklist = dict['blacklist']
        else:
            self.blacklist = []

        if 'notify' in dict.keys():
            self.notify = dict['notify']
        else:
            self.notify = True

        if 'name' in dict.keys():
            self.name = dict['name']
        else:
            self.name = ""

        if 'lastPing' in dict.keys():
            self.lastPing = dict['lastPing']
        else:
            self.lastPing = 0

        if 'specifyTags' in dict.keys():
            self.specifyTags = dict['specifyTags']
        else:
            self.specifyTags = True

        if 'tagCombos' in dict.keys():
            self.tagCombos = dict['tagCombos']
        else:
            self.tagCombos = []