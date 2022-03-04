import discord
import requests
import json
import time
import imagehash
import os
import re
from random import choice, choices, randint
from dotenv import load_dotenv

import TagAPI
from User import User
from Post import Post


from discord.ext import commands
from PIL import Image
from scipy.spatial import distance

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')

description = ''' Kira bot. Pings users for images that have tags they like. '''
#Consts
#debug = True;	#if debug statements should be printed
debug = False;	#Too tired of deleting true or false, just comment out if you want debug
postTTL = -1;	#how long a post should be recorded before it is up for deletion. -1 for no time
logSizeLimit = 255;	#number of images to record for repost detection, -1 for no limit (CAREFUL OF THIS)
repostDistance = 10; #how similar an image must be to be a repost. Smaller means more similar, account for Discord compression

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guild_messages = True
intents.dm_messages = True
bot = commands.Bot(command_prefix = '+', description=description, intents=intents)

testImage = 'https://cdn.discordapp.com/attachments/772128575213666309/772181178068762634/nfsuiefmiesfbosdtgd.png'
tagFile = './kiraBotFiles/users.json'
logFile = './kiraBotFiles/imageLog.json'

pic_ext = ['.jpg', '.png', '.gif', '.jpeg', '.bmp']

@bot.event
async def on_ready():
	initFiles()
	print('Running')


def initFiles():
	if not os.path.exists(logFile):
		with open(logFile, 'a') as file:
			file.write("{\n}")

	if not os.path.exists(tagFile):
		with open(tagFile, 'a') as file:
			file.write("{\n}")


@bot.event
async def on_message(message):
	channel = message.channel
	if debug: print("Guild:" , message.channel.guild)
	if message.author == bot.user:
		return
	if "fuck you" in message.content.lower():
		if "kira" in message.content.lower():
			await channel.send("fuck me yourself, coward")
		else:
			await channel.send("fuck them yourself, coward")
	elif "fuck me" in message.content.lower():
		await channel.send("that's kinda gross dude")
	if message.attachments and ( len(message.content) == 0  or message.content[0] != '+'):
			for attachment in message.attachments:
				imageLink =  attachment.url
				tag_list = sauceNaoLookup(imageLink)
				await ping_people(message, tag_list)
				if repostDetected(message.channel.guild, imageLink):
					await message.add_reaction(str('♻️'))
	await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
	print(error)
	return

@bot.command()
async def myId(ctx, *args):
	await ctx.send(ctx.author.id)
	print(ctx.author.id)
	return

@bot.command()
async def tagMe(ctx, *tags):
	""" 	Adds the given tag to the users list of tags to be notified for.
		<arg> is the name of any Danbooru tag you wished to be notified about.
		If you do not have a tag list then one will be created for you.
		Use this to make a tag list for yourself should you not have one.
	 """
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)

	if uid not in data.keys():
		#new user, add them with default values
		data[uid] = user.__dict__

	
	user.setFromDict(uid, data[uid])
	for tag in tags:
		if tag not in user.tags:
			user.tags.append(tag)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.send("Alright, I added your tags for you.")
	

@bot.command()
async def untagMe(ctx, *tags):
	""" 	Removes the tag from the users list of tags to be notified for.
		<arg> is the tag you want removed from your list.
		If you do not have a list nothing will happen.
	 """
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)
	message = ""

	if uid not in data.keys():
		data[uid] = user.__dict__
		message = "You don't even have tags yet dude. I added you to the tag list, but you gotta fill it up first."
	else:	
		user.setFromDict(uid, data[uid])
		for tag in tags:
			if tag in user.tags:
				user.tags.remove(tag)
		message = "Alright, your tag list doesn't have any of that in it anymore."

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.send(message)

@bot.command()
async def blacklist(ctx, *tags):
	"""
		Adds tags to your blacklist. If these tags are contained in the image you will NOT be notified, even if
		the image has tags you want to be pinged for
	"""
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)

	if uid not in data.keys():
		#new user, add them with default values
		data[uid] = user.__dict__

	
	user.setFromDict(uid, data[uid])
	for tag in tags:
		if tag not in user.blacklist:
			user.blacklist.append(tag)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.send("Alright, I update your blacklist for you.")

@bot.command()
async def unblacklist(ctx, *tags):
	""" 	
		Removes the tags from your blacklist, allowing you to be notified
		on images that contain the tag again. This does NOT mean you will
		be alerted if the tag is in an image, you need to update your
		tags using tagMe for that
	 """
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)
	message = ""

	if uid not in data.keys():
		data[uid] = user.__dict__
		message = "You don't even have tags yet dude. I added you to the tag list, but you gotta fill it up first."
	else:	
		user.setFromDict(uid, data[uid])
		for tag in tags:
			if tag in user.blacklist:
				user.blacklist.remove(tag)
		message = "Alright, your blacklist doesn't have any of that in it anymore."

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.send(message)

@bot.command()
async def myBlacklist(ctx):
	f = open(tagFile)
	data = json.load(f)
	f.close()
	uid = str(ctx.author.id)
	response = "Your blacklist is: "+ ", ".join(data[uid]['blacklist'])
	await ctx.author.send(response)

@bot.command()
async def nickname(ctx, name):
	"""	Ask the bot to call you by a different name.
		<name> is your new nickname.
	"""
	f = open(tagFile)
	data = json.load(f)
	f.close()
	if str(ctx.author.id) not in data:
		return
	data[str(ctx.author.id)]['name'] = name
	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)
	confirm = "Alright, I'll call you " + name + " from now on."
	await ctx.send(confirm)

@bot.command()
async def checkTags(ctx):
	""" Prints out the tags currently assigned to the user """
	f = open(tagFile)
	data = json.load(f)
	f.close()
	uid = str(ctx.author.id)
	response = "Your tag list is: "+ ", ".join(data[uid]['tags'])
	await ctx.author.send(response)

@bot.command()
async def myTags(ctx):
	await checkTags(ctx)

@bot.command()
async def setPing(ctx, state):
	"""Set if you want to be pinged or not.
	Options to be pinged are yes, y, true, t, 1, enable, on, ping @
	Options to not be pinged are no, n, false, f, 0, disable, off, mention"""
	ping = True
	if state in ('yes','y','true','t','1','enable','on','ping','@'):
		ping = True
	elif state in ('no','n','false''f','0','disable','off','mention'):
		ping = False
	else:
		await ctx.author.send("Not sure what that means. Use +help setNotify for the list you can use.")
		return

	f = open(tagFile)
	data = json.load(f)
	uid = str(ctx.author.id)
	data[uid]['notify'] = ping
	message = "Alright, ping for you are now set to " + str(ping)
	await ctx.author.send(message)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent = 4)

@bot.command()
async def hideTags(ctx, state):
	"""
		When you are getting pinged for an image, this is used to decide
		if the tags you're getting pinged for are told to the server or not.
		This is false by default, meaning tags are shown
		Options to hide tags are yes, y, true, t, 1, enable, on, hide
		Options to show tags are no, n, false, f, 0, disable, off, show
	"""
	hide = True
	if state in ('yes','y','true','t','1','enable','on','hide'):
		hide = True
	elif state in ('no','n','false''f','0','disable','off','show'):
		hide = False
	else:
		await ctx.author.send("Not sure what that means. Use +help hideTags for the list you can use.")
		return

	f = open(tagFile)
	data = json.load(f)
	uid = str(ctx.author.id)
	data[uid]['specifyTags'] = not hide
	message = "Alright, hiding your tags is now set to " + str(not hide)
	await ctx.author.send(message)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent = 4)

""" This code pretty much entirely from ImagineNotHavingAnAlt, bless their soul """

@bot.command()
async def slide(ctx):
	""" Starts a PM with Kira, keeps commands hidden, avoids spam. """
	await ctx.author.send("You wanted something?")

@bot.command()
async def addCombo(ctx, *tags):
	"""Adds all the given tags to a specific combo, meaning all of them must be in an image to be pinged for it"""
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)

	if uid not in data.keys():
		#new user, add them with default values
		data[uid] = user.__dict__

	
	user.setFromDict(uid, data[uid])
	user.tagCombos.append(tags)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

	await ctx.send("Alright, I added your new combo list")

@bot.command()
async def myCombos(ctx):
	"""Prints out all your combos along with their id. You need their id to delete them, so this helps you identify them"""
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)
	if uid not in data.keys():
			#new user, add them with default values
			data[uid] = user.__dict__		
	user.setFromDict(uid, data[uid])

	message = ""
	id = 1
	for combo in user.tagCombos:
		message += f"{id} {combo}\n"
		id += 1

	if message == "":
		message = "You don't have any combos right now dude. Use addCombo <tags> to add at least one."
	await ctx.send(message)

@bot.command()
async def deleteCombo(ctx, id: int):
	"""Removes the tag combination from your list of combos that has the given id"""
	realId = id - 1
	uid = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	user = User(ctx.author.id)
	if uid not in data.keys():
			#new user, add them with default values
			data[uid] = user.__dict__		
	user.setFromDict(uid, data[uid])

	message = ""
	if user.tagCombos[realId]:
		del user.tagCombos[realId]
		message = "Alright, that tag combo doesn't exist anymore for you."
	else:
		message = "Dude, you don't _have_ a tag combo with that id. Double check your id's with +myCombos"

	await ctx.send(message)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)

""" Using the brand new SauceNaoAPI that I wrote - Shephipster"""
def sauceNaoLookup(url):
	tags = TagAPI.getTagsByURL(url)
	return tags


#This code does work, and it works well. However, with the new sauceNaoApi it's not
#really needed anymore. We're leaving it in though because of its influence.
#Also, if there's any 'heavy' searching (5 in 30s and 300 in 24h) the SN API will
#lock out, so we might have to resort to calling this one if that happens

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
	f = open(tagFile)
	data = json.load(f)
	f.close()
	pingTime = time.time()
	isPM = not ctx.guild

	loggedUsers = []

	for user in data:
		tmpUser = User(user)
		tmpUser.setFromDict(user, data[user])
		for tag in tag_list:
			if not isPM  and (user in [str(member.id) for member in ctx.guild.members]):
				if tag not in data[user]['blacklist'] and (pingTime - tmpUser.lastPing > tmpUser.pingDelay):
						if tag in tmpUser.tags:		
							data[tmpUser.id]['lastPing'] = pingTime
							loggedUsers.append(tmpUser)
						else:
							for combo in tmpUser.tagCombos:
								if all(tags in tag_list for tags in combo):
									data[tmpUser.id]['lastPing'] = pingTime
									loggedUsers.append(tmpUser)
	
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
						message += f"`{tag}`, "
				for combo in tmpUser.tagCombos:
					if all(tags in tag_list for tags in combo):
						message += f"`{combo}, "
				message = message[:-2]
		else:
			message += f"{loopUser.name}"
			if loopUser.specifyTags:
				message += " for "
				for tag in tag_list:
					if tag in loopUser.tags:
						message += f"`{tag}`, "
				for combo in tmpUser.tagCombos:
					if all(tags in tag_list for tags in combo):
						message += f"`{combo}``, "
				message = message[:-2]

	if message != "":
		await ctx.channel.send(message)

	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent = 4)

@bot.command()
async def checkNotifications(ctx):
	""" Tells you if you'll be pinged for images or only get a small mention """
	f = open(tagFile)
	data = json.load(f)
	f.close()
	userName = ctx.author.name
	try:
		if data[str(ctx.author.id)]['notify']:
			await ctx.send(f"{userName}, you will get pinged for images with your tags.")
			return
		await ctx.send(f"{userName}, you will not be pinged for images with your tags.")
	except:
		await ctx.send(f"{userName}, you don't have a tag list yet. Use +tagMe <tag> to start one!")


@bot.command()
async def getTagsFor(ctx):
	""" Gets the tags for a given image """
	if not ctx.message.attachments:
		await ctx.channel.send("You have to give me an image to look up you know.")
	else:
		for attachment in ctx.message.attachments:
			imageLink = attachment.url
			tag_list = sauceNaoLookup(imageLink)
			output = "The tag list for that image is: "
			for tag in tag_list:
				output = output + tag + ", "

			await ctx.channel.send(output[:-2])

@bot.command()
async def changeDelay(ctx, delay):
	"""Sets how long to wait between pings. Takes how many seconds to wait before each ping."""

	if(delay == None):
		await ctx.channel.send("And how long am I supposed to wait exactly? The command is +changeDelay <seconds>")
		return
	if(int(delay) < 0):
		await ctx.channel.send("How am I supposed to wait for negative seconds? Just say 0 if you want no delay and use +toggleNotify if you don't want to be pinged.")
		return

	f = open(tagFile)
	data = json.load(f)
	f.close()

	try:
		data[str(ctx.author.id)]['pingDelay'] = int(delay)
		await ctx.channel.send("Okay, I'll wait at least " + delay + " seconds between each ping for you.")
		with open(tagFile, "w") as dataFile:
			json.dump(data, dataFile, indent = 4)
	except:
		await ctx.channel.send("I couldn't set your delay, do you even have a tag list? If not, make one first with +tagMe <tag>")

@bot.command()
async def setDelay(ctx, delay):
	await changeDelay(ctx, delay)

@bot.command()
async def roll(ctx, regex):
	numRollsGroup = re.search("\d+d",regex)
	diceSizeGroup = re.search("d\d+",regex)
	if not numRollsGroup or not diceSizeGroup:
		await ctx.channel.send("The format is \{numDice\}d\{diceSize\}. Try 7d12 as an example.")
	else:
		numRolls = int(numRollsGroup.group()[:-1])
		diceSize = int(diceSizeGroup.group()[1:])
		rolls = list()
		total = 0
		for x in range(0,numRolls):
			roll = randint(1,diceSize)
			rolls.append(roll)
			total += roll
		message = "" + str(regex) + ": " + str(rolls) + "\nTotal: " + str(total)
		await ctx.channel.send(message)

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
	latestPost = Post(file, time.time(), str(hash), str(guild))

	f = open(logFile)
	data = json.load(f)
	f.close()

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
		json.dump(data, dataFile, indent=4, default=Post.to_dict)
	return reposted

def postExpired(timePosted:float):
	if postTTL == -1:
		return False
	return time.time() - timePosted >= postTTL

bot.run(TOKEN)
