# Pydrus-Tagger
Takes a Hydrus server and tags images using SauceNao and its results. Written in Python and can be used for more than just Hydrus.

Most everything is as simple as importing and calling. By and large though, you'll want to just use the sauceNaoApi::getAllTags method,
but this is just a small hobby project so do what you want with this. Make a discord bot that pings your friends for them, tags your
private Hydrus library, it's all up to you.

How to use:
  you _can_ call it directly with python3 sauceNaoApi.py <url>
  You'll need to have a .env file that contains all of your API keys because I am _NOT_ giving mine out
  You can also import from sauceNaoApi if you want
  
Notice:
  I have written AI, Machine Learning algorithms, multivariate calculus solvers, and auto-pinging Discord bots in Python, so naturally
  I have not Earthly idea how I have managed to write any of this. If something's busted don't expect any fast fixes. 
  
#Kira-Bot
  If you're just using the discord Kira Bot, you can ignore the HydrusAPI, Pydrus, and tester.
  You just need to make sure you still have the following in your .env file:
  Twitter Bearer Token API, SauceNao API Token, Threshold percent (90.0 is a good value), Discord API Key and Token
  You can also ignore the files HydrusAPI and Pydrus-Tagger in that case
  Once everything is installed and loaded, just call python3 .\kiraBot.py and let it run. Will update if problems are found, as well
  as if any improvements come up.
  
#Notes
   Since this uses SauceNao, if too many searches happen at once a problem can occur and no results will return. You also only have
  6 searches every 30s and 200 every 24hr with a default sauceNao account, but for small servers this shouldn't be an issue.
  
#Plans
  Will consider encrypting certain data in the users.json if security is a concern for people, but for now since tags are mentioned anyway it
  doesn't make a whole lot of sense.
  Considering adding a feature where you can turn off tag mentioning, so you'll still get pinged but it won't say why (if you opt for that)
  Will add a check for twitter API, so if you don't want to sign up for that you can opt to leave it empty
