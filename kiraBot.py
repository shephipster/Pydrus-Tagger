from io import BytesIO
import discord
import requests
import json
import time
import imagehash
import os
import re
import shutil

from random import choice, choices, randint
from dotenv import load_dotenv
from Services import TwitterService
from Services.GelbooruService import getRandomPostWithTags
from Services.GelbooruService import getRandomSetWithTags as gelSet
from Services.DanbooruService import getRandomSetWithTags as danSet
from Utilities.Tagger import Tagger

import Utilities.TagAPI as TagAPI
from Entities import User, Post, Guild
from discord.ext import commands
from PIL import Image
from scipy.spatial import distance
import Services.IQDBService as IQDB

load_dotenv()
DEBUG = False
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
JOKE_MODE = False
POLL_LIMIT = 10  # maximum number of items allowed in a poll

#what people put before 'twitter' in a url to fix it. 
# NOTE: this is not like fx/vx twitter. It doesn't actually host the url, it instead make it's own embed using
# data it finds at the twitter url given. So if you post something and then add the prefix the bot will follow
# up with a custom-made embed that contains the content as best it can
EMBED_FIX_PREFIX = 'kira' 

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guild_messages = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='+',
                   description=description, intents=intents)

logFile = './kiraBotFiles/imageLog.json'
guildsFile = './kiraBotFiles/guilds.json'
tempImageLoc = './kiraBotFiles/'

pic_ext = ['.jpg', '.png', '.gif', '.jpeg', '.bmp']
ROLL_LIMIT = 10

@bot.event
async def on_guild_join(guild):
	print("Joined guild", guild)  
	await updateGuildCommand(guild)

@bot.event
async def on_ready():
	initFiles()
	await updateAllGuilds()
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
	if message.author == bot.user:
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
					await ping_people(message, tag_list)

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
		parsed_text = re.search(f"(https?://twitter.com/[\S]+/status/[0-9]+)(\?[\S]+)*", before.content)
		parsed_text = parsed_text.group(1)
		tweet_meta = TwitterService.get_tweet_meta_from_link(parsed_text)
		embed_type = TwitterService.tweetType(tweet_meta['raw_data'])

		media = []
		media_urls = []
		is_gif = False
		for entry in tweet_meta['raw_data']['includes']['media']:
			media.append(entry)
			if entry['type'] == 'animated_gif':
				media_urls.append(entry['variants'][0]['url'])
				is_gif = True
			else:
				media_urls.append(entry['url'])
   
		if not is_gif:
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
			body = f"Original: {parsed_text}" + tweet_meta['raw_data']['data']['text'] + f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

			embed_obj = discord.Embed(
				colour=discord.Colour(0x5f4396),
				description=body,
				type="rich",
				url=parsed_text,
			)

			embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
	
			embed_obj.set_image(url="attachment://image.jpeg")
			await after.channel.send(file=tempFile, embed=embed_obj)
		else:
			bot_avatar = bot.user.avatar_url
			bot_image = bot_avatar.BASE + bot_avatar._url
	
			#TODO: include more info if need be
			body = f"Original: {parsed_text}" + tweet_meta['raw_data']['data']['text'] + f"\n❤{tweet_meta['raw_data']['data']['public_metrics']['like_count']}" + f"\t🔁{tweet_meta['raw_data']['data']['public_metrics']['retweet_count']}"

			embed_obj = discord.Embed(
				colour=discord.Colour(0x5f4396),
				description=body,
				type="rich",
				url=parsed_text,
			)
			embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
	
			embed_obj.set_image(url=media_urls[0])
			await after.channel.send(embed=embed_obj)
			await after.channel.send(media_urls[0])

@bot.event
async def on_command_error(ctx, error):
	print(error)
	return

@bot.command(aliases=['sauce', 'urls', 'sites'])
async def source(ctx):
	if not ctx.message.attachments:
		await ctx.channel.send("You have to give me an image to look up you know.")
	else:
		for attachment in ctx.message.attachments:
			file = await attachment.to_file()
			file_url = attachment.url
			file = file.fp
			data = IQDB.getInfoDiscordFile(file)
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
			bot_avatar = bot.user.avatar_url
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
			await ctx.channel.send(embed=embed_obj)

@bot.command(aliases=['init', 'initServer'])
async def initGuild(ctx):
	#for each file, if guild not already part of it add them
	if type(ctx.channel) == discord.channel.DMChannel:
		await ctx.channel.send("You can't use this command in a DM, how am I going to know what server you want?")
		return

	guildUID = str(ctx.guild.id)

	f = open(guildsFile)
	data = json.load(f)
	f.close()

	guild = Guild.Guild(ctx.guild)

	if guildUID not in data.keys():
		#guild not initialized yet, add it
		data[f'{guildUID}'] = guild.__dict__
		with open(guildsFile, 'w') as f:
			json.dump(data, f, indent=4)
		await ctx.channel.send("Added your guild to the list")
	else:
		await ctx.channel.send("Your guild has already been initialized")
	return


@bot.command(aliases=['tagme', 'addTag', 'addtag'])
async def tagMe(ctx, *tags):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	for tag in tags:
		if tag not in user.tags:
			user.tags.append(tag.lower())

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Alright, I added {tags} to your tags.")
	return


@bot.command(aliases=['untag', 'untagme', 'removeTag'])
async def untagMe(ctx, *tags):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	for tag in tags:
		if tag in user.tags:
			user.tags.remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I took {tags} out of your tags list.")
	return


@bot.command(aliases=[])
async def blacklist(ctx, *tags):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	for tag in tags:
		if tag not in user.blacklist:
			user.blacklist.append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send("Alright, I update your blacklist for you.")


@bot.command(aliases=[])
async def unblacklist(ctx, *tags):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	for tag in tags:
		if tag in user.blacklist:
			user.blacklist.remove(tag)
	message = "Alright, your blacklist doesn't have any of that in it anymore."

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.send(message)


@bot.command(aliases=[])
async def myBlacklist(ctx):

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return
	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)

	response = "Your blacklist is: " + \
		", ".join(data[guid]['users'][uid]['blacklist'])
	await ctx.channel.send(response)


@bot.command(aliases=['nick'])
async def nickname(ctx, name):

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)

	data[guid]['users'][uid]["name"] = name
	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)
	confirm = "Alright, I'll call you " + name + " from now on."
	await ctx.channel.send(confirm)


@bot.command(aliases=['mytags', 'myTags', 'taglist'])
async def checkTags(ctx):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	response = "Your tag list is: " + ", ".join(data[guid]['users'][uid]['tags'])
	await ctx.channel.send(response)


@bot.command(aliases=['ping', 'pingMe', 'pingme'])
async def setPing(ctx, state):

	ping = True
	if state in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'ping', '@'):
		ping = True
	elif state in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'mention'):
		ping = False
	else:
		await ctx.channel.send("Not sure what that means. Use +help setNotify for the list you can use.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	data[guid]['users'][uid]['notify'] = ping
	message = "Alright, ping for you are now set to " + str(ping)
	await ctx.channel.send(message)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)


@bot.command()
async def hideTags(ctx, state):
	hide = True
	if state in ('yes', 'y', 'true', 't', '1', 'enable', 'on', 'hide'):
		hide = True
	elif state in ('no', 'n', 'false', 'f', '0', 'disable', 'off', 'show'):
		hide = False
	else:
		await ctx.channel.send("Not sure what that means. Use +help hideTags for the list you can use.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	data[guid]['users'][uid]['specifyTags'] = not hide
	message = "Alright, hiding your tags is now set to " + str(not hide)
	await ctx.channel.send(message)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)


@bot.command(aliases=['pm', 'dm'])
async def slide(ctx):
	await ctx.author.send("You wanted something?")


@bot.command()
async def addCombo(ctx, *tags):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	user.tagCombos.append(tags)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send("Alright, I added your new combo list")


@bot.command()
async def myCombos(ctx):
	user, data = await processUser(ctx)
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


@bot.command()
async def deleteCombo(ctx, id: int):
	"""Removes the tag combination from your list of combos that has the given id"""
	realId = id - 1
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)

	message = ""
	if user.tagCombos[realId]:
		del user.tagCombos[realId]
		message = "Alright, that tag combo doesn't exist anymore for you."
	else:
		message = "Dude, you don't _have_ a tag combo with that id. Double check your id's with +myCombos"

	await ctx.channel.send(message)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

""" Using the brand new SauceNaoAPI that I wrote - Shephipster"""


def sauceNaoLookup(url):
	tags = TagAPI.getTagsByURL(url)
	return tags


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


async def ping_people(ctx, tag_list):
	"""	Takes a tag_list from an image and pings the people that it concerns.
		Pings use userID so it can't call by nickname
	"""
	pingTime = time.time()
	isPM = not ctx.guild

	loggedUsers = []

	if isPM:
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	guid = str(ctx.guild.id)

	for user in data[guid]['users']:
		tmpUser = User.User(user)
		tmpUser.setFromDict(user, data[guid]['users'][user])

		# #Uncomment after debugging
		# if type(ctx) == discord.message.Message:
		# 	if ctx.author.id == tmpUser.id:
		# 		continue
		# else:
		# 	if int(tmpUser.id) == ctx.message.author.id:
		# 		continue
  

		cleaned_tags = list(tag_list)
		for i in range(len(cleaned_tags)):
			cleaned_tags[i] = Tagger.getCleanTag(cleaned_tags[i])

		if all(bTag not in cleaned_tags for bTag in data[guid]['users'][user]['blacklist']):
			if (pingTime - tmpUser.lastPing < tmpUser.pingDelay):
				continue
			else:
				for tag in cleaned_tags:
					if tag in tmpUser.tags and tmpUser not in loggedUsers:
						data[guid]['users'][str(tmpUser.id)]['lastPing'] = pingTime
						loggedUsers.append(tmpUser)
					
				for combo in tmpUser.tagCombos:
					if all(combo_tag in cleaned_tags for combo_tag in combo):
						if tmpUser not in loggedUsers:
							data[guid]['users'][str(tmpUser.id)]['lastPing'] = pingTime
							loggedUsers.append(tmpUser)

		else:
			continue

	message = ""
	loopUser: User

	#Not going to be nearly as efficient, but at this point I don't care. Re-loop through everything to generate the message
	for loopUser in loggedUsers:
		if loopUser.notify:
			message += f"<@{loopUser.id}>"
			if loopUser.specifyTags:
				message += " for "
				for tag in cleaned_tags:
					if tag in loopUser.tags:
						message += f"`{tag}`, "
				for combo in tmpUser.tagCombos:
					if all(combo_tag in cleaned_tags for combo_tag in combo):
						message += f"`{combo}`, "
				message = message[:-2]
		else:
			message += f"{loopUser.name}"
			if loopUser.specifyTags:
				message += " for "
				for tag in cleaned_tags:
					if tag in loopUser.tags:
						message += f"`{tag}`, "
				for combo in tmpUser.tagCombos:
					if all(combo_tag in cleaned_tags for combo_tag in combo):
						message += f"`{combo}`, "
				message = message[:-2]

	if message != "":
		await ctx.channel.send(message)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)


@bot.command()
async def checkNotifications(ctx):
	""" Tells you if you'll be pinged for images or only get a small mention """
	user, data = await processUser(ctx)
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


@bot.command(aliases=['tags'])
async def getTagsFor(ctx):
	""" Gets the tags for a given image """
	if not ctx.message.attachments:
		await ctx.channel.send("You have to give me an image to look up you know.")
	else:
		for attachment in ctx.message.attachments:
			imageLink = attachment.url
			data = IQDB.getInfoUrl(imageLink)
			tag_list = data['tags']
			output = "The tag list for that image is: "
			for tag in tag_list:
				output = output + tag + ", "

			await ctx.channel.send(output[:-2])


@bot.command(aliases=['delay', 'setdelay', 'setDelay'])
async def changeDelay(ctx, delay):
	"""Sets how long to wait between pings. Takes how many seconds to wait before each ping."""

	if(delay == None):
		await ctx.channel.send("And how long am I supposed to wait exactly? The command is +changeDelay <seconds>")
		return
	if(int(delay) < 0):
		await ctx.channel.send("How am I supposed to wait for negative seconds? Just say 0 if you want no delay and use +toggleNotify if you don't want to be pinged.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)

	try:
		data[guid]['users'][uid]['pingDelay'] = int(delay)
		await ctx.channel.send("Okay, I'll wait at least " + delay + " seconds between each ping for you.")
		with open(guildsFile, "w") as dataFile:
			json.dump(data, dataFile, indent=4)
	except:
		await ctx.channel.send("I couldn't set your delay, do you even have a tag list? If not, make one first with +tagMe <tag>")


@bot.command()
async def roll(ctx, regex):
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


@bot.command(aliases=['randomPic', 'randomPicture', 'randomContent'])
async def randomPost(ctx, *tags):
	roll = True
	num_rolls = 0

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	cleaned_tags = []
	for tag in tags:
		cleaned_tags.append(tag.replace('`',''))

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

	while roll:
		roll = False

		randomDanSet = danSet(cleaned_tags)
		randomGelSet = gelSet(cleaned_tags)['post']
  
		danWeight = len(randomDanSet)
		gelWeight = len(randomGelSet)
		totalWeight = danWeight + gelWeight
		rolled_number = randint(0,totalWeight)
  
		if rolled_number <= danWeight:
			random_item = (randomDanSet[rolled_number], 'dan')
		elif rolled_number - danWeight <= gelWeight:
			random_item = (randomGelSet[rolled_number-danWeight], 'gel')
   
		if random_item[1] == 'dan':
			tag_list = random_item[0]['tag_string'].split()
			image_url = random_item[0]['file_url']
			isExplicit = random_item[0]['rating'] == 'e'
		elif random_item[1] == 'gel':
			tag_list = random_item[0]['tags'].split()
			image_url = random_item[0]['file_url']
			isExplicit = random_item[0]['rating'] == 'explicit'

		#Safety filter, if it's loli and explicit re-roll that junk
		for tag in tag_list:
			if tag in bannedTags:
				roll = True
				#print('skipped a post becase of', tag)
				break
			if isExplicit and tag in bannedPorn:
				roll = True
				#print('skipped a post because of', tag)
				break

		num_rolls += 1
		if num_rolls > ROLL_LIMIT:
			await ctx.channel.send(f"I couldn't find anything with {tags} in {ROLL_LIMIT} rolls. Better luck next time.")
			return

	if JOKE_MODE and isExplicit:
		poster = ctx.message.author.display_name
		await ctx.channel.send(f"{poster} just rolled porn!", tts=True)
  
	#send the initial embed, reverse search for urls will take time
	
	bot_avatar = bot.user.avatar_url
	bot_image = bot_avatar.BASE + bot_avatar._url

	if random_item[1] == 'gel' :
		post_id = random_item[0]['id']
		description = random_item[0]['source'] + f'\nhttps://gelbooru.com/index.php?page=post&s=view&id={ post_id }'
		image_url = random_item[0]['file_url']
	elif random_item[1] == 'dan':
		post_id = random_item[0]['id']
		description = random_item[0]['source'] + f'\nhttps://danbooru.donmai.us/posts/{post_id}'
		image_url = random_item[0]['file_url']
   
   
	embed_obj = discord.Embed(
  		colour=discord.Colour(0x5f4396),
		description=description,
		type="rich",
	)
	embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
	embed_obj.set_image(url=image_url)
 
	await ctx.channel.send("Alright, here's your random post. Don't blame me if it's cursed.")
	if isExplicit and not ctx.channel.is_nsfw():
		embed_msg = await ctx.channel.send("||" + image_url + "||")
	else:
		embed_msg = await ctx.channel.send(embed=embed_obj) 
 
	extra_data = IQDB.getInfoUrl(image_url)
	sources = []
	if extra_data != None:
		for url in extra_data['urls']:
			sources.append(url)
  
  
	if random_item[0]['source'] not in sources:
		sources.append(random_item[0]['source'])
  
	for i in range(len(sources)):
		if re.match('https?://', sources[i]) == None:
			sources[i] = "https://" + sources[i]
  
	description = '\n'.join(sources)
  
	#delete old embed and replace with new one that has more links
	await embed_msg.delete()
	embed_obj = discord.Embed(
  		colour=discord.Colour(0x5f4396),
		description=description,
		type="rich",
	)
	embed_obj.set_author(name="Kira Bot", icon_url=bot_image)
	embed_obj.set_image(url=image_url)
	if isExplicit and not ctx.channel.is_nsfw():
			embed_msg = await ctx.channel.send("||" + image_url + "||")
	else:
			embed_msg = await ctx.channel.send(embed=embed_obj) 
	
	await ping_people(ctx, tag_list)

	return


@bot.command(aliases=['randomPorn', 'randomExplicit'])
async def randomNSFW(ctx, *tags):
	await randomPost(ctx, 'rating:explicit', *tags)


@bot.command(aliases=['randomSFW', 'randomClean'])
async def randomSafe(ctx, *tags):
	await randomPost(ctx, 'rating:general', *tags)


@bot.command()
async def random(ctx, *inputs):
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


@bot.command(aliases=['deleteMessage', 'deletePost', 'deletepost', 'removePost', 'removepost'])
async def removeMessage(ctx, id):
	message = await ctx.channel.fetch_message(id)

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	guid = str(ctx.guild.id)

	if str(message.author.id) in data[guid]['purgableIds']:
		await message.delete()
	else:
		await ctx.channel.send(f"I'm not allowed to delete stuff {message.author.name} posts")
	return


@bot.command(aliases=['servers', 'guilds', 'myGuilds'])
async def myServers(ctx):

	uid = str(ctx.author.id)

	f = open(guildsFile)
	data = json.load(f)
	f.close()

	for guild in data:
		if uid in data[guild]['users'].keys():
			await ctx.channel.send(f"You are in {data[guild]['name']}, ID: {data[guild]['id']}")
	return


#-------------This is the portion to let them do stuff in DM's to alleviate chat spam----------------------------------#

@bot.command()
async def addTagsByServer(ctx, guid, *tags):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Alright, I added {tags} to your tags for {data[guid]['name']}.")
	return


@bot.command()
async def removeTagsByServer(ctx, guid, *tags):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Alright, I removed {tags} to your tags for {data[guid]['name']}.")
	return


@bot.command()
async def addComboByServer(ctx, guid, *tags):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send("Alright, I added your new combo list")
	return

#TODO: THIS ISN'T USING TAGS


@bot.command()
async def removeComboByServer(ctx, guid, *tags):
	user, data = await processUser(ctx, guid)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)

	if guid not in data.keys():
		await ctx.channel.send(f"I don't know of any servers with the ID {guid}.\nUse `+myServers` to get a list of your servers and their ID")
		return
	else:
		realId = id - 1
		message = ""
		if user.tagCombos[realId]:
			del user.tagCombos[realId]
			message = "Alright, that tag combo doesn't exist anymore for you."
		else:
			message = "Dude, you don't _have_ a tag combo with that id. Double check your id's with +myCombos"

	await ctx.channel.send(message)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)
	return


@bot.command()
async def addBlacklistByServer(ctx, guid, *tags):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Alright, I added {tags} to your blacklist for {data[guid]['name']}")
	return


@bot.command()
async def removeBlacklistByServer(ctx, guid, *tags):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Alright, I removed {tags} from your blacklist for {data[guid]['name']} ")
	return


@bot.command()
async def setNicknameByServer(ctx, guid, nick):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Alright, I'll call you {nick} in {data[guid]['name']} from now on")
	return


@bot.command()
async def setPingByServer(ctx, guid, state):
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

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)


@bot.command()
async def setDelayByServer(ctx, guid, delay):
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
		with open(guildsFile, "w") as dataFile:
			json.dump(data, dataFile, indent=4)
	except:
		await ctx.channel.send("I couldn't set your delay, do you even have a tag list? If not, make one first with +tagMe <tag>")

#view information - Just send it as a big message


@bot.command(aliases=['info', 'myStuff'])
async def myInfo(ctx, guid=None):
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


@bot.command()
async def poll(ctx, *options):
	message = "Cast your vote using the reactions below!"
	optionCount = 1
	pollMap = dict()
	if len(options) > POLL_LIMIT:
		await ctx.channel.send(f"I can only do a poll with up to {POLL_LIMIT} options")
		return
	for option in options:
		message += "\n" + getNumericEmoji(optionCount) + " " + option
		optionCount += 1
	msg = await ctx.channel.send(message)

	#Generate reactions
	optionCount = 1
	for option in options:
		reaction = getNumericReaction(optionCount)
		await msg.add_reaction(reaction)
		pollMap[reaction] = option
		optionCount += 1
	return msg, pollMap


@bot.command(aliases=['timedpoll', 'timepoll', 'limitpoll', 'limitedpoll'])
async def timedPoll(ctx, seconds, *options):

	try:
		int(seconds)
	except:
		await ctx.channel.send("You need to give me the time first then your options")
		return

	results = dict()
	msg: discord.Message
	msg, pollMap = await poll(ctx, *options)
	time.sleep(int(seconds))
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
		message += getNumericEmoji(ranking) + " "
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


async def processUser(ctx, guid=-1):
	#If this is in DM's, there is no guild with an id
	if not ctx.guild:
		if guid == -1:
			await ctx.channel.send("I'm having trouble knowing what guild you want.\nEither try that again in the guild you want to update stuff for or give me the guild ID")
			return None, None
	else:
		guid = str(ctx.guild.id)

	uid = str(ctx.author.id)

	f = open(guildsFile)
	guilds = json.load(f)
	f.close()

	user = User.User(ctx.author.id)

	if uid not in guilds[guid]['users']:
		guilds[guid]['users'][uid] = user.__dict__

	user.setFromDict(uid, guilds[guid]['users'][uid])
	return user, guilds


#===============================Power commands=================================#
def userCanUsePowerCommand(guild: Guild, member: discord.Member):
	userId = int(member.id)
	if userId in guild['powerUsers']:
		return True
	for role in member.roles:
		if role in guild['powerRoles']:
			return True
	return False


async def invokePowerCommand(ctx: commands.context, command, *params):
	user: User
	guild: Guild
	user, guilds = await processUser(ctx)
	guild = guilds[f'{ctx.guild.id}']

	if user == None or guild == None:
		#there was some sort of issue
		return
	if not userCanUsePowerCommand(guild, ctx.author):
		await ctx.channel.send(f"You don't have permission to use this command!")
		return

	await command(ctx, guilds, f'{ctx.guild.id}', *params)


@bot.command(aliases=['empower', 'promote'])
async def addPowerUser(ctx: commands.context, userId):
	await invokePowerCommand(ctx, addPowerUserCommand, int(userId))


async def addPowerUserCommand(ctx, guilds, guid, userToAdd):
	if userToAdd not in guilds[guid]['powerUsers']:
		guilds[guid]['powerUsers'].append(userToAdd)
		with open(guildsFile, 'w') as dataFile:
			json.dump(guilds, dataFile, indent=4)


@bot.command(aliases=['demote', 'fell'])
async def removePowerUser(ctx: commands.context, userId):
	await invokePowerCommand(ctx, removePowerUserCommand, int(userId))


async def removePowerUserCommand(ctx, guilds, guid, userToAdd):
	if userToAdd in guilds[guid]['powerUsers']:
		guilds[guid]['powerUsers'].remove(userToAdd)
		with open(guildsFile, 'w') as dataFile:
			json.dump(guilds, dataFile, indent=4)


@bot.command(aliases=['empowerRole', 'promoteRole'])
async def addPowerRole(ctx: commands.context, role):
	await invokePowerCommand(ctx, addPowerRoleCommand, role)


async def addPowerRoleCommand(ctx, guilds, guid, role):
	#print(role)
	if role not in guilds[guid]['powerRoles']:
		guilds[guid]['powerRoles'].append(role)
		with open(guildsFile, 'w') as dataFile:
			json.dump(guilds, dataFile, indent=4)


@bot.command(aliases=['demoteRole', 'fellRole'])
async def removePowerRole(ctx: commands.context, role):
	await invokePowerCommand(ctx, removePowerUserCommand, role)


async def removePowerRoleCommand(ctx, guilds, guid, role):
	if role in guilds[guid]['powerRoles']:
		guilds[guid]['powerRoles'].remove(role)
		with open(guildsFile, 'w') as dataFile:
			json.dump(guilds, dataFile, indent=4)


@bot.command(aliases=['unblockPornTag', 'unbanPornTag', 'permitPornTag'])
async def removeBannedExplicitTags(ctx: commands.context, *tags):
	await invokePowerCommand(ctx, removeBannedExplicitTagsCommand, *tags)


async def removeBannedExplicitTagsCommand(ctx, guilds, guid, *tags):
	for tag in tags:
		if tag in guilds[guid]['bannedExplicitTags']:
			guilds[guid]['bannedExplicitTags'].remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I can now roll explicit stuff with any of the following: {tags}")


@bot.command(aliases=['banExplicitTag', 'blockExplicitTag', 'blockPornTag', 'banPornTag'])
async def addBannedExplicitTags(ctx: commands.context, *tags):
	await invokePowerCommand(ctx, addBannedExplicitTagsCommand, *tags)


async def addBannedExplicitTagsCommand(ctx, guilds, guid, *tags):
	for tag in tags:
		if tag not in guilds[guid]['bannedExplicitTags']:
			guilds[guid]['bannedExplicitTags'].append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I'll now no longer roll explicit stuff with any of the following: {tags}")


@bot.command(aliases=['canDelete', 'canRemove', 'canPurge'])
async def addPurgablePoster(ctx: commands.context, id):
	await invokePowerCommand(ctx, addPowerUserCommand, id)


async def addPurgablePosterCommand(ctx, guilds, guid, id):
	if id in guilds[guid]['purgableIds']:
		await ctx.channel.send("I'm already allowed to delete their posts.")
	else:
		guilds[guid]['purgableIds'].append(id)
		member = await ctx.guild.fetch_member(id)
		with open(guildsFile, "w") as dataFile:
			json.dump(guilds, dataFile, indent=4)
		await ctx.channel.send(f"Okay, I can now delete {member.name}'s posts.")


@bot.command(aliases=['cantDelete', 'cantRemove', 'cantPurge'])
async def removePurgablePoster(ctx: commands.context, id):
	await invokePowerCommand(ctx, removePurgablePosterCommand, id)


async def removePurgablePosterCommand(ctx, guilds, guid, id):
	if id not in guilds[guid]['purgableIds']:
		await ctx.channel.send("I'm already not allowed to delete their posts.")
	else:
		guilds[guid]['purgableIds'].remove(id)
		member = await ctx.guild.fetch_member(id)
		with open(guildsFile, "w") as dataFile:
			json.dump(guilds, dataFile, indent=4)
		await ctx.channel.send(f"Okay, I can no longer delete {member.name}'s posts.")


@bot.command(aliases=['banTag', 'blockTag'])
async def addBannedGeneralTags(ctx: commands.context, *tags):
	await invokePowerCommand(ctx, addBannedGeneralTagsCommand, *tags)


async def addBannedGeneralTagsCommand(ctx, guilds, guid, *tags):
	for tag in tags:
		if tag not in guilds[guid]['bannedGeneralTags']:
			guilds[guid]['bannedGeneralTags'].append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I'll now no longer roll stuff with any of the following: {tags}")


@bot.command(aliases=['unblockTag', 'unbanTag'])
async def removeBannedGeneralTags(ctx: commands.context, *tags):
	await invokePowerCommand(ctx, removeBannedGeneralTagsCommand, *tags)


async def removeBannedGeneralTagsCommand(ctx, guilds, guid, *tags):
	for tag in tags:
		if tag in guilds[guid]['bannedGeneralTags']:
			guilds[guid]['bannedGeneralTags'].remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I can now roll stuff with any of the following: {tags}")

#Update command


@bot.command(aliases=['update'])
async def updateGuild(ctx):
	f = open(guildsFile)
	data = json.load(f)
	f.close()

	await updateGuildCommand(ctx.guild.id, data)


async def updateAllGuilds():
	for guild in bot.guilds:
		await updateGuildCommand(guild)


async def updateGuildCommand(guild):

	f = open(guildsFile)
	data = json.load(f)
	f.close()

	guid = f'{guild.id}'
	#for role in guild.roles:
		#print(role)

	tempGuild = Guild.Guild(guild)
	if guid in data.keys():
		tempGuild.setFromDict(data[guid])
	data[guid] = tempGuild

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

#============================Channel-specific commands============================#


@bot.command(aliases=['banChannelTag'])
async def banTagFromChannel(ctx, *tags):
	await invokePowerCommand(ctx, banTagsFromChannelCommand, *tags)


async def banTagsFromChannelCommand(ctx, guilds, guid, *tags):
	channel = ctx.channel
	cid = str(channel.id)
	for tag in tags:
		if tag not in guilds[guid]['channels'][cid]['bannedTags']:
			guilds[guid]['channels'][cid]['bannedTags'].append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, won't roll stuff in <#{channel.id}> that has {tags}")


@bot.command(aliases=['unbanChannelTag', 'allowChannelTag'])
async def unbanTagFromChannel(ctx, *tags):
	await invokePowerCommand(ctx, unbanTagsFromChannelCommand, *tags)


async def unbanTagsFromChannelCommand(ctx, guilds, guid, *tags):
	channel = ctx.channel
	cid = str(channel.id)
	for tag in tags:
		if tag in guilds[guid]['channels'][cid]['bannedTags']:
			guilds[guid]['channels'][cid]['bannedTags'].remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I can roll stuff in <#{channel.id}> that has {tags} now")


@bot.command(aliases=['banChannelPornTag'])
async def banNSFWTagFromChannel(ctx, *tags):
	await invokePowerCommand(ctx, banNSFWTagsFromChannelCommand, *tags)


async def banNSFWTagsFromChannelCommand(ctx, guilds, guid, *tags):
	channel = ctx.channel
	cid = str(channel.id)
	for tag in tags:
		if tag not in guilds[guid]['channels'][cid]['bannedNSFWTags']:
			guilds[guid]['channels'][cid]['bannedNSFWTags'].append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, won't roll stuff in <#{channel.id}> that's porn and has {tags}")


@bot.command(aliases=['unbanChannelNSFWTag', 'allowChannelNSFWTag', 'unbanChannelPornTag', 'allowChannelPornTag'])
async def unbanNSFWTagFromChannel(ctx, *tags):
	await invokePowerCommand(ctx, unbanNSFWTagsFromChannelCommand, *tags)


async def unbanNSFWTagsFromChannelCommand(ctx, guilds, guid, *tags):
	channel = ctx.channel
	cid = str(channel.id)
	for tag in tags:
		if tag in guilds[guid]['channels'][cid]['bannedNSFWTags']:
			guilds[guid]['channels'][cid]['bannedNSFWTags'].remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(guilds, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I can roll stuff in <#{channel.id}> that's porn and has {tags} now")


# @bot.command()
# async def multiEmbedTest(ctx):
#     #seems like only webhooks allow for multiple embeds in one message, and that's the trick to multiple images
#     #in a single embed best I can figure
# 	bot_avatar = bot.user.avatar_url
# 	bot_image = bot_avatar.BASE + bot_avatar._url
 
# 	payload = {
# 		"username": "Kira Bot",
# 		"avatar_url": bot_image,
# 	}
 
# 	bot_avatar = bot.user.avatar_url
# 	bot_image = bot_avatar.BASE + bot_avatar._url

# 	payload['embeds'] = [
# 			{
# 				# 'url':'shephipster.ddns.net',
# 				'image':{
#         			'url':'https://www.pixiv.net/en/artworks/56829205',
# 				},
# 				'title': "TEST",
# 				'description':'Test of multiple embeds via webhooks',
# 				'color':0x5f4396,
# 			},
# 			{
# 				# 'url':'shephipster.ddns.net',
# 				'image':{
#         			'url': 'https://www.pixiv.net/en/artworks/56556538'
# 				},
# 			}
# 		]

# 	res = requests.post(webhook, json=payload)
# 	print(res)

bot.run(TOKEN)
