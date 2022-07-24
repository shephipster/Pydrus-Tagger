import json
import os
from discord.ext import commands

from Utilities.ProcessUser import processUser
from sql import Database


class TagManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guildsFile = os.getenv('GUILDS_FILE')

    @commands.command(aliases=['addtag'])
    async def tagMe(self, ctx, *tags):
        if not ctx.guild:
            await ctx.channel.send("Sorry, I can't do this in DMs")

        # Migrate to the SQLite database
        for tag in tags:
            Database.addTagToUser(tag, ctx)

        await ctx.channel.send(f"Alright, I added `{', '.join(tags)}` to your tags.")

    @commands.command(aliases=['untag', 'removeTag'])
    async def untagMe(self, ctx, *tags):
        if not ctx.guild:
            await ctx.channel.send("Sorry, I can't do this in DMs")

        # Migrate to the SQLite database
        for tag in tags:
            Database.removeTagFromUser(tag, ctx)

        await ctx.channel.send(f"Okay, I took `{', '.join(tags)}` out of your tags list.")

    @commands.command(aliases=[])
    async def blacklist(self, ctx, *tags):
        if not ctx.guild:
            await ctx.channel.send("Sorry, I can't do this in DMs")

        # Migrate to the SQLite database
        for tag in tags:
            Database.addBlacklistToUser(tag, ctx)

        await ctx.channel.send(f"Alright, I added `{', '.join(tags)}` to your blacklist.")

    @commands.command(aliases=[])
    async def unblacklist(self, ctx, *tags):
        if not ctx.guild:
            await ctx.channel.send("Sorry, I can't do this in DMs")
            
        # Migrate to the SQLite database
        for tag in tags:
            Database.removeBlacklistFromUser(tag, ctx)

        await ctx.channel.send(f"Alright, I removed `{', '.join(tags)}` frpm your blacklist.")


    @commands.command(aliases=[])
    async def myBlacklist(self, ctx):
        tags = Database.getBlacklist(user_id = ctx.author.id, guild_id = ctx.guild.id)
        tag_set = []
        if not tags:
            await ctx.channel.send("You don't have any blacklisted tags yet.")
            return
        for tag in tags:
            tag_set.append(tag[3])
        message = "Your blacklisted tags are: `"
        message += ', '.join(tag_set) + '`'
        await ctx.channel.send(message)
        
        
    @commands.command(aliases=['mytags', 'taglist'])
    async def checkTags(self, ctx):
        tags = Database.getTags(user_id = ctx.author.id, guild_id = ctx.guild.id)
        tag_set = []
        if not tags:
            await ctx.channel.send("You don't have any tags yet.")
            return
        for tag in tags:
            tag_set.append(tag[3])
        message = "Your tags are: `"
        message += ', '.join(tag_set) + '`'
        await ctx.channel.send(message)
        
    @commands.command()
    async def hideTags(self, ctx, state):
        hide = True
        if state in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'hide'):
            hide = True
        elif state in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'show'):
            hide = False
        else:
            await ctx.channel.send("Not sure what that means. Use +help hideTags for the list you can use.")
            return

        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        uid = str(ctx.author.id)
        guid = str(ctx.guild.id)
        data[guid]['users'][uid]['specifyTags'] = not hide
        message = "Alright, hiding your tags is now set to " + str(not hide)
        await ctx.channel.send(message)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)
            
    @commands.command()
    async def addCombo(self, ctx, *tags):
        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        user.tagCombos.append(tags)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send("Alright, I added your new combo list")
        
    @commands.command()
    async def deleteCombo(self, ctx, id: int):
        """Removes the tag combination from your list of combos that has the given id"""
        realId = id - 1
        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        message = ""
        if user.tagCombos[realId]:
            del user.tagCombos[realId]
            message = "Alright, that tag combo doesn't exist anymore for you."
        else:
            message = "Dude, you don't _have_ a tag combo with that id. Double check your id's with +myCombos"

        await ctx.channel.send(message)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)
            
    @commands.command()
    async def addTagsByServer(self, ctx, guid, *tags):
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
            for tag in tags:
                if tag not in user.tags:
                    user.tags.append(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send(f"Alright, I added {tags} to your tags for {data[guid]['name']}.")
        return


    @commands.command()
    async def removeTagsByServer(self, ctx, guid, *tags):
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
            for tag in tags:
                if tag in user.tags:
                    user.tags.remove(tag)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send(f"Alright, I removed {tags} to your tags for {data[guid]['name']}.")
        return


    @commands.command()
    async def addComboByServer(self, ctx, guid, *tags):
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
            user.tagCombos.append(tags)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send("Alright, I added your new combo list")
        return
    
    @commands.command()
    async def removeComboByServer(self, ctx, guid, *tags):
        #TODO
        pass
    
    @commands.command()
    async def addBlacklistByServer(self, ctx, guid, *tags):
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
            user.blacklist.append(tags)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send(f"Alright, I added {tags} to your blacklist for {data[guid]['name']}")
        return


    @commands.command()
    async def removeBlacklistByServer(self, ctx, guid, *tags):
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
            user.blacklist.remove(tags)

        with open(self.guildsFile, "w") as dataFile:
            json.dump(data, dataFile, indent=4)

        await ctx.channel.send(f"Alright, I removed {tags} from your blacklist for {data[guid]['name']} ")
        return
    
    @commands.command()
    async def myCombos(self, ctx):
        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return

        message = ""
        id = 1
        for combo in user.tagCombos:
            message += f"{id} {combo}\n"
            id += 1

        if message == "":
            message = "You don't have any combos right now dude. Use addCombo <tags> to add at least one."
        await ctx.channel.send(message)