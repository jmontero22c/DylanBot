import discord
import asyncio
from utils.youtube import get_youtube_audio, get_image_youtube_video
from utils.GetInfoSongFromYTMusic import GenerateQueueRecommended, GetInfoSongYTM

async def play_song(current_url, interaction=None, client=None, voice_client=None):
    try:
        GenerateQueueRecommended(current_url, client, interaction.guild_id)
        
        if len(client.music_queues[interaction.guild_id]) == 0:
            await interaction.channel.send("URL inválida")
            return
  
        current_song = client.music_queues[interaction.guild_id][0]
        
        audio_url = get_youtube_audio(current_song['url_yt'])
        
        embed = discord.Embed(
            title="🎵 Reproductor de música",
            description=f"Reproduciendo: **{current_song['title']}**",
            color=discord.Color.blurple(),
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/512px-YouTube_full-color_icon_%282017%29.svg.png"
        )
        embed.set_image(url=get_image_youtube_video(current_song['url_yt']))
        embed.set_footer(text="Bot de música creado por Daeoro")

        await interaction.channel.send(embed=embed)
        
        source = discord.FFmpegPCMAudio(
            executable="ffmpeg",
            source=audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )
        
        def after_play(err):
            if err:
                print(f"⚠️ Error al finalizar la canción: {err}")
            else:
                print("🎧 Canción terminada. Buscando relacionada...")
                asyncio.run_coroutine_threadsafe(
                    play_next_in_queue(interaction.guild.id, client, interaction, voice_client),
                    client.loop
                )
                
        voice_client.play(source, after=after_play)

    except Exception as e:
        print("❌ Error al reproducir:", e)
        await interaction.channel.send("❌ Error al reproducir la canción")
        await play_song(client.music_queues[interaction.guild_id][0]['url_yt'], interaction, client, voice_client)
        
        
async def play_next_in_queue(guild_id, client, interaction, voice_client):
    """Saca la siguiente canción de la cola y la reproduce."""
    queue = client.music_queues.get(guild_id, [])
    if not queue:
        print("🎵 Cola vacía.")
        return

    queue.pop(0)
    next_url = queue[0] if queue else None 
    print(f"▶️ Siguiente canción: {next_url}")
    await play_song(next_url['url_yt'], interaction, client, voice_client)

async def setup(client: discord.Client):
    @client.tree.command()
    async def play(interaction: discord.Interaction, url: str):
        if not interaction.user.voice:
            await interaction.response.send_message("Debes estar en un canal de voz.", ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel
        await interaction.response.send_message("🎶 Preparando para reproducir...", ephemeral=False)

        try:
            voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
            if not voice_client:
                voice_client = await voice_channel.connect()
                print("✅ Conectado al canal de voz.")
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        except Exception as e:
            print("❌ Error al conectar al canal de voz:", e)
            await interaction.channel.send("❌ No pude conectarme al canal de voz.")
            return

        # Esperar hasta que esté conectado realmente
        timeout = 5
        while not voice_client.is_connected():
            await asyncio.sleep(0.1)
            timeout -= 0.1
            if timeout <= 0:
                print("⛔ Timeout esperando conexión de voz")
                await interaction.channel.send("❌ No se pudo conectar al canal de voz a tiempo.")
                return

        # Si ya está reproduciendo, agregar a la cola
        if interaction.guild_id not in client.music_queues:
            client.music_queues[interaction.guild_id] = []
        queue = client.music_queues[interaction.guild_id]
        if voice_client.is_playing():
            song = GetInfoSongYTM(url, client, interaction.guild_id)
            queue.insert(0,song)
            await interaction.response.send_message(f"🎶 Agregado a la cola (posición {len(queue)}): {url}")
            return
        
        # Función interna que reproduce una canción y busca la siguiente al terminar
        await play_song(url, interaction=interaction, client=client, voice_client=voice_client)