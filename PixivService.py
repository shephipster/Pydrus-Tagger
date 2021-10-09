#Okay, so this is all I can figure out about Pixiv's API. There's basically zero information out there and
#this is the best I can find. Unfortunately this is giving a 403, which means that unless Pixiv suddenly
#opens up their API to the public I can't get any kind of Auth keys and using an API is out.

PIXIV_URL = "public-api.secure.pixiv.net/"

#Therefore, we're going to have to either not handle pixiv at all or scrape the page.
#Trying to scrape the page is possible, but it's slow and cumbersome for both the
#program and Pixiv servers. Will need to consider this.