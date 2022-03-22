from .User import User

class Guild:
    id: int
    ownerId: int
    users: dict
    name: str
    purgableIds: list
    bannedExplicitTags: list
    bannedGeneralTags: list
    powerUsers: list
    powerRoles: list

    def __init__(self, guild):
        self.id = guild.id
        self.ownerId = guild.owner_id
        self.users = dict()
        for user in guild.members:
            tmpUser = User(user.id)
            tmpUser.setName(user.name)
            self.users[user.id] = tmpUser.__dict__
        self.name = guild.name
        self.purgableIds = [899043866102071336, 891426527223349258]
        self.bannedExplicitTags = ['loli', 'shota', 'cub']
        self.bannedGeneralTags = []
        self.powerUsers = [guild.owner_id]
        self.powerRoles = []

    def setId(self, id: int):
        self.id = id

    def setOwnerId(self, ownerId: int):
        self.ownerId = ownerId

    def setUsers(self, users: dict):
        self.users = users

    def setName(self, name: str):
        self.name = name

    def setPurgableIds(self, ids: list):
        self.purgableIds = ids

    def setBannedExplicitTags(self, tags: list):
        self.bannedExplicitTags = tags

    def setBannedGeneralTags(self, tags: list):
        self.bannedGeneralTags = tags

    def setPowerUsers(self, powerUsers:list):
        self.powerUsers = powerUsers

    def setPowerRoles(self, powerRoles:list):
        self.powerRoles = powerRoles

    def setFromDict(self, id, dict):
        self.id = id
        self.ownerId = dict['ownerId']
        self.users = dict['users']
        self.name = dict['name']
        self.purgableIds = dict['purgableIds']
        self.bannedGeneralTags = dict['bannedGeneralTags']
        self.bannedExplicitTags = dict['bannedExplicitTags']
        self.powerUsers = dict['powerUsers']
        self.powerRoles = dict['powerRoles']