import discord

async def setup(client):
    @client.tree.command()
    async def hello(interaction: discord.Interaction):
        """Dylan te dice hola!"""
        await interaction.response.send_message(f'Hi, {interaction.user.mention}')
