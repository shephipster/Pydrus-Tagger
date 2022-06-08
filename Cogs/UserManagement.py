import json
import os
from discord.ext import commands

from Utilities.ProcessUser import processUser

class UserManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guildsFile = os.getenv('GUILDS_FILE')

    @commands.command()
    async def setNicknameByServer(self, ctx, guid, nick):
        user, data = await processUser(ctx, guid)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)

        if guid not in data.keys():
            await ctx.channel.send(f"I don't know of any servers with the ID {guid}.\nUse `+myServers` to get a list of your servers and their ID")
            return
        else:
            user.setFromDict(uid, data[guid]['users'][uid])
            user.name = nick

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send(f"Alright, I'll call you {nick} in {data[guid]['name']} from now on")
        return
    
    @commands.command()
    async def setPingByServer(self, ctx, guid, state):
        ping = True
        if state in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'ping', '@'):
            ping = True
        elif state in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'mention'):
            ping = False
        else:
            await ctx.channel.send("Not sure what that means. Use +help setNotify for the list you can use.")
            return

        user, data = await processUser(ctx, guid)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)
        data[guid]['users'][uid]['notify'] = ping
        message = "Alright, ping for you are now set to " + str(ping)
        await ctx.channel.send(message)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)
            
    @commands.command()
    async def setDelayByServer(self, ctx, guid, delay):
        if(delay == None):
            await ctx.channel.send("And how long am I supposed to wait exactly? The command is +changeDelay <seconds>")
            return
        if(int(delay) < 0):
            await ctx.channel.send("How am I supposed to wait for negative seconds? Just say 0 if you want no delay and use +toggleNotify if you don't want to be pinged.")
            return

        user, data = await processUser(ctx, guid)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)

        try:
            data[guid]['users'][uid]['pingDelay'] = int(delay)
            await ctx.channel.send("Okay, I'll wait at least " + delay + " seconds between each ping for you.")
            with open(self.guildsFile, "w") as dataFile:
                json.dump(data, dataFile, indent=4)
        except:
            await ctx.channel.send("I couldn't set your delay, do you even have a tag list? If not, make one first with +tagMe <tag>")
            
    
    @commands.command(aliases=['info', 'myStuff'])
    async def myInfo(self, ctx, guid=None):
        """
        This returns ALL of your data for the server. This can be a lot and will always be sent as a DM
        """
        user, data = await processUser(ctx, guid)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)

        if guid != None:
            user.setFromDict(uid, data[guid]['users'][uid])

        message = str(user.__str__())
        await ctx.author.send(message)
        
    @commands.command(aliases=['servers', 'guilds', 'myGuilds'])
    async def myServers(self, ctx):

        uid = str(ctx.author.id)

        f = open(self.guildsFile)
        data = json.load(f)
        f.close()

        for guild in data:
            if uid in data[guild]['users'].keys():
                await ctx.channel.send(f"You are in {data[guild]['name']}, ID: {data[guild]['id']}")
        return
    
    @commands.command(aliases=['delay', 'setdelay'])
    async def changeDelay(self, ctx, delay):
        """Sets how long to wait between pings. Takes how many seconds to wait before each ping."""

        if(delay == None):
            await ctx.channel.send("And how long am I supposed to wait exactly? The command is +changeDelay <seconds>")
            return
        if(int(delay) < 0):
            await ctx.channel.send("How am I supposed to wait for negative seconds? Just say 0 if you want no delay and use +toggleNotify if you don't want to be pinged.")
            return

        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)
        guid = str(ctx.guild.id)

        try:
            data[guid]['users'][uid]['pingDelay'] = int(delay)
            await ctx.channel.send("Okay, I'll wait at least " + delay + " seconds between each ping for you.")
            with open(self.guildsFile, "w") as dataFile:
                json.dump(data, dataFile, indent=4)
        except:
            await ctx.channel.send("I couldn't set your delay, do you even have a tag list? If not, make one first with +tagMe <tag>")
            
    @commands.command()
    async def checkNotifications(self, ctx):
        """ Tells you if you'll be pinged for images or only get a small mention """
        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)
        guid = str(ctx.guild.id)
        userName = user.name
        try:
            if data[guid]['users'][uid]['notify']:
                await ctx.send(f"{userName}, you will get pinged for images with your tags.")
                return
            await ctx.send(f"{userName}, you will not be pinged for images with your tags.")
        except:
            await ctx.send(f"{userName}, you don't have a tag list yet. Use +tagMe <tag> to start one!")
            
    @commands.command(aliases=['nick'])
    async def nickname(self, ctx, name):

        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)
        guid = str(ctx.guild.id)

        data[guid]['users'][uid]["name"] = name
        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)
        confirm = "Alright, I'll call you " + name + " from now on."
        await ctx.channel.send(confirm)
        
    @commands.command(aliases=['ping', 'pingme'])
    async def setPing(self, ctx, state):

        ping = True
        if state in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'ping', '@'):
            ping = True
        elif state in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'mention'):
            ping = False
        else:
            await ctx.channel.send("Not sure what that means. Use +help setNotify for the list you can use.")
            return

        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)
        guid = str(ctx.guild.id)
        data[guid]['users'][uid]['notify'] = ping
        message = "Alright, ping for you are now set to " + str(ping)
        await ctx.channel.send(message)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)