# Kira Bot
She tags, she pings, she rolls pictures. She's a jack of all trades and totally not modeled after the character she gets her image from.
She's also bound to have some bugs so if something doesn't work or you don't get pinged for an image you probably should have don't be
super surprised. You can run her yourself, which I recommend personally because whoever runs her can see all the tags people have and
you won't have to worry about my little Raspberry Pi making the bot drop, but if you want to add the instance I'm running then you can
go to https://discord.com/api/oauth2/authorize?client_id=891426527223349258&permissions=130112&scope=bot%20applications.commands


# Pydrus-Tagger
Takes a Hydrus server and tags images using SauceNao and its results. Written in Python and can be used for more than just Hydrus.

Important note: I am only intermediate with Python, so there are bound to be bugs here and there especially as new features are added.
This almost exclusively applies to KiraBot though, so if you don't care about that then you should have no trouble.

Most everything is as simple as importing and calling. By and large though, you'll want to just use the sauceNaoApi::getAllTags method,
but this is just a small hobby project so do what you want with this. Make a discord bot that pings your friends for them, tags your
private Hydrus library, it's all up to you.

Usage:
If you just want to work on tagging your Hydrus files the simplest way is to run IQDBTagger.py
As a side note, an unintended but much welcome side effect is that it will also give you a good amount of similar/recommended images. This wasn't
actually meant to happen, but it turns out that artists tend to draw similar work to themselves so you get similar content.

  It is highly recommended to run hashFileEstimater.py first. It will rapidly go through your Hydrus database and create two files for you, one of files that the
  system doesn't think need to be processed and ones it does think need to be worked on. This is extremely useful if it is your first time using
  HyTagUI.py and you already have filees you pulled in from a booru or if you, like I did 30 minutes prior to making hashFileEstimater.py, accidentally 
  delete your file containing all of the processed files HyTagUI has already worked on.
  processedHashes.txt will contain a list of all hashes that have at least one url reference to a site that has tags (Gel, Dan, Sankaku, E621, Pixiv)
  and is the default for HyTagUI.py. 
  needWork.txt doesn't actually have much use and can be deleted at the moment, but at some point I might find a use for it someday.

  (Make sure you have a processedIQDBHashes.txt file, even if it's blank)
  Launch IQDBTagger.py
  Hit "Initialize" and wait, the more files you have the longer it will take as it is checking all files to see which need tagging. Hydrus is going to be bombarded when this happens and it currently can not be paused during this stage, so don't plan on being able to use Hydrus very much during this time. At around 55,000 files it takes me up to 4 minutes to initialize. HyTagUI is not optimized yet and takes around 15 minutes to initialize 55,000 files.
  Once it is done it will let you know you can start. Set the stop limit (default 100) to whatever you want and hit "Run". If using HyTagUi you might want to leave this at 100 or 150 on account of the sauceNao api limits (if you have an upgraded account you can crank it up).
  Hit run. It will begin tagging your images using the tags it finds from GelBooru, DanBooru, Yandex, Twitter, and many more. This WILL slow down Hydrus a little bit, but you can pause the program with the big red "Pause" button. The process is a bit faster than doing it manually, but don't expect it to be super fast. IQDB has limits that have to be accounted for via making the program stall for set times. You can try lowering this but the lower it goes the more likely IQDB is to give you issues. At default values, it takes roughly 1 hour to initialize and process 250 files.
  When it's done, or you have paused it, you can hit "Stop" to close the program. This is more of a formality, if you really want you can just close it anyway. Try to use the "stop" button though as it is safer and less likely to cause any possible issues with the file tracking what hashes have been searched/tagged.
  
KiraBot:
  Kira bot serves as a proof-of-concept for using the various different APIs in other programs. 
  It can currently:
  Track of what tags users request to be pinged for and will do so if an image posted to the server is found to have those tags.
  It can also roll random images from Gelbooru (and Danbooru but that's disabled by default due to API limits) that have specific tags, skipping ones that have tags blacklisted by the server or the channel you are rolling images in. (Added the blacklist after some poor saps tried to get girls in the cowgirl position and ended up with horse genetalia in their server. Default blacklist includes explicit [loli, shota, and cub] images)
  Roll random elements from a list (A user may ask it to pick three random days of the week for example using "+random [Mon,Tue,Wed,Thur,Fri]")
