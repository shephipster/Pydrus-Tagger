import json
import os
from discord.ext import commands
import discord
from Entities.User import User
from Entities.Guild import Guild

from Utilities.ProcessUser import processUser

class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guildsFile = os.getenv('GUILDS_FILE')

    @commands.command(aliases=['deleteMessage', 'deletepost', 'removepost', 'delete'])
    async def removeMessage(self, ctx, id):
        message = await ctx.channel.fetch_message(id)

        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        guid = str(ctx.guild.id)

        if str(message.author.id) in data[guid]['purgableIds']:
            await message.delete()
        else:
            await ctx.channel.send(f"I'm not allowed to delete stuff {message.author.name} posts")
        return
    
    def userCanUsePowerCommand(self, guild: Guild, member: discord.Member):
        userId = int(member.id)
        if userId in guild['powerUsers']:
            return True
        for role in member.roles:
            if role in guild['powerRoles']:
                return True
        return False
    
    async def invokePowerCommand(self, ctx: commands.context, command, *params):
        user: User
        guild: Guild
        user, guilds = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        guild = guilds[f'{ctx.guild.id}']

        if user == None or guild == None:
            #there was some sort of issue
            return
        if not self.userCanUsePowerCommand(guild, ctx.author):
            await ctx.channel.send(f"You don't have permission to use this command!")
            return

        await command(ctx, guilds, f'{ctx.guild.id}', *params)
        
    @commands.command(aliases=['empower', 'promote'])
    async def addPowerUser(self, ctx: commands.context, userId):
        await self.invokePowerCommand(ctx, self.addPowerUserCommand, int(userId))


    async def addPowerUserCommand(self, ctx, guilds, guid, userToAdd):
        if userToAdd not in guilds[guid]['powerUsers']:
            guilds[guid]['powerUsers'].append(userToAdd)
            with open(self.guildsFile, 'w') as dataFile:
                json.dump(guilds, dataFile, indent=4)


    @commands.command(aliases=['demote', 'fell'])
    async def removePowerUser(self, ctx: commands.context, userId):
        await self.invokePowerCommand(ctx, self.removePowerUserCommand, int(userId))


    async def removePowerUserCommand(self, ctx, guilds, guid, userToAdd):
        if userToAdd in guilds[guid]['powerUsers']:
            guilds[guid]['powerUsers'].remove(userToAdd)
            with open(self.guildsFile, 'w') as dataFile:
                json.dump(guilds, dataFile, indent=4)


    @commands.command(aliases=['empowerRole', 'promoteRole'])
    async def addPowerRole(self, ctx: commands.context, role):
        await self.invokePowerCommand(ctx, self.addPowerRoleCommand, role)


    async def addPowerRoleCommand(self, ctx, guilds, guid, role):
        if role not in guilds[guid]['powerRoles']:
            guilds[guid]['powerRoles'].append(role)
            with open(self.guildsFile, 'w') as dataFile:
                json.dump(guilds, dataFile, indent=4)


    @commands.command(aliases=['demoteRole', 'fellRole'])
    async def removePowerRole(self, ctx: commands.context, role):
        await self.invokePowerCommand(ctx, self.removePowerUserCommand, role)


    async def removePowerRoleCommand(self, ctx, guilds, guid, role):
        if role in guilds[guid]['powerRoles']:
            guilds[guid]['powerRoles'].remove(role)
            with open(self.guildsFile, 'w') as dataFile:
                json.dump(guilds, dataFile, indent=4)


    @commands.command(aliases=['unblockPornTag', 'unbanPornTag', 'permitPornTag'])
    async def removeBannedExplicitTags(self, ctx: commands.context, *tags):
        await self.invokePowerCommand(ctx, self.removeBannedExplicitTagsCommand, *tags)


    async def removeBannedExplicitTagsCommand(self, ctx, guilds, guid, *tags):
        for tag in tags:
            if tag in guilds[guid]['bannedExplicitTags']:
                guilds[guid]['bannedExplicitTags'].remove(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, I can now roll explicit stuff with any of the following: {tags}")


    @commands.command(aliases=['banExplicitTag', 'blockExplicitTag', 'blockPornTag', 'banPornTag'])
    async def addBannedExplicitTags(self, ctx: commands.context, *tags):
        await self.invokePowerCommand(ctx, self.addBannedExplicitTagsCommand, *tags)


    async def addBannedExplicitTagsCommand(self, ctx, guilds, guid, *tags):
        for tag in tags:
            if tag not in guilds[guid]['bannedExplicitTags']:
                guilds[guid]['bannedExplicitTags'].append(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, I'll now no longer roll explicit stuff with any of the following: {tags}")


    @commands.command(aliases=['canDelete', 'canRemove', 'canPurge'])
    async def addPurgablePoster(self, ctx: commands.context, id):
        await self.invokePowerCommand(ctx, self.addPurgablePosterCommand, id)


    async def addPurgablePosterCommand(self, ctx, guilds, guid, id):
        if id in guilds[guid]['purgableIds']:
            await ctx.channel.send("I'm already allowed to delete their posts.")
        else:
            guilds[guid]['purgableIds'].append(id)
            member = await ctx.guild.fetch_member(id)
            with open(self.guildsFile, "w") as dataFile:
                json.dump(guilds, dataFile, indent=4)
            await ctx.channel.send(f"Okay, I can now delete {member.name}'s posts.")


    @commands.command(aliases=['cantDelete', 'cantRemove', 'cantPurge'])
    async def removePurgablePoster(self, ctx: commands.context, id):
        await self.invokePowerCommand(ctx, self.removePurgablePosterCommand, id)


    async def removePurgablePosterCommand(self, ctx, guilds, guid, id):
        if id not in guilds[guid]['purgableIds']:
            await ctx.channel.send("I'm already not allowed to delete their posts.")
        else:
            guilds[guid]['purgableIds'].remove(id)
            member = await ctx.guild.fetch_member(id)
            with open(self.guildsFile, "w") as dataFile:
                json.dump(guilds, dataFile, indent=4)
            await ctx.channel.send(f"Okay, I can no longer delete {member.name}'s posts.")


    @commands.command(aliases=['banTag', 'blockTag'])
    async def addBannedGeneralTags(self, ctx: commands.context, *tags):
        await self.invokePowerCommand(ctx, self.addBannedGeneralTagsCommand, *tags)


    async def addBannedGeneralTagsCommand(self, ctx, guilds, guid, *tags):
        for tag in tags:
            if tag not in guilds[guid]['bannedGeneralTags']:
                guilds[guid]['bannedGeneralTags'].append(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, I'll now no longer roll stuff with any of the following: {tags}")


    @commands.command(aliases=['unblockTag', 'unbanTag'])
    async def removeBannedGeneralTags(self, ctx: commands.context, *tags):
        await self.invokePowerCommand(ctx, self.removeBannedGeneralTagsCommand, *tags)


    async def removeBannedGeneralTagsCommand(self, ctx, guilds, guid, *tags):
        for tag in tags:
            if tag in guilds[guid]['bannedGeneralTags']:
                guilds[guid]['bannedGeneralTags'].remove(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, I can now roll stuff with any of the following: {tags}")
        
    @commands.command(aliases=['update'])
    async def updateGuild(self, ctx):
        f = open(self.guildsFile)
        data = json.load(f)
        f.close()

        data = ctx.guild
        await self.updateGuildCommand(data)


    async def updateAllGuilds(self):
        for guild in self.bot.guilds:
            await self.updateGuildCommand(guild)


    async def updateGuildCommand(self, guild):
        f = open(self.guildsFile)
        data = json.load(f)
        f.close()

        guid = f'{guild.id}'
        tempGuild = Guild(guild)
        if guid in data.keys():
            tempGuild.setFromDict(data[guid])
        data[guid] = tempGuild

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)
            
            
    @commands.command(aliases=['banChannelTag'])
    async def banTagFromChannel(self, ctx, *tags):
        await self.invokePowerCommand(ctx, self.banTagsFromChannelCommand, *tags)


    async def banTagsFromChannelCommand(self, ctx, guilds, guid, *tags):
        channel = ctx.channel
        cid = str(channel.id)
        for tag in tags:
            if tag not in guilds[guid]['channels'][cid]['bannedTags']:
                guilds[guid]['channels'][cid]['bannedTags'].append(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, won't roll stuff in <#{channel.id}> that has {tags}")


    @commands.command(aliases=['unbanChannelTag', 'allowChannelTag'])
    async def unbanTagFromChannel(self, ctx, *tags):
        await self.invokePowerCommand(ctx, self.unbanTagsFromChannelCommand, *tags)


    async def unbanTagsFromChannelCommand(self, ctx, guilds, guid, *tags):
        channel = ctx.channel
        cid = str(channel.id)
        for tag in tags:
            if tag in guilds[guid]['channels'][cid]['bannedTags']:
                guilds[guid]['channels'][cid]['bannedTags'].remove(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, I can roll stuff in <#{channel.id}> that has {tags} now")


    @commands.command(aliases=['banChannelPornTag'])
    async def banNSFWTagFromChannel(self, ctx, *tags):
        await self.invokePowerCommand(ctx, self.banNSFWTagsFromChannelCommand, *tags)


    async def banNSFWTagsFromChannelCommand(self, ctx, guilds, guid, *tags):
        channel = ctx.channel
        cid = str(channel.id)
        for tag in tags:
            if tag not in guilds[guid]['channels'][cid]['bannedNSFWTags']:
                guilds[guid]['channels'][cid]['bannedNSFWTags'].append(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, won't roll stuff in <#{channel.id}> that's porn and has {tags}")


    @commands.command(aliases=['unbanChannelNSFWTag', 'allowChannelNSFWTag', 'unbanChannelPornTag', 'allowChannelPornTag'])
    async def unbanNSFWTagFromChannel(self, ctx, *tags):
        await self.invokePowerCommand(ctx, self.unbanNSFWTagsFromChannelCommand, *tags)


    async def unbanNSFWTagsFromChannelCommand(self, ctx, guilds, guid, *tags):
        channel = ctx.channel
        cid = str(channel.id)
        for tag in tags:
            if tag in guilds[guid]['channels'][cid]['bannedNSFWTags']:
                guilds[guid]['channels'][cid]['bannedNSFWTags'].remove(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(guilds, dataFile, indent=4)

        await ctx.channel.send(f"Okay, I can roll stuff in <#{channel.id}> that's porn and has {tags} now")

    @commands.command(aliases=['init', 'initServer'])
    async def initGuild(self, ctx):
        #for each file, if guild not already part of it add them
        if type(ctx.channel) == discord.channel.DMChannel:
            await ctx.channel.send("You can't use this command in a DM, how am I going to know what server you want?")
            return

        guildUID = str(ctx.guild.id)

        f = open(self.guildsFile)
        data = json.load(f)
        f.close()

        guild = Guild(ctx.guild)

        if guildUID not in data.keys():
            #guild not initialized yet, add it
            data[f'{guildUID}'] = guild.__dict__
            with open(self.guildsFile, 'w') as f:
                json.dump(data, f, indent=4)
            await ctx.channel.send("Added your guild to the list")
        else:
            await ctx.channel.send("Your guild has already been initialized")
        return
    
    @commands.command(aliases=['pm', 'dm'])
    async def slide(ctx):
        await ctx.author.send("You wanted something?")