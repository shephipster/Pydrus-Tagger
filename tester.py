import asyncio
import Services.IQDBService as iqs

url = 'https://img3.gelbooru.com/images/1e/d2/1ed25bbb50c93e00be35f8253996790e.jpg'

async def test():
    data = await iqs.getFromUrl(url)
    print(data)
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())