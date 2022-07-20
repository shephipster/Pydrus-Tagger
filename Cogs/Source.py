import re
import discord
from discord.ext import commands

from Services import IQDBService

class Source(commands.Cog):
    def __init__(self, bot) :
        self.bot = bot
        
    @commands.command(aliases=['sauce', 'urls', 'sites'])
    async def source(self, ctx):
        if not ctx.message.attachments:
            await ctx.channel.send("You have to give me an image to look up you know.")
        else:
            await ctx.channel.send("Alright, lemme see if I can't find out where these are from...")
            for attachment in ctx.message.attachments:
                file = await attachment.to_file()
                file_url = attachment.url
                file = file.fp
                data = await IQDBService.getInfoDiscordFile(file)
                if 'error' in data.keys():
                    await ctx.channel.send(f"Sorry, I had trouble finding that. You can try checking SauceNao here: {data['sauceNao_redirect']}")
                    return

                cleaned_urls = []
                for url in data['urls']:
                    if re.match('https?://', url) == None:
                        cleaned_urls.append('https://' + url)
                    else:
                        cleaned_urls.append(url)

                description = "Sources:\n" + '\n'.join(cleaned_urls)
                bot_avatar = self.bot.user.avatar_url
                bot_image = bot_avatar.BASE + bot_avatar._url
                embed_obj = discord.Embed(
                    colour=discord.Colour(0x5f4396),
                    description=description,
                    type="rich",
                )
                embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
                embed_obj.set_image(url=file_url)

                # url_list = data['urls']
                # output = "Found that image at the following sites:\n "
                # for url in url_list:
                # 	output = output + "http://" + url + "\n"

                # await ctx.channel.send(output)
                await ctx.reply(embed=embed_obj)
                
    @commands.command(aliases=['tags','tagsFor'])
    async def getTagsFor(self, ctx):
        """ Gets the tags for a given image """
        if not ctx.message.attachments:
            await ctx.channel.send("You have to give me an image to look up you know.")
        else:
            count = 1
            for attachment in ctx.message.attachments:
                await ctx.channel.send(f"Looking up the tags for picture #{count}...")
                count += 1
                imageLink = attachment.url
                data = await IQDBService.getInfoUrl(imageLink)
                if data == None:
                    #no result was found, sauceNao couldn't find anything
                    output = "Sorry, I couldn't find anything like it on IQDB."
                else: 
                    tag_list:set = data['tags']
                    tag_list = sorted(tag_list)
                    output = "The tag list for that image is: `"
                    output += ', '.join(tag_list)
                    output += '`'

                await ctx.channel.send(output)
                
    