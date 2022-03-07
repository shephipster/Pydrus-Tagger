import GelbooruService
import DanbooruService

post = GelbooruService.getRandomPostWithTags("aisaka_taiga")
print(post)
if post['rating'] == '-solo_male':
    print("THIS DUDE ROLLING PORN")
# tags = post['tags'].split()
# for tag in tags:
#     print(tag)