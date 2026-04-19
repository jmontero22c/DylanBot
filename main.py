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

async def load_commands():
    from commands import hello, play, skip, versicle
    await hello.setup(client)
    await play.setup(client)
    await skip.setup(client)
    await versicle.setup(client)
    print("Comandos cargados correctamente.")

# Evento on_ready - se activa cuando el bot se conecta
@client.event
async def on_ready():
    print(f'✅ Bot listo: {client.user.name} - {client.user.id}')
    print(f'   Guilds: {[g.name for g in client.guilds]}')

    # Iniciar servidor web DESPUÉS de que el bot esté conectado
    # Solo iniciar si no está ya corriendo
    if not hasattr(client, '_web_server_started'):
        client._web_server_started = True
        run_web_server(client)

async def main():
    await load_commands()
    await client.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Bot detenido manualmente.")
