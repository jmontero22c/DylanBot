# commands/skip.py
import discord
from commands.play import play_next_in_queue

async def setup(client: discord.Client):
    @client.tree.command()
    async def skip(interaction: discord.Interaction):
        """Salta a la siguiente canción en la cola."""
        voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)

        if not voice_client or not voice_client.is_connected():
            await interaction.response.send_message("❌ No estoy conectado a un canal de voz.", ephemeral=True)
            return

        if not voice_client.is_playing():
            await interaction.response.send_message("⏹ No hay ninguna canción en reproducción.", ephemeral=True)
            return

        await interaction.response.send_message("⏭ Saltando a la siguiente canción...")
        voice_client.stop()  # Esto activará el after_play() y continuará la cola
