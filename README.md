# Pydrus-Tagger
Takes a Hydrus server and tags images using SauceNao and its results. Written in Python and can be used for more than just Hydrus.

Important note: I am only intermediate with Python, so there are bound to be bugs here and there especially as new features are added.
This almost exclusively applies to KiraBot though, so if you don't care about that then you should have no trouble.

Most everything is as simple as importing and calling. By and large though, you'll want to just use the sauceNaoApi::getAllTags method,
but this is just a small hobby project so do what you want with this. Make a discord bot that pings your friends for them, tags your
private Hydrus library, it's all up to you.

Usage:
If you just want to work on tagging your Hydrus files the simplest way is to run HyTagUI.py

  It is highly recommended to run hashFileEstimater.py first. It will rapidly go through your Hydrus database and create two files for you. This is extremely useful if it is your first time using
  HyTagUI.py or if you, like I did 30 minutes prior to making hashFileEstimater.py, accidentally delete your file containing all of the processed files HyTagUI has already worked on.
  processedHashes.txt will contain a list of all hashes that have at least one url reference to a site that has tags (Gel, Dan, Sankaku, E621, Pixiv) and is the default for HyTagUI.py. 
  needWork.txt doesn't actually have much use and can be deleted.

  (Make sure you have a processedHashes.txt file, even if it's blank)
  Launch HyTagUI.py
  Hit "Initialize" and wait, the more files you have the longer it will take as it is checking all files to see which need tagging. Hydrus is going to be bombarded when this happens and it currently can not be paused during this stage, so don't plan on being able to use Hydrus very much during this time. At around 55,000 files it takes me up to 15 minutes to initialize. Don't worry, optimization will be coming at some point.
  Once it is done it will let you know you can start. Set the stop limit (default 100) to whatever you want and hit "Run", but know that the base limit for sauceNao is 200. Personally I recommend 150 as your limit.
  Hit run. It will begin tagging your images using the tags it finds from GelBooru, DanBooru, Yandex, Twitter, and many more. This WILL slow down Hydrus a little bit, but you can pause the program with the big red "Pause" button.
  When it's done, or you have paused it, you can hit "Stop" to close the program. This is more of a formality, if you really want you can just close it anyway. Try to use the "stop" button though as it is safer and less likely to cause any possible issues with the file tracking what hashes have been searched/tagged.
  
  Hytag.py does effectively the same thing, but it runs through all the files one at a time and will tag new ones as it finds them. This is the faster method, but it is not able to be paused and is a little less intuitive. Look it over or run it with the default of 25 files to get an idea of how it might work for you.
  
KiraBot:
  Kira bot serves as a proof-of-concept for using the various different APIs in other programs. 
  It can currently:
  Track of what tags users request to be pinged for and will do so if an image posted to the server is found to have those tags.
  It can also roll random images from Gelbooru (and Danbooru but that's disabled by default due to API limits) that have specific tags, skipping ones that have tags blacklisted by the server.
  Roll random elements from a list (A user may ask it to pick three random days of the week for example using "+random [Mon,Tue,Wed,Thur,Fri]")
  
