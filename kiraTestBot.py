import discord
import requests
import json
import time
import imagehash
import os
import re

from random import choice, choices, randint
from dotenv import load_dotenv
from Services.GelbooruService import getRandomPostWithTags
from Utilities.Tagger import Tagger
import Services.IQDBService as IQDB

import Utilities.TagAPI as TagAPI
from Entities import User, Post, Guild
from discord.ext import commands
from PIL import Image
from scipy.spatial import distance

load_dotenv()

#TOKEN = os.getenv('DISCORD_TOKEN')
#DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')

# This is used for debugging
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

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guild_messages = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='+',
                   description=description, intents=intents)

testImage = 'https://cdn.discordapp.com/attachments/772128575213666309/772181178068762634/nfsuiefmiesfbosdtgd.png'
logFile = './kiraBotFiles/imageLog.json'
guildsFile = './kiraBotFiles/guilds.json'

pic_ext = ['.jpg', '.png', '.gif', '.jpeg', '.bmp']
ROLL_LIMIT = 10


@bot.event
async def on_ready():
	initFiles()
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

	if message.content[0] != '+':
		if message.attachments:
			for attachment in message.attachments:
				print("Attachment:", attachment)
				imageLink = attachment.url
				data = IQDB.getInfoUrl(imageLink)
				tag_list = data['tags']
				await ping_people(message, tag_list)
				if repostDetected(message.channel.guild, imageLink):
					await message.add_reaction(str('♻️'))
		elif message.embeds:
			for embed in message.embeds:
				print("Embed:", embed)
				imageLink = embed.url
				data = IQDB.getInfoUrl(imageLink)
				tag_list = data['tags']
				await ping_people(message, tag_list)
				if repostDetected(message.channel.guild, imageLink):
					await message.add_reaction(str('♻️'))
	await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
	print(error)
	return


@bot.command(aliases=['init'])
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
	data = json.load(f)
	f.close()

	user = User.User(ctx.author.id)

	if uid not in data[guid]['users']:
		data[guid]['users'][uid] = user.__dict__

	user.setFromDict(uid, data[guid]['users'][uid])
	return user, data


@bot.command(aliases=['tagme', 'addTag', 'addtag'])
async def tagMe(ctx, *tags):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	for tag in tags:
		if tag not in user.tags:
			user.tags.append(tag)

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
		if type(ctx) == discord.message.Message:
			if ctx.author.id == tmpUser.id:
				continue
		else:
			if int(tmpUser.id) == ctx.message.author.id:
				continue

		if all(bTag not in tag_list for bTag in data[guid]['users'][user]['blacklist']):
			if (pingTime - tmpUser.lastPing < tmpUser.pingDelay):
				continue
			else:
				for tag in tag_list:
					realTag = Tagger.getCleanTag(tag)
					if realTag in tmpUser.tags and tmpUser not in loggedUsers:
						data[guid]['users'][tmpUser.id]['lastPing'] = pingTime
						loggedUsers.append(tmpUser)
					# else:
						# for combo in tmpUser.tagCombos:
						# 	if all(Tagger.getCleanTag(tags) in tag_list for tags in combo) and tmpUser not in loggedUsers:
						# 		data[guid]['users'][tmpUser.id]['lastPing'] = pingTime
						# 		loggedUsers.append(tmpUser)
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
				for tag in tag_list:
					if tag in loopUser.tags:
						message += f"`{Tagger.getCleanTag(tag)}`, "
				# for combo in tmpUser.tagCombos:
				# 	if all(Tagger.getCleanTag(tags) in tag_list for tags in combo):
				# 		message += f"`{combo}`, "
				# message = message[:-2]
		else:
			message += f"{loopUser.name}"
			if loopUser.specifyTags:
				message += " for "
				for tag in tag_list:
					if tag in loopUser.tags:
						message += f"`{Tagger.getCleanTag(tag)}`, "
				# for combo in tmpUser.tagCombos:
				# 	if all(Tagger.getCleanTag(tags) in tag_list for tags in combo):
				# 		message += f"`{combo}`, "
				# message = message[:-2]

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

	guid = str(ctx.guild.id)

	while roll:
		roll = False

		#Get the random post and all it's data.
		post = getRandomPostWithTags(tags)
		if post == None:
			await ctx.channel.send(f"Couldn't find anything, one or more of your tags might just not exist.")
			return
		#We already have the tags, get them and then ping people

		tag_list = post['tags'].split()
		image = post['file_url']
		isExplicit = post['rating'] == 'explicit'

		#Safety filter, if it's loli and explicit re-roll that junk
		if isExplicit:
			for tag in tag_list:
				if tag in data[guid]['bannedExplicitTags']:
					roll = True
					break
		for tag in tag_list:
			if tag in data[guid]['bannedGeneralTags']:
				roll = True
				break

		num_rolls += 1
		if num_rolls > ROLL_LIMIT:
			await ctx.channel.send(f"I couldn't find anything with {tags} in {ROLL_LIMIT} rolls. Better luck next time.")
			return

	if JOKE_MODE and isExplicit:
		poster = ctx.message.author.display_name
		await ctx.channel.send(f"{poster} just rolled porn!", tts=True)

	await ctx.channel.send("Alright, here's your random post. Don't blame me if it's cursed.")
	if isExplicit and not ctx.channel.is_nsfw():
		await ctx.channel.send("|| " + image + " ||")
	else:
		await ctx.channel.send(image)

	#Double pings are occuring, might need investigation
	await ping_people(ctx, tag_list)

	return


@bot.command(aliases=['randomPorn', 'randomExplicit'])
async def randomNSFW(ctx, *tags):
	await randomPost(ctx, 'rating:explicit', *tags)


@bot.command(aliases=['randomSFW', 'randomClean'])
async def randomSafe(ctx, *tags):
	await randomPost(ctx, 'rating:safe', *tags)


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


@bot.command(aliases=['canDelete', 'canRemove', 'canPurge'])
async def addPurgablePoster(ctx, id):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)

	#Can author use this command?
	if ctx.author.id != ctx.guild.owner_id:
		await ctx.channel.send(f"You're not the boss around here, only {ctx.guild.owner} can use this command.")
		return

	user, data = await processUser(ctx)
	if id in data[guid]['purgableIds']:
		await ctx.channel.send("I'm already allowed to delete their posts.")
	else:
		data[guid]['purgableIds'].append(id)
		member = await ctx.guild.fetch_member(id)
		with open(guildsFile, "w") as dataFile:
			json.dump(data, dataFile, indent=4)
		await ctx.channel.send(f"Okay, I can now delete {member.name}'s posts.")


@bot.command(aliases=['cantDelete', 'cantRemove', 'cantPurge'])
async def removePurgablePoster(ctx, id):
	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)

	#Can author use this command?
	if ctx.author.id != ctx.guild.owner_id:
		await ctx.channel.send(f"You're not the boss around here, only {ctx.guild.owner} can use this command.")
		return

	user, data = await processUser(ctx)
	if id not in data[guid]['purgableIds']:
		await ctx.channel.send("I'm already not allowed to delete their posts.")
	else:
		data[guid]['purgableIds'].remove(id)
		member = await ctx.guild.fetch_member(id)
		with open(guildsFile, "w") as dataFile:
			json.dump(data, dataFile, indent=4)
		await ctx.channel.send(f"Okay, I can no longer delete {member.name}'s posts.")


@bot.command(aliases=['banTag', 'blockTag'])
async def addBannedGeneralTags(ctx, *tags):
	if ctx.author.id != ctx.guild.owner_id:
		await ctx.channel.send(f"You're not the boss around here, only {ctx.guild.owner} can use this command.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	for tag in tags:
		if tag not in data[guid]['bannedGeneralTags']:
			data[guid]['bannedGeneralTags'].append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I'll now no longer roll stuff with any of the following: {tags}")


@bot.command(aliases=['banExplicitTag', 'blockExplicitTag', 'blockPornTag', 'banPornTag'])
async def addBannedExplicitTags(ctx, *tags):
	if ctx.author.id != ctx.guild.owner_id:
		await ctx.channel.send(f"You're not the boss around here, only {ctx.guild.owner} can use this command.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	for tag in tags:
		if tag not in data[guid]['bannedExplicitTags']:
			data[guid]['bannedExplicitTags'].append(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I'll now no longer roll explicit stuff with any of the following: {tags}")


@bot.command(aliases=['unbanExplicitTag', 'unblockExplicitTag', 'unblockPornTag', 'unbanPornTag'])
async def removeBannedGeneralTags(ctx, *tags):
	if ctx.author.id != ctx.guild.owner_id:
		await ctx.channel.send(f"You're not the boss around here, only {ctx.guild.owner} can use this command.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	for tag in tags:
		if tag in data[guid]['bannedGeneralTags']:
			data[guid]['bannedGeneralTags'].remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I can now roll stuff with any of the following: {tags}")


@bot.command(aliases=['unblockTag', 'unbanTag'])
async def removeBannedExplicitTags(ctx, *tags):
	if ctx.author.id != ctx.guild.owner_id:
		await ctx.channel.send(f"You're not the boss around here, only {ctx.guild.owner} can use this command.")
		return

	user, data = await processUser(ctx)
	if user == None or data == None:
		#there was an issue, break
		return

	uid = str(ctx.author.id)
	guid = str(ctx.guild.id)
	for tag in tags:
		if tag in data[guid]['bannedExplicitTags']:
			data[guid]['bannedExplicitTags'].remove(tag)

	with open(guildsFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.channel.send(f"Okay, I can now roll explicit stuff with any of the following: {tags}")


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


bot.run(TOKEN)
