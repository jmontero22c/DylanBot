import discord 
from discord import app_commands 
import os
from dotenv import load_dotenv

load_dotenv()

id_guild = int(os.getenv('DEV_GUILD'))  
DEV_GUILD = discord.Object(id=id_guild) 

class MyClient(discord.Client): 
    def __init__(self, *, intents: discord.Intents): 
        super().__init__(intents=intents) 
        self.tree = app_commands.CommandTree(self) 
        self.music_queues = {} 
        
    async def setup_hook(self): 
        # self.tree.clear_commands(guild=DEV_GUILD)
        self.tree.copy_global_to(guild=DEV_GUILD) 
        await self.tree.sync(guild=DEV_GUILD)