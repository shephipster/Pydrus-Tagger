# Pydrus-Tagger
IQDBTagger.py

This is a somewhat simple program for automatically tagging your images, useful for when you save images and upload them later to your client.
First you will want to update the .env file to include: The url to your Hydrus client (http://192.168.1.XXX as an example) and the API key you want to use the program with (you will need an API key that has permission to fetch files, add tags, and remove tags)
Once you have these .env values you can launch the program. If everything works out the program will tell you to hit initialize to load in up to 1000 (this can be increased by adjusting the value of MAX_FILES value in IQDBTagger.py). If the program has trouble it will instead let you know where it had issues.
Once you have hit initialize and the files are noted the program will let you know you can hit run.
The pause and stop button are there in case you assign too many files and need to stop or just want to pause for a minute because it's slowing down your internet.

# KiraBot

A slightly older discord bot that has an array of uses, but the primary function is to let users declare what tags they like. The bot will then reverse-image search images posted to discord (using the IQDBService) and will ping any users that have declared tags contained in the image. Please note you may need to include access keys and/or other credentials to various sites for Kira to function properly (sites include Twitter, GelBooru, Danbooru, E621). To be perfectly honest I can't remember how much of those were for the randomPost function where it will go to a random site and grab a random image with given tags and how much was required for image searching. 

# HyTag and HyTagUI

These are older and not maintained, but they basically do the same as IQDBTagger. It is highly recommended to use IQDBTagger instead.

