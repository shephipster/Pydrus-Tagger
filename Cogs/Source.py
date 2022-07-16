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
                
    @commands.command(aliases=['tags'])
    async def getTagsFor(self, ctx):
        """ Gets the tags for a given image """
        if not ctx.message.attachments:
            await ctx.channel.send("You have to give me an image to look up you know.")
        else:
            for attachment in ctx.message.attachments:
                imageLink = attachment.url
                data = await IQDBService.getInfoUrl(imageLink)
                tag_list = data['tags']
                output = "The tag list for that image is: "
                for tag in tag_list:
                    output = output + tag + ", "

                await ctx.channel.send(output[:-2])
                
    