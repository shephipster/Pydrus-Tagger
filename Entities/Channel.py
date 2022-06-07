class Channel(dict):
    id: int
    nsfw: bool
    bannedNSFWTags: list
    bannedTags: list
    name: str
    safe_exemptions: list((str,str))
    nsfw_exemptions: list((str,str))

    def __init__(self, channel=None, id=None, is_nsfw=None, name=None) -> None:
        if  channel != None:
            self['id'] = channel.id
            self['nsfw'] = channel.is_nsfw()
            self['bannedNSFWTags'] = []
            self['bannedTags'] = []
            self['name'] = channel.name
            self['exemptions'] = []
        elif not (id == None or is_nsfw == None or name == None):
            self['id'] = id
            self['nsfw'] = is_nsfw
            self['bannedNSFWTags'] = []
            self['bannedTags'] = []
            self['name'] = name
            self['exemptions'] = []

    def setFromDict(self, dict:dict):
        self['id'] = dict['id']

        if 'nsfw' in dict.keys():
            self['nsfw'] = dict['nsfw']
        else:
            self['nsfw'] = False

        if 'bannedNSFWTags' in dict.keys():
            self['bannedNSFWTags'] = dict['bannedNSFWTags']
        else:
            self['bannedNSFWTags'] = []

        if 'bannedTags' in dict.keys():
            self['bannedTags'] = dict['bannedTags']
        else:
            self['bannedTags'] = []
            
        if 'safe_exemptions' in dict.keys():
            self['safe_exemptions'] = dict['safe_exemptions']
        else:
            self['safe_exemptions'] = []
        
        if 'nsfw_exemptions' in dict.keys():
            self['nsfw_exemptions'] = dict['nsfw_exemptions']
        else:
            self['nsfw_exemptions'] = []
            