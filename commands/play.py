import discord
import asyncio
from GeminiAI.index import sayHelloAI
from Speaker.ActualSong import actualSong
from Speaker.SayHello import sayHello
from utils.youtube import get_youtube_audio, get_image_youtube_video
from utils.GetInfoSongFromYTMusic import GenerateQueueRecommended, GetInfoSongYTM

async def play_song(current_url, interaction=None, client=None, voice_client=None, isPlaylist=False):
    try:
        guild_id = interaction.guild_id
        
        # 1. Genera cola recomendada
        GenerateQueueRecommended(current_url, client, guild_id, isPlaylist)
        
        queue = client.music_queues.get(guild_id, [])
        if not queue:
            await interaction.channel.send("URL inválida")
            return
  
        current_song = queue[0]
        
        # 2. Obtiene audio y miniatura
        audio_url = get_youtube_audio(current_song['url_yt'])
        thumbnail = get_image_youtube_video(current_song["url_yt"])
        
        # 3. Embed de estado 
        embed = discord.Embed(
            title="🎵 Reproductor de música",
            description=f"Reproduciendo: **{current_song['title']}**",
            color=discord.Color.blurple(),
        )
        embed.set_author(
            name=interaction.user.name,
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/512px-YouTube_full-color_icon_%282017%29.svg.png"
        )
        embed.set_image(url=thumbnail)
        embed.set_footer(text="Bot de música creado por Daeoro")

        await interaction.channel.send(embed=embed)
        
        # 4. Preparación de FFmpeg 
        source = discord.FFmpegPCMAudio(
            executable="ffmpeg",
            source=audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )
        
        # 5. Callback al finalizar la canción
        def after_play(err):
            if err:
                print(f"⚠️ Error al finalizar la canción: {err}")
            else:
                print("🎧 Canción terminada. Buscando relacionada...")
                asyncio.run_coroutine_threadsafe(
                    play_next_in_queue(interaction.guild.id, client, interaction, voice_client),
                    client.loop
                )
                
        # 6. Anunciar por VOZ la canción actual
        await actualSong(current_song['title'], current_song['artist'])
        
        voice_client.play(discord.FFmpegPCMAudio("next_song.mp3"))
        
        while voice_client.is_playing():
            await asyncio.sleep(0.5)        
            
        # 7. Reproducir la canción
        voice_client.play(source, after=after_play)

    except Exception as e:
        print("❌ Error al reproducir:", e)
        await interaction.channel.send("❌ Error al reproducir la canción")
        
        
async def play_next_in_queue(guild_id, client, interaction, voice_client):
    """Saca la siguiente canción de la cola y la reproduce."""
    # 1. Obtiene la cola actual
    queue = client.music_queues.get(guild_id, [])
    
    if not queue:
        print("🎵 Cola vacía.")
        return
    
    # 2. Elimina la canción que terminó
    queue.pop(0)
    
    # 3. Obtén la siguiente canción
    next_url = queue[0] if queue else None 
    print(f"▶️ Siguiente canción: {next_url}")
    
    await play_song(next_url['url_yt'], interaction, client, voice_client)

async def setup(client: discord.Client):
    @client.tree.command()
    async def play(interaction: discord.Interaction, url: str, playlist: bool = False):
        """Reproduce una canción de YouTube"""
        # 1. Validar que el usuario esté en un canal de voz
        if not interaction.user.voice:
            await interaction.response.send_message(
                "⚠️ Debes estar en un canal de voz para usar este comando.",
                ephemeral=True
            )
            return

        voice_channel = interaction.user.voice.channel
        
        # 2. Responder inmediatamente para evitar timeout de interacción
        await interaction.response.send_message("🎶 Preparando para reproducir...", ephemeral=False)

        # 3. Asegurar conexión de voz
        try:
            voice_client = discord.utils.get(client.voice_clients, guild=interaction.guild)
            if not voice_client:
                await sayHelloAI("Acabas de entrar al canal de voz para colocar musica, di hola de una manera divertida, sarcástica, grosera y agresiva")
                
                voice_client = await voice_channel.connect()
                print("✅ Conectado al canal de voz.")
                # Saludar por primera vez
                
                voice_client.play(discord.FFmpegPCMAudio("tts.mp3"))
                while voice_client.is_playing():
                    await asyncio.sleep(0.5)
                    
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
            
        # 4. Inicializar cola si no existe
        if interaction.guild_id not in client.music_queues:
            client.music_queues[interaction.guild_id] = []
            
        queue = client.music_queues[interaction.guild_id]
        
        # 5. Si ya está reproduciendo: añadir a la cola
        if voice_client.is_playing():
            song_data = GetInfoSongYTM(url)
            queue.insert(1,song_data)
            await interaction.channel.send(f"🎶 Agregado a la cola en la siguiente posición")
            return
        
        # 6. Reproducir inmediatamente
        await play_song(url, interaction=interaction, client=client, voice_client=voice_client, isPlaylist=playlist)