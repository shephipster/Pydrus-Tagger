import json
import os

from Entities import User

async def processUser(ctx, guid=-1):
	#If this is in DM's, there is no guild with an id
	if not ctx.guild:
		if guid == -1:
			await ctx.channel.send("I'm having trouble knowing what guild you want.\nEither try that again in the guild you want to update stuff for or give me the guild ID")
			return None, None
	else:
		guid = str(ctx.guild.id)

	uid = str(ctx.author.id)

	f = open(os.getenv('GUILDS_FILE'))
	guilds = json.load(f)
	f.close()

	user = User.User(ctx.author.id)

	if uid not in guilds[guid]['users']:
		guilds[guid]['users'][uid] = user.__dict__

	user.setFromDict(uid, guilds[guid]['users'][uid])
	return user, guilds