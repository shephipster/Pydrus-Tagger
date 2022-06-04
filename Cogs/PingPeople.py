import json
import os
import time

from Entities import User
from Utilities.ProcessUser import processUser
from Utilities.Tagger import Tagger


async def ping_people(ctx, tag_list, exempt_user):
	"""	Takes a tag_list from an image and pings the people that it concerns.
		Pings use userID so it can't call by nickname
	"""
	pingTime = time.time()
	isPM = not ctx.guild
	exempt_user = User.User(exempt_user) if exempt_user else None

	loggedUsers = []

	if isPM:
		return

	user, data = await processUser(ctx, guid = ctx.guild.id, uid= ctx.author.id)
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
		if exempt_user != None and loopUser.id == exempt_user.id.id:
			continue
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
			if exempt_user != None and loopUser.id == exempt_user.id.id:
					continue
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

	with open(os.getenv('GUILDS_FILE'), "w") as dataFile:
		json.dump(data, dataFile, indent=4)