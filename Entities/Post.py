class Post:
	urls=""	#this is either a url to some place (e.g Twitter) or a discord file link
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
			return {"url": p.url, "timePosted": p.timePosted, "phash": p.phash, "guild": p.guild,}
		else:
			raise TypeError("Unexpected type {0}".format(p.__class__.__name__))