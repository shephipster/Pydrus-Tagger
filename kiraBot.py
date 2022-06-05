import asyncio
import html
import json
import os
import re
import time
from io import BytesIO

import discord
import imagehash
import requests
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
from scipy.spatial import distance

import Services.IQDBService as IQDB
from Cogs.Activities import Activities
from Cogs.Luck import Luck
from Cogs.Management import Management
from Cogs.PingPeople import ping_people
from Cogs.RandomPost import RandomPost
from Cogs.Source import Source
from Cogs.TagManager import TagManager
from Cogs.UserManagement import UserManagement
from Entities import Post
from Services import TwitterService

load_dotenv()
DEBUG = False  # set to false for live versions
#Use this set for the normal version
TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')

# This is used for debugging
if DEBUG:
	DISCORD_API_KEY = os.getenv('DISCORD_TEST_API_KEY')
	TOKEN = os.getenv('DISCORD_TEST_TOKEN')

description = ''' Kira bot. Pings users for images that have tags they like. '''
#Consts
postTTL = -1  # how long a post should be recorded before it is up for deletion. -1 for no time
# number of images to record for repost detection, -1 for no limit (CAREFUL OF THIS)
logSizeLimit = 255
repostDistance = 10  # how similar an image must be to be a repost. Smaller means more similar, account for Discord compression

#what people put before 'twitter' in a url to fix it.
# NOTE: this is not like fx/vx twitter. It doesn't actually host the url, it instead makes its own embed using
# data it finds at the twitter url given. So if you post something and then add the prefix the bot will follow
# up with a custom-made embed that contains the content as best it can
EMBED_FIX_PREFIX = 'kira'

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guild_messages = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='+',
                   description=description, intents=intents, case_insensitive=True)

logFile = './kiraBotFiles/imageLog.json'
guildsFile = os.getenv('GUILDS_FILE')

pic_ext = ['.jpg', '.png', '.gif', '.jpeg', '.bmp']
ROLL_LIMIT = 10

bot.add_cog(Activities(bot))
bot.add_cog(Luck(bot))
bot.add_cog(Management(bot))
bot.add_cog(RandomPost(bot))
bot.add_cog(Source(bot))
bot.add_cog(TagManager(bot))
bot.add_cog(UserManagement(bot))
manager = bot.get_cog('Management')


@bot.event
async def on_guild_join(guild):
	print("Joined guild", guild)
	await manager.updateGuildCommand(guild)


@bot.event
async def on_ready():
	initFiles()
	await manager.updateAllGuilds()
	print('Running')


def initFiles():
	if not os.path.exists(logFile):
		with open(logFile, 'a') as file:
			file.write("{\n}")

	if not os.path.exists(guildsFile):
		with open(guildsFile, 'a') as file:
			file.write("{\n}")


@bot.event
async def on_message(message):
	channel = message.channel
	if message.author.bot == True:
		#This causes bot to by-pass the repost filter. Do we care? I don't, and who would notice
		return

	if "fuck you" in message.content.lower():
		if "kira" in message.content.lower():
			await channel.send("fuck me yourself, coward")
		else:
			await channel.send("fuck them yourself, coward")
	elif "fuck me" in message.content.lower():
		await channel.send("that's kinda gross dude")

	if not message.content or message.content[0] != '+':
		if message.attachments:
			for attachment in message.attachments:
				file = await attachment.to_file()
				file = file.fp
				data = IQDB.getInfoDiscordFile(file)
				if data != None and not 'error' in data:
					tag_list = data['tags']
					await ping_people(message, tag_list, exempt_user=message.author)

					if repostDetected(message.channel.guild, attachment.url):
						await message.add_reaction(str('♻️'))
		elif message.embeds:
			for embed in message.embeds:
				imageLink = embed.url
				data = IQDB.getInfoUrl(imageLink)
				if data != None:
					tag_list = data['tags']
					await ping_people(message, tag_list)
					if repostDetected(message.channel.guild, imageLink):
						await message.add_reaction(str('♻️'))

	await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    #If a message is edited from a standard Twitter link to a custom one, the bot will create an embed and post it in the channel. While not as pretty as vx/fx twitter, it doesn't rely on external websites
	#and everything is in-memory so it's not physically capable of spying on what you use it for. Other sites to come. Pixiv would be next but they don't have an api so...
	if re.search(f"https?://twitter.com/[\S]+/status/[0-9]+(\?[\S]+)*", before.content) != None and re.search(f"https?://{EMBED_FIX_PREFIX}twitter.com/[\D]+/status/[0-9]+(\?[\S]+)*", after.content) != None:
		parsed_text = re.search(
		    f"(https?://twitter.com/[\S]+/status/[0-9]+)(\?[\S]+)*", before.content)
		parsed_text = parsed_text.group(1)
		tweet_meta = TwitterService.get_tweet_meta_from_link(parsed_text)
		embed_type = TwitterService.tweetType(tweet_meta['raw_data'])

		media = []
		media_urls = []
		is_gif = False
		is_video = False
		max_bitrate = 0
		max_bitrate_index = -1
		for entry in tweet_meta['raw_data']['includes']['media']:
			media.append(entry)
			if entry['type'] == 'animated_gif':
				is_gif = True
				for ind, url in enumerate(entry['variants']):
					media_urls.append(url['url'])
					if 'bit_rate' in url:
						if max_bitrate > url['bit_rate']:
							max_bitrate = url['bit_rate']
							max_bitrate_index = ind
			elif entry['type'] == 'video':
				for ind, url in enumerate(entry['variants']):
					media_urls.append(url['url'])
					if 'bit_rate' in url:
						if max_bitrate > url['bit_rate']:
							max_bitrate = url['bit_rate']
							max_bitrate_index = ind
				is_video = True
			else:
				media_urls.append(entry['url'])

		if not is_gif and not is_video:
			finalImage = TwitterService.genImageFromURL(media_urls)
			imgIo = BytesIO()
			finalImage = finalImage.convert("RGB")
			finalImage.save(imgIo, 'JPEG', quality=70)
			imgIo.seek(0)
			tempFile = discord.File(fp=imgIo, filename="image.jpeg")

			#create the custom embed
			#TODO: Replace avatar/image with the twitter poster's
			bot_avatar = bot.user.avatar_url
			bot_image = bot_avatar.BASE + bot_avatar._url

			#TODO: include more info if need be
			body = f"Original: {parsed_text} \n" + tweet_meta['raw_data']['data']['text'] + \
			    f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + \
                            f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

			body = html.unescape(body)

			embed_obj = discord.Embed(
				colour=discord.Colour(0x5f4396),
				description=body,
				type="rich",
				url=parsed_text,
			)

			embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

			embed_obj.set_image(url="attachment://image.jpeg")
			await after.channel.send(file=tempFile, embed=embed_obj)
		elif is_gif:
			#Apparently Twitter hides gif urls, but not jpgs/pngs or videos
			#Gifs do include mp4 variants, so we'll use that
			bot_avatar = bot.user.avatar_url
			bot_image = bot_avatar.BASE + bot_avatar._url

			#TODO: include more info if need be
			body = f"Original: {parsed_text} \n" + tweet_meta['raw_data']['data']['text'] + \
			    f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + \
                            f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

			embed_obj = discord.Embed(
				colour=discord.Colour(0x5f4396),
				description=body,
				type="rich",
				url=parsed_text,
			)
			embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

			embed_obj.set_image(url=media_urls[max_bitrate_index])
			await after.channel.send(embed=embed_obj)
			await after.channel.send(media_urls[max_bitrate_index])
		elif is_video:

			bot_avatar = bot.user.avatar_url
			bot_image = bot_avatar.BASE + bot_avatar._url

			#TODO: include more info if need be
			body = f"Original: {parsed_text} \n" + tweet_meta['raw_data']['data']['text'] + \
			    f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + \
                            f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

			embed_obj = discord.Embed(
				colour=discord.Colour(0x5f4396),
				description=body,
				type="rich",
				url=parsed_text,
			)
			embed_obj.set_author(name="Kira Bot", icon_url=bot_image)

			embed_obj.set_image(url=media_urls[max_bitrate_index])
			await after.channel.send(embed=embed_obj)
			await after.channel.send(media_urls[max_bitrate_index])


@bot.event
async def on_command_error(ctx, error):
	print(error)
	return


#region old_tagging_code
#This code does work, and it works well. However, with the new sauceNaoApi it's not
#really needed anymore. We're leaving it in though because of its influence.
#Also, if there's any 'heavy' searching (5 in 30s and 300 in 24h) the SN API will
#lock out, so we might have to resort to calling this one if that happens
""" This code pretty much entirely from ImagineNotHavingAnAlt, bless their soul """
# def query_iqdb(filename):
# 	""" Gets the search result page for a danbooru iqdb search on filename  """
# 	url = 'https://danbooru.donmai.us/iqdb_queries'
# 	sourceURL = {"search[url]":filename}
# 	result = requests.post(url, data=sourceURL, auth=("shephipster",APIKey) )
# 	return result

# def booru_link(res):
# 	""" Takes the result page of a search and parses it """
# 	threshold = 85.0
# 	tag_list = []

# 	#convert result into a text string
# 	restext = res.text
# 	#regex to see if the high-similarity section is empty
# 	highSimilarity_text = re.compile(r"iqdb-posts-high-similarity\">\s*.*(<a.*</a>)")
# 	highSimilarity = highSimilarity_text.search(restext)
# 	if debug:
# 		print("High similarity result: " , highSimilarity)
# 	#check if there is at least one highSimilarity
# 	if highSimilarity != None:
# 		#not null, get the first result
# 		mostSimilar = highSimilarity.group(0)
# 		#print(mostSimilar)
# 		#obtain the tags in the image
# 		partitionedTags = mostSimilar.partition("data-tags=")[2]
# 		split_string = partitionedTags.split("\"", 2)
# 		substring = split_string[1]
# 		tag_list = substring.split(" ")
# 		return tag_list
# 	#if there is no highly similar image try the most similar of the lower results at a threshold
# 	else:
# 		try:
# 			lowerSimilarity_percentage_text = re.compile(r"iqdb-posts-low-similarity\".*>\s*(.*\s){17}")
# 			lowerSimilarity_tag_text = re.compile(r"iqdb-posts-low-similarity\".*>\s*(.*\s){10}")
# 			lowerSimilarity_percentage = lowerSimilarity_percentage_text.search(restext)
# 			lowerSimilarity_tags = lowerSimilarity_tag_text.search(restext)
# 			if lowerSimilarity_percentage != None:
# 				#determine if even worth getting tags for
# 				parsed_percentage = lowerSimilarity_percentage.group(0).split('>')[-2]
# 				real_percent = parsed_percentage.split("%")[0]
# 				if float(real_percent) >= threshold:
# 					#get the tags
# 					mostSimilar = lowerSimilarity_tags.group(0)
# 					partitionedTags = mostSimilar.partition("data-tags=")[2]
# 					split_string = partitionedTags.split("\"", 2)
# 					substring = split_string[1]
# 					tag_list = substring.split(" ")
# 					return tag_list
# 		except TypeError:
# 			print("Couldn't find the image on Danbooru")
# 			return tag_list
# 	return tag_list
#endregion


def repostDetected(guild, file):
	#https://github.com/polachok/py-phash#:~:text=py-pHash%20Python%20bindings%20for%20libpHash%20%28http%3A%2F%2Fphash.org%2F%29%20A%20perceptual,file%20derived%20from%20various%20features%20from%20its%20content.

	image = Image.open(requests.get(file, stream=True).raw)
	hash = imagehash.phash(image)

	reposted = False
	latestPost = Post.Post(file, time.time(), str(hash), str(guild))

	f = open(logFile)
	data = json.load(f)
	f.close()

	#TODO: include embeds/urls

	for post in data:
		values = data[post]
		if postExpired(values['timePosted']):
			del data[post]
		elif values['guild'] == latestPost.guild:
			dist = distance.hamming(values['phash'], latestPost.phash) * len(hash)
			if dist <= repostDistance:
				reposted = True

	if len(data) >= logSizeLimit:
		del data[0]

	data[len(data)] = latestPost

	with open(logFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4, default=Post.Post.to_dict)
	return reposted


def postExpired(timePosted: float):
	if postTTL == -1:
		return False
	return time.time() - timePosted >= postTTL


bot.run(TOKEN)
