class Channel(dict):
    id: int
    nsfw: bool
    bannedNSFWTags: list
    bannedTags: list
    name: str

    def __init__(self, channel) -> None:
        self['id'] = channel.id
        self['nsfw'] = channel.is_nsfw()
        self['bannedNSFWTags'] = []
        self['bannedTags'] = []
        self['name'] = channel.name

    def setFromDict(self, dict:dict):
        self.id = dict['id']

        if 'nsfw' in dict.keys():
            self.nsfw = dict['nsfw']
        else:
            self.nsfw = False

        if 'nsfwBlacklist' in dict.keys():
            self.bannedNSFWTags = dict['nsfwBlacklist']

        if 'blacklist' in dict.keys():
            self.bannedTags = dict['blacklist']