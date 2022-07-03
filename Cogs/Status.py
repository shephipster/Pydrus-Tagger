from discord.ext import commands, tasks
from discord import Game
import random

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()
        
    @tasks.loop(minutes=5.0)
    async def update_status(self):
        jobs = ['running the casino', 'answering the phones', 'manning the till', 'cooking dinner', 'cleaning the room', 'doing laundry', 'alone time']
        job = random.choice(jobs)
        await self.bot.change_presence(activity = Game(name=job))
    
    @update_status.before_loop
    async def before_update_status(self):
        print('waiting...')
        await self.bot.wait_until_ready()
        await self.bot.change_presence(activity = Game(name="starting work"))
