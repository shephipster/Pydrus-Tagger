import asyncio
from discord.ext import commands
import discord

POLL_LIMIT = 10

class Activities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx, *options):
        message = "Cast your vote using the reactions below!"
        optionCount = 1
        pollMap = dict()
        if len(options) > POLL_LIMIT:
            await ctx.channel.send(f"I can only do a poll with up to {POLL_LIMIT} options")
            return
        for option in options:
            message += "\n" + self.getNumericEmoji(optionCount) + " " + option
            optionCount += 1
            
        bot_avatar = self.bot.user.avatar_url
        bot_image = bot_avatar.BASE + bot_avatar._url
        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description=message,
            type="rich",
        )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
        
        msg = await ctx.channel.send(embed=embed_obj)

        #Generate reactions
        optionCount = 1
        for option in options:
            reaction = self.getNumericReaction(optionCount)
            await msg.add_reaction(reaction)
            pollMap[reaction] = option
            optionCount += 1
        return msg, pollMap
    
    @commands.command(aliases=['timepoll', 'limitpoll', 'limitedpoll'])
    async def timedPoll(self, ctx, seconds, *options):

        try:
            int(seconds)
        except:
            await ctx.channel.send("You need to give me the time first then your options")
            return

        results = dict()
        msg: discord.Message
        msg, pollMap = await self.poll(ctx, *options)
        await asyncio.sleep(int(seconds))
        msg = await ctx.channel.fetch_message(msg.id)
        for reaction in msg.reactions:
            if reaction.count not in results.keys():
                results[reaction.count] = [reaction.emoji]
            else:
                results[reaction.count].append(reaction.emoji)
        sortedResults = {key: value for key, value in sorted(
            results.items(), key=lambda item: item[0], reverse=True)}

        message = "Stop your voting! The results are in and are...\n"
        ranking = 1
        for place in sortedResults:
            message += self.getNumericEmoji(ranking) + " "
            ranking += 1
            for item in sortedResults[place]:
                message += pollMap[item] + ", "
            message += f'with {int(place)-1} votes\n'
        await msg.clear_reactions()
        await msg.edit(content=message)
        return
    
    def getNumericEmoji(num):
        switch = {
            1: ':one:',
            2: ':two:',
            3: ':three:',
            4: ':four:',
            5: ':five:',
            6: ':six:',
            7: ':seven:',
            8: ':eight:',
            9: ':nine:',
            10: ':zero:'
        }
        return switch.get(num, ':question:')


    def getNumericReaction(num):
        #This is a tad wonky and require the actual emoji (win + . (and not the numpad .) to access)
        switch = {
            1: '1️⃣',
            2: '2️⃣',
            3: '3️⃣',
            4: '4️⃣',
            5: '5️⃣',
            6: '6️⃣',
            7: '7️⃣',
            8: '8️⃣',
            9: '9️⃣',
            10: '0️⃣'
        }
        return switch.get(num, '❓')