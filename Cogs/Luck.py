import asyncio
from random import choice, choices, randint
import re
import discord
from discord.ext import commands

class Luck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def roll(self, ctx, regex):
        numRollsGroup = re.search("\d+d", regex)
        diceSizeGroup = re.search("d\d+", regex)
        if not numRollsGroup or not diceSizeGroup:
            await ctx.channel.send("The format is \{numDice\}d\{diceSize\}. Try 7d12 as an example.")
        else:
            numRolls = int(numRollsGroup.group()[:-1])
            diceSize = int(diceSizeGroup.group()[1:])
            rolls = list()
            total = 0
            for x in range(0, numRolls):
                roll = randint(1, diceSize)
                rolls.append(roll)
                total += roll
            message = "" + str(regex) + ": " + str(rolls) + "\nTotal: " + str(total)
            await ctx.channel.send(message)
            
    @commands.command()
    async def random(self, ctx, *inputs):
        #get how many to select, 1 if none provided
        instructions = ""
        for i in inputs:
            instructions += i
        selectionsGroup = re.search("\d*\s*\[", instructions)

        if (selectionsGroup.group() == '['):
            numSelections = 1
        else:
            numSelections = int(selectionsGroup.group()[:-1])

        #get the list of options
        groupOptions = re.search("\[.+\]", instructions)
        options = groupOptions.group()[1:-1].split(',')

        #do we replace after a pick?
        replace = False
        replaceGroup = re.search("\]\s*.+", instructions)
        if replaceGroup:
            replace = True

        #can we select enough options if no replacement?
        picked = list()
        if replace == False:
            if numSelections > options.__len__():
                await ctx.channel.send("You're asking me to pick more things than you gave me. See if you forgot an option or typed the number in wrong.")
            elif numSelections == options.__len__():
                await ctx.channel.send("You're asking me to pick as many things as you gave, wouldn't that just be all of them? Double check you didn't type the number wrong.")
            else:
                for x in range(numSelections):
                    item = choice(options)
                    picked.append(item)
                    options.remove(item)
                await ctx.channel.send(str(picked))
        else:
            picked = choices(options, k=numSelections)
            await ctx.channel.send(str(picked))
            
    @commands.command(aliases=['selection', 'lottery', 'raffle'])
    async def giveaway(self, ctx, winners, time, *allowed_roles):
        #get the number of winners
        num_winners = int(winners)
        #get the giveaway time, default to minutes
        if time.isdigit():
            delay = int(time) * 60
        else:
            if re.search('(\d+)m', time) != None:
                delay = int(re.search('(\d+)', time).group(1)) * 60
            elif re.search('(\d+)s', time) != None:
                delay = int(re.search('(\d+)', time).group(1))
            elif re.search('(\d+)h', time) != None:
                delay = int(re.search('(\d+)', time).group(1)) * 3600
        #get what roles can enter
        available_roles = []
        available_roles_mentions = []
        if allowed_roles == ():
            for gr in ctx.guild.roles:
                if gr.name == '@everyone':
                    available_roles.append(gr)
                    available_roles_mentions.append(gr.mention)
                    break
        else:
            for role in allowed_roles:
                role_id = int(role[3:-1])
                for gr in ctx.guild.roles:
                    if gr.id == role_id:
                        available_roles.append(gr)
                        available_roles_mentions.append(gr.mention)

        roles_string = ','.join(available_roles_mentions)

        description = f'{ctx.author.name} is running a lottery!\n{winners} lucky winners will be selected from those that ' \
            + \
            f'click the 🎁 reaction below so long as you are {roles_string}.\nBetter hurry up though, it will only last for so long!'
        bot_avatar = self.bot.user.avatar_url
        bot_image = bot_avatar.BASE + bot_avatar._url
        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description=description,
            type="rich",
        )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
        msg = await ctx.channel.send(embed=embed_obj)
        await msg.add_reaction(str('🎁'))

        await asyncio.sleep(int(delay))
        # update message with those that reacted
        msg = await ctx.channel.fetch_message(msg.id)
        reactors = await msg.reactions[0].users().flatten()
        #available
        can_be_selected = []
        for person in reactors:
            if person.bot == False and any(role in available_roles for role in person.roles):
                can_be_selected.append(person)

        #get W random winners, do NOT allow repeats
        if can_be_selected == []:
            await ctx.channel.send("There were no winners this time around. If you entered, make sure you have one of the roles for the lottery.")
            return

        picked = list()
        for x in range(num_winners):
            if can_be_selected == []:
                #out of people, done
                break
            item = choice(can_be_selected)
            picked.append(item)
            can_be_selected.remove(item)

        message = f'Selection is over! Will the following people please message {ctx.message.author.mention} for the follow-up.'
        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description="Entry period is over!",
            type="rich",
        )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

        await msg.edit(embed=embed_obj)

        winner_mentions = []
        for winner in picked:
            winner_mentions.append(winner.mention)

        winners_string = ",".join(winner_mentions)
        message += "\n" + winners_string
        await ctx.channel.send(message)
