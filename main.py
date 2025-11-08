import discord
from models.client import MyClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

TOKEN = os.getenv('TOKEN')
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user.name} - {client.user.id}')

async def load_commands():
    from commands import hello, play, skip
    await hello.setup(client)
    await play.setup(client)
    await skip.setup(client)
    print("Comandos cargados correctamente.")
    

async def main():
    await load_commands()
    await client.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Bot detenido manualmente.")
