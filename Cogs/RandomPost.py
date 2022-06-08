import itertools
from random import randint
import re
import discord
from discord.ext import commands
from Cogs.PingPeople import ping_people
from Services import IQDBService
from Services.GelbooruService import getRandomSetWithTags as gelSet
from Services.DanbooruService import getRandomSetWithTags as danSet

from Utilities.ProcessUser import processUser

# https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html#ext-commands-cogs

ROLL_LIMIT = 10
JOKE_MODE = False

class RandomPost(commands.Cog):
    '''
        Cog for fetching random posts from boorus, such as Gelbooru and/or Danbooru
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['randomimage','rollimage'])
    async def randomPost(self, ctx, *tags):
        
        """Fetches a random post from multiple sites that contains the provided tag(s) and then displays it in a custom embed.

        Args:
            ctx (_type_): Context of the message, passed in automatically by discord.
        """

        user, data = await processUser(ctx, guid=ctx.guild.id, uid=ctx.author.id)
        if user == None or data == None:
            #there was an issue, break
            return -1

        cleaned_tags = []
        for tag in tags:
            cleaned_tags.append(tag.replace('`', ''))

        guid = str(ctx.guild.id)
        cid = str(ctx.channel.id)
        bannedTags = []
        bannedPorn = []

        for tag in data[guid]['bannedExplicitTags']:
            bannedPorn.append(tag)
        for tag in data[guid]['bannedGeneralTags']:
            bannedTags.append(tag)
        for tag in data[guid]['channels'][cid]['bannedTags']:
            bannedTags.append(tag)
        for tag in data[guid]['channels'][cid]['bannedNSFWTags']:
            bannedPorn.append(tag)
            
        safe_exemptions = data[guid]['channels'][cid]['safe_exemptions']
        nsfw_exemptions = data[guid]['channels'][cid]['nsfw_exemptions']
        
        rolled_data = await self.getImageFromTags(banned_tags=bannedTags, banned_porn=bannedPorn, query_set=cleaned_tags,
                                                  safe_exemptions=safe_exemptions, nsfw_exemptions=nsfw_exemptions, channel_explicit=ctx.channel.is_nsfw() )

        if rolled_data == None:
            await ctx.channel.send('Sorry, I couldn\'t find anything with those tags.')
            return

        sources = rolled_data['sources']
        image_url = rolled_data['image_url']
        tag_list = rolled_data['tag_list']
        is_explicit = rolled_data['is_explicit']
        
    
        bot_avatar = self.bot.user.avatar_url
        bot_image = bot_avatar.BASE + bot_avatar._url
        description = '\n'.join(sources)

        #await ctx.channel.send("Alright, here's your random post. Don't blame me if it's cursed.")
        if image_url.endswith('.mp4'):
            embed_msg = await ctx.channel.send(image_url)
            return 1

        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description=description,
            type="rich",
        )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
        embed_obj.set_image(url=image_url)

        embed_msg = await ctx.channel.send(embed=embed_obj)

        await self.updateRolledImage(sources=sources, ctx=ctx, embed_msg=embed_msg, image_url=image_url, tag_list=tag_list, isExplicit=is_explicit)
        return 1
    
    #Blocking calls
    async def updateRolledImage(self, ctx, sources, embed_msg, image_url, tag_list, isExplicit):
        extra_data = await IQDBService.getInfoUrl(image_url)
        bot_avatar = self.bot.user.avatar_url
        bot_image = bot_avatar.BASE + bot_avatar._url
        if extra_data != None:
            for url in extra_data['urls']:
                if url not in sources:
                    sources.append(url)

        for i in range(len(sources)):
            if re.match('https?://', sources[i]) == None:
                sources[i] = "https://" + sources[i]

        description = '\n'.join(sources)

        #update embed

        embed_obj = discord.Embed(
            colour=discord.Colour(0x5f4396),
            description=description,
            type="rich",
        )
        embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
        embed_obj.set_image(url=image_url)
        if isExplicit and not ctx.channel.is_nsfw():
            #embed_msg = await ctx.channel.send("|| " + image_url + " ||")
            pass
        else:
            embed_msg = await embed_msg.edit(embed=embed_obj)
    
        await ping_people(ctx, tag_list, exempt_user = ctx.message.author)

        return
    
    @commands.command(pass_context=True, aliases=['randomporn', 'randomexplicit', 'rollporn'])
    async def randomNsfw(self, ctx, *tags):
       if not ctx.channel.is_nsfw():
           await ctx.channel.send("Sorry, I can't roll NSFW in a channel that's not age-restricted. Try randomPost or randomSafe instead.")
           return
       await ctx.invoke(self.bot.get_command('randomPost'), 'rating:explicit', *tags)

    
    @commands.command(pass_context=True, aliases=['randomsafe', 'rollsafe'])
    async def randomSfw(self, ctx, *tags):
        await ctx.invoke(self.bot.get_command('randomPost'), 'rating:general', *tags)


    def mistakenTagSearcher(self, tags:list):
        search_set = []
        for p in itertools.product([True, False], repeat=len(tags)):
            search_term = []
            params = list(zip(tags, p))
            for entry in params:
                if entry[1] and len(entry[0].split('_') ) == 2:
                    spl = entry[0].split('_')
                    spl = spl[1] + '_' + spl[0]
                    search_term.append(spl)
                else:
                    search_term.append(entry[0])
            search_set = sorted(search_set)
            if search_term not in search_set:
                search_set.append(search_term)
                
        return search_set
    
    async def getImageFromTags(self, banned_tags:list, banned_porn:list, query_set:list, safe_exemptions:list, nsfw_exemptions:list, channel_explicit:bool):
        #TODO: overhaul the randompost to call this
        
        data = {
            'sources': [],
            'image_url': "",
            'tag_list': [],
            'is_explicit': False
        }
        
        search_set = self.mistakenTagSearcher(query_set)
        for entry in search_set:
            randomDanSet = await danSet(entry)
            randomGelSet = await gelSet(entry)

            if 'post' in randomGelSet:
                randomGelSet = randomGelSet['post']
            
            full_set = []
            for entry in randomDanSet:
                full_set.append((entry, 'dan'))
            for entry in randomGelSet:
                full_set.append((entry, 'gel'))
            
            if len(full_set) == 0 or full_set == [('@attributes', 'gel')]:
                continue    #no results, move to next one

            for i in range(ROLL_LIMIT):

                rolled_number = randint(0, len(full_set))            
                random_item = full_set[rolled_number]

                if random_item[1] == 'dan':
                    tag_list = random_item[0]['tag_string'].split()
                    image_url = random_item[0]['file_url']
                    isExplicit = random_item[0]['rating'] == 'e'
                elif random_item[1] == 'gel':
                    tag_list = random_item[0]['tags'].split()
                    image_url = random_item[0]['file_url']
                    isExplicit = random_item[0]['rating'] == 'explicit'
                    
                marked_tags = []
                for tag in tag_list:
                    if tag in banned_tags:
                        if not any([tag, '*all*'] in exemption for exemption in safe_exemptions ):
                            marked_tags.append(tag)
                    if isExplicit and tag in banned_porn: 
                        if not any([tag, '*all*'] in exemption for exemption in nsfw_exemptions):               
                            marked_tags.append(tag)
                if marked_tags != []:
                    for tag in tag_list:
                        if marked_tags == []:
                            break   #reduce cost measure
                        else:    
                            for marked_tag in marked_tags:
                                test_pair = [tag, marked_tag]
                                if any(test_pair == exemption for exemption in safe_exemptions) and not isExplicit:
                                    marked_tags.remove(marked_tag)
                                if any(test_pair == exemption for exemption in nsfw_exemptions) and isExplicit:
                                    marked_tags.remove(marked_tag)
                
                if isExplicit and not channel_explicit:
                    continue
                            
                if marked_tags != []:
                    continue
                
                #if still here then the image has passed and can be returned

                sources = []

                if random_item[1] == 'gel':
                    post_id = random_item[0]['id']
                    sources.append(random_item[0]['source'])
                    sources.append(
                                f'https://gelbooru.com/index.php?page=post&s=view&id={ post_id }')
                    image_url = random_item[0]['file_url']
                elif random_item[1] == 'dan':
                    post_id = random_item[0]['id']
                    sources.append(random_item[0]['source'])
                    sources.append(f'https://danbooru.donmai.us/posts/{post_id}')
                    image_url = random_item[0]['file_url']
            
                for source in sources:
                    if source.strip() == '':
                        sources.remove(source)
                        
                data['image_url'] = image_url
                data['is_explicit'] = isExplicit
                data['sources'] = sources
                data['tag_list'] = tag_list
                return data
                
        return None