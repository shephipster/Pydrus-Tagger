import json
import os

from Entities import User

async def processUser(ctx, guid:int, uid: int):
	f = open(os.getenv('GUILDS_FILE'))
	guilds = json.load(f)
	f.close()

	user = User.User(uid)
	user_id = f'{uid}'
	guild_id = f'{guid}'

	if user_id not in guilds[guild_id]['users']:
		guilds[guild_id]['users'][user_id] = user.__dict__

	user.setFromDict(user_id, guilds[guild_id]['users'][user_id])
	return user, guilds