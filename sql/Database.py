from typing import Union
from sql import Connection
from sql import models
from sql.models import *
import discord


def addUser(user: Union[discord.User, discord.Member]):
    id = user.id
    name = user.name
    user_table = Users()
    user_table.addRow(user_id=id, name=name)
    del user_table
    save()
    
async def addChannel(guild: discord.Guild, channel: discord.TextChannel):
    #add the guild if not present
    guild_table = Guilds()
    guild_table.addRow(guild_id = guild.id, owner_id = guild.owner_id, name = guild.name)
    del guild_table
    #add the channel if not present
    channel_table = Channels()
    channel_table.addRow(channel_id=channel.id, name=channel.name, nsfw=channel.is_nsfw(), guild_id=channel.guild.id)
    del channel_table
    
    ugm = User_Guild_Mappings()
    member: discord.Member
    async for member in guild.fetch_members():
        ugm.addRow(user_id = member.id, guild_id = guild.id)
        
    save()

async def addGuild(guild: discord.Guild):
    #add the guild
    id = guild.id
    name = guild.name
    owner:discord.Member = guild.owner
    async for user in guild.fetch_members():
        addUser(user)
    if owner:
        addUser(owner)
    #add the channels
    channels = await guild.fetch_channels()
    for channel in channels:
        if isinstance(channel, discord.TextChannel):
            await addChannel(guild, channel)
    save()

def addTagToUser(tag:str, ctx:discord.Message):
    user:discord.Member = ctx.author
    guild:discord.Guild = ctx.guild
    utm = User_Tag_Mappings()
    utm.addRow(user_id = user.id, guild_id = guild.id, tag = tag, blacklist = False)
    save() 
    
def removeTagFromUser(tag:str, ctx:discord.Message):
    user:discord.Member = ctx.author
    guild:discord.Guild = ctx.guild
    utm = User_Tag_Mappings()
    utm.deleteRow(user_id = user.id, guild_id = guild.id, tag = tag, blacklist = False)
    save() 
    
def addBlacklistToUser(tag:str, ctx:discord.Message):
    user:discord.Member = ctx.author
    guild:discord.Guild = ctx.guild
    utm = User_Tag_Mappings()
    utm.addRow(user_id = user.id, guild_id = guild.id, tag = tag, blacklist = True)
    save() 
    
def removeBlacklistFromUser(tag:str, ctx:discord.Message):
    user:discord.Member = ctx.author
    guild:discord.Guild = ctx.guild
    utm = User_Tag_Mappings()
    utm.deleteRow(user_id = user.id, guild_id = guild.id, tag = tag, blacklist = True)
    save()  
    
def getBlacklist(user_id, guild_id):
    utm = User_Tag_Mappings()
    results = utm.search(user_id = user_id, guild_id = guild_id, blacklist = True)
    return results

def getTags(user_id, guild_id):
    utm = User_Tag_Mappings()
    results = utm.search(user_id = user_id, guild_id = guild_id, blacklist = False)
    return results

def save():
    Connection.connection.commit()
    
def init():
    entity = models.Users()
    entity.createTable()

    entity = models.Guilds()
    entity.createTable()

    entity = models.Channels()
    entity.createTable()

    entity = models.User_Guild_Mappings()
    entity.createTable()

    entity = models.User_Tag_Mappings()
    entity.createTable()
    
    entity = models.User_Channel_Mappings()
    entity.createTable()