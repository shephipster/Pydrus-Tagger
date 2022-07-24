from datetime import datetime, timedelta
from Utilities.Tagger import Tagger
from sql.models.Users import Users
from sql.models.User_Tag_Mappings import User_Tag_Mappings


async def ping_people(ctx, tag_list, exempt_user):
	"""	Takes a tag_list from an image and pings the people that it concerns.
		Pings use userID so it can't call by nickname
	"""

	users: list = []
	cleaned_tags = list(tag_list)
	for i in range(len(cleaned_tags)):
		cleaned_tags[i] = Tagger.getCleanTag(cleaned_tags[i])
  
	results = []
	utm = User_Tag_Mappings()
	for tag in cleaned_tags:
		people = utm.search(guild_id = ctx.guild.id, blacklist = False, tag=tag)
		ignore = utm.search(guild_id = ctx.guild.id, blacklist = True, tag=tag)
		for person in people:
			if person not in ignore:
				results.append((person[1], person[3]))
	
	results.sort()
	pingTime = datetime.now()
	users = Users()
	message = ""
	last_user = 0
	for result in results:
		user = users.getByPKey(result[0])[0]
		last_pinged = datetime.strptime(user[2], '%Y-%m-%d %H:%M:%S.%f')
		if last_pinged + timedelta(seconds=user[4]) <= pingTime:
			users.updateTime(user_id = user[1])
			if last_user != user[1]:
				if last_user != 0:
					message +="\n"
				last_user = user[1]
			if user[3]:				
				message += f"<@{user[0]}> for `"
			else:
				message += f"{user[1]} for `"
			message += result[1] + ", "
	message = message[:-2] + "`"
	if results and message != '`':
		await ctx.channel.send(message)