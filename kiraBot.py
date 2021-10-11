import discord
import requests
import re
import json
import time
import imagehash
import sauceNaoApi
import os
from dotenv import load_dotenv

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
tagFile = 'users.json'
logFile = 'imageLog.json'

@bot.event
async def on_ready():
	print('Running')

pic_ext = ['.jpg', '.png', '.gif']


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
async def tagMe(ctx, *args):
	""" 	Adds the given tag to the users list of tags to be notified for.
		<arg> is the name of any Danbooru tag you wished to be notified about.
		If you do not have a tag list then one will be created for you.
		Use this to make a tag list for yourself should you not have one.
	 """
	userID = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	if userID not in data:
		newUser = {userID: {"tags" : [], "notify" : True, "name" : ctx.author.name, "lastPing" : time.time(), "pingDelay" : 300, "specifyTag" : False}}
		data.update(newUser)
		with open(tagFile, "w") as dataFile:
			json.dump(data, dataFile, indent=4)

	f = open(tagFile)
	data = json.load(f)
	f.close()
	for uid in data:
		if uid == userID:
			tagList = data[uid]['tags']
			for tag in args:
				if tag.lower() in tagList:
					confirm = data[uid]['name'] + ", " + tag + " is already in your tag list."
					await ctx.send(confirm)
					return
				else:
					tagList.append(str(tag).lower())
					data[uid]['tags'] = tagList

	f.close()
	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)
	confirm = "Alright " + data[userID]['name'] + ", I've added "
	for tag in args:
		confirm = confirm + tag + " "
	confirm = confirm + " to your list of tags"
	await ctx.send(confirm)
	return

@bot.command()
async def untagMe(ctx, arg):
	""" 	Removes the tag from the users list of tags to be notified for.
		<arg> is the tag you want removed from your list.
		If you do not have a list nothing will happen.
	 """
	userID = str(ctx.author.id)
	f = open(tagFile)
	data = json.load(f)
	f.close()
	if userID not in data:
		return
	for uid in data:
		if uid == userID:
			if arg.lower() not in data[uid]['tags']:
				await ctx.send("That wasn't even in your tag list.")
				return
			data[uid]['tags'].remove(arg.lower())
	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4)
	confirm = "Alright " + data[userID]['name'] + ", I removed " + arg + " from your tag list."
	await ctx.send(confirm)
	""" end if not """
	""" else remove tag from entry if present """

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
	for u in data:
		if u == str(ctx.author.id):
			response = "Your tag list is: "+ ", ".join(data[u]['tags'])
			await ctx.author.send(response)
			break
	f.close()

@bot.command()
async def myTags(ctx):
	await checkTags(ctx)

@bot.command()
async def setNotify(ctx, state):
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

	f=open(tagFile)
	data = json.load(f)
	uid = str(ctx.author.id)
	for user in data:
		if user == uid:
			data[user]['notify'] = ping
			message = "Alright, ping for you are now set to" + str(ping)
			await ctx.author.send(message)
			return
	with open(tagFile, "w") as dataFile:
		json.dump(data, dataFile, indent = 4)

""" More commands can be added using the @bot.command() tag """

""" This code pretty much entirely from ImagineNotHavingAnAlt, bless their soul """

@bot.command()
async def slide(ctx):
	""" Starts a PM with Kira, keeps commands hidden, avoids spam. """
	await ctx.author.send("You wanted something?")


""" Using the brand new SauceNaoAPI that I wrote - Shephipster"""
def sauceNaoLookup(url):
	tags = sauceNaoApi.getAllTagsFromUrl(url)
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
	if debug: print("Poster:" + str(ctx.author) + " [ctx.author.id] ")
	f = open(tagFile)
	data = json.load(f)
	f.close()
	usersToPing = []
	usersToAlert = []
	pingTime = time.time()
	isPM = not ctx.guild
	if(debug):
		print("Time of ping is: " , pingTime)
		print(data)

	tagsList = "`"
	peopleList = ""

	for user in data:
		if(debug):
			print("User: ", data[user]['name'], "[", user, "]" , "\nlastPinged: " , data[user]['lastPing'] , "\npingDelay: " , data[user]['pingDelay'] , "\ncurrentTime: " , pingTime , "\nmeetsDelay? " , (pingTime - data[user]['lastPing'] > data[user]['pingDelay']) )
		for tag in tag_list:
			if tag in data[user]['tags'] and (pingTime - data[user]['lastPing'] > data[user]['pingDelay']):
				if(debug):
					print(data[user]['name'], "has contained tag", tag, "and isn't timed out on pings.")
				if not isPM and (str(user) != str(ctx.author.id)) and (user in [str(member.id) for member in ctx.guild.members]):
					if(debug):
						print(data[user]['name'], "eligible for notifications.")
					data[user]['lastPing'] = pingTime
					tagsList += f"{tag}, "
					if data[user]['notify'] == True:
						usersToPing.append(user)
					else:
						usersToAlert.append(data[user]["name"])
					break
	tagsList = tagsList[:-2]	#fencepost last ', '
	tagsList += "`"
	text = "Let's see here...\n"
	for people in usersToPing:
		peopleList += f"<@{people}>, "
		#await ctx.channel.send(f"Hey <@{people}>, this has something for you.")
		if(debug):
			print("Pinging ", people)

	for people in usersToAlert:
		peopleList += f"{people}, "
		#await ctx.channel.send(f"Hey {people}, found something for you.")
		if(debug):
			print("Stating ", people)

	text += peopleList[:-2]  #fencepost
	text += " should like this. It's got "
	text += tagsList
	text += " and everything."
	if debug:	print("People List:" + peopleList)
	if debug: 	print("Tag List:" + tagsList)
	if debug:	print("Ping text:" + text)
	if(peopleList != ""):
		await ctx.channel.send(text)
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



def repostDetected(guild, file):
#https://github.com/polachok/py-phash#:~:text=py-pHash%20Python%20bindings%20for%20libpHash%20%28http%3A%2F%2Fphash.org%2F%29%20A%20perceptual,file%20derived%20from%20various%20features%20from%20its%20content.

	#Get the url, passed as file, and load the image
	image = Image.open(requests.get(file, stream=True).raw)
	#Get the Phash of the image
	hash = imagehash.phash(image)
	if debug: print("PHash: " + str(hash))

	#Generate post object
	reposted = False;
	latestPost = Post(file, time.time(), str(hash), str(guild))
	if debug: print(latestPost)

	#Load in existing objects
	f = open(logFile)
	data = json.load(f)
	f.close()

#	if debug: print(data)

	for post in data:
		#delete expired posts
		if postExpired(post['timePosted']):
			data.remove(post)
		if post['guild'] == latestPost.guild:
			dist = distance.hamming(post['phash'], latestPost.phash) * len(hash)
			if dist <= repostDistance:
				reposted = True;
				if debug: print("\n", latestPost, " reposted with ", post, " PHamming of ", dist )
				break #short circuit

	#reached end of logged files, determine if needs trimming or not
	if len(data) >= logSizeLimit:
		#logs added with smaller indeces being oldest, so delete the first one
		del data[0]
	#Space will have been made by this point, add latestPost no matter what
	data.append(latestPost)
	#if debug: print(type(data))
	#if debug: print(data)
	#Save the list to the log file
	with open(logFile, "w") as dataFile:
		json.dump(data, dataFile, indent=4, default=Post.to_dict)
	return reposted;

class Post:
	url=""
	timePosted=0
	phash=""
	guild=""

	def __init__(self, url, timePosted, phash, guild):
		self.url = url
		self.timePosted = timePosted
		self.phash = phash
		self.guild = guild

	def __str__(self):
		return  f'Post({self.url}, {self.timePosted}, {self.phash})'

	def to_dict(p):
		if isinstance(p, Post):
			return {"url": p.url, "timePosted": p.timePosted, "phash": p.phash, "guild": p.guild}
		else:
			raise TypeError("Unexpected type {0}".format(p.__class__.__name__))

def postExpired(timePosted):
	if postTTL == -1:
		return False;
	return time.time() - timePosted >= postTTl;

bot.run(TOKEN)
