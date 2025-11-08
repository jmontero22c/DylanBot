import discord

async def hello(interaction: discord.Interaction):
    """Saludos."""
    await interaction.response.send_message("El mundo te saluda pequeña luciernaga.")

