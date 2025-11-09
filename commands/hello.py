import discord

from Speaker.SayHello import sayHello

async def setup(client):
    @client.tree.command()
    async def hello(interaction: discord.Interaction):
        """Dylan te dice hola!"""
        await interaction.response.send_message(f'Hi, {interaction.user.mention}')
        
        if not interaction.user.voice:
            return

        voice_channel = interaction.user.voice.channel
        try:
            voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
            if not voice_client:
                voice_client = await voice_channel.connect()
                print("✅ Conectado al canal de voz.")
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        except Exception as e:
            print("❌ Error al conectar al canal de voz:", e)
            await interaction.channel.send("No pude conectarme al canal de voz.")
            return
        
        await sayHello()
        voice_client.play(discord.FFmpegPCMAudio("tts.mp3"))