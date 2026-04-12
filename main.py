import discord
from commands import versicle
from models.client import MyClient
import asyncio
import os
import threading
from dotenv import load_dotenv
from web.server import run_web_server

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
# intents.members = True  # Necesario para detectar cuando usuarios entran a canales de voz

TOKEN = os.getenv('TOKEN')
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user.name} - {client.user.id}')

# @client.event
# async def on_voice_state_update(member, before, after):
#     """Debuggear cambios de estado de voz"""
#     if member.id == client.user.id:
#         if before.channel is None and after.channel is not None:
#             print(f"✅ Bot conectado a: {after.channel.name}")
#         elif before.channel is not None and after.channel is None:
#             print(f"⛔ Bot desconectado de: {before.channel.name}")
#     else:
#         # Debuggear otros usuarios
#         if before.channel != after.channel:
#             print(f"👤 {member.name}: {before.channel} -> {after.channel}")

async def load_commands():
    from commands import hello, play, skip, versicle
    await hello.setup(client)
    await play.setup(client)
    await skip.setup(client)
    await versicle.setup(client)
    print("Comandos cargados correctamente.")
    

async def main():
    await load_commands()

    # Iniciar servidor web en thread separado
    run_web_server(client)

    await client.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Bot detenido manualmente.")
