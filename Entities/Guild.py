from .User import User
from .Channel import Channel
import discord

class Guild(dict):
    def __init__(self, guild):
        id = guild.id
        ownerId = guild.owner_id
        users = dict()
        for user in guild.members:
            tmpUser = User(user.id)
            tmpUser.setName(user.name)
            users[user.id] = tmpUser.__dict__
        name = guild.name
        purgableIds = [899043866102071336, 891426527223349258]
        bannedExplicitTags = ['loli', 'shota', 'cub']
        bannedGeneralTags = []
        powerUsers = [guild.owner_id]
        powerRoles = []
        channels = dict()

        for channel in guild.channels:
            if type(channel) == discord.channel.TextChannel:
                channels[channel.id] = Channel(channel)

        dict.__init__(self,
                      id=id,
                      ownerId=ownerId,
                      users=users,
                      name=name,
                      purgableIds=purgableIds,
                      bannedExplicitTags=bannedExplicitTags,
                      bannedGeneralTags=bannedGeneralTags,
                      powerUsers=powerUsers,
                      powerRoles=powerRoles,
                      channels=channels
                      )

    def setFromDict(self, dict: dict):
        self['id'] = dict['id']
        self['ownerId'] = dict['ownerId']
        self['users'] = dict['users']
        self['name'] = dict['name']

        if 'purgableIds' in dict.keys():
            self['purgableIds'] = dict['purgableIds']

        if 'bannedGeneralTags' in dict.keys():
            self['bannedGeneralTags'] = dict['bannedGeneralTags']

        if 'bannedExplicitTags' in dict.keys():
            self['bannedExplicitTags'] = dict['bannedExplicitTags']

        if 'powerUsers' in dict.keys():
            self['powerUsers'] = dict['powerUsers']

        if 'powerRoles' in dict.keys():
            self['powerRoles'] = dict['powerRoles']

        if 'channels' in dict.keys():
            for channel in dict['channels']:
                self['channels'][channel] = dict['channels'][channel]

