from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import os
import asyncio
import discord

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configurar CORS simple para todas las rutas
CORS(app, origins="*", supports_credentials=False)

# Agregar headers CORS a todas las respuestas
# @app.after_request
# def after_request(response):
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Accept'
#     response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,OPTIONS,PUT'
#     response.headers['Access-Control-Max-Age'] = '3600'
#     return response

# Manejar OPTIONS manualmente para preflight requests
# @app.route('/api/<path:path>', methods=['OPTIONS'])
# def handle_options(path):
#     response = jsonify({"success": True})
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,Accept'
#     response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,OPTIONS,PUT'
#     return response

# Decorador para agregar headers CORS a respuestas JSON
def cors_jsonify(*args, **kwargs):
    """Crea una respuesta JSON con headers CORS"""
    response = jsonify(*args, **kwargs)
    # response.headers.add('Access-Control-Allow-Origin', '*')
    # response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    # response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS,PUT')
    return response

# Referencia al cliente de Discord (se asigna desde main.py)
discord_client = None

def init_web_server(client):
    """Inicializa la referencia al cliente de Discord"""
    global discord_client
    discord_client = client

    # Verificar que el cliente es válido
    if discord_client:
        print(f"✅ Web server inicializado con bot: {discord_client.user}")
        print(f"   Guilds disponibles: {[g.name for g in discord_client.guilds]}")
    else:
        print("❌ ERROR: Cliente de Discord es None")

def get_voice_client(guild_id):
    """Obtiene el voice_client para un guild específico"""
    if not discord_client:
        return None
    guild_id_int = int(guild_id) if isinstance(guild_id, str) else guild_id
    for vc in discord_client.voice_clients:
        if vc.guild.id == guild_id_int:
            return vc
    return None

def get_guild_info(guild_id):
    """Obtiene información del guild"""
    if not discord_client:
        return None
    # Buscar guild en la lista de guilds del bot
    for g in discord_client.guilds:
        if g.id == guild_id:
            return g
    return None

@app.route('/')
def index():
    """Página principal del panel de control"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Obtiene el estado actual del bot en todos los guilds"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    guilds = []
    for guild in discord_client.guilds:
        voice_client = get_voice_client(guild.id)
        queue = discord_client.music_queues.get(guild.id, [])

        current_song = None
        if queue:
            current_song = queue[0]

        guilds.append({
            "id": guild.id,
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "connected": voice_client.is_connected() if voice_client else False,
            "playing": voice_client.is_playing() if voice_client else False,
            "paused": voice_client.is_paused() if voice_client else False,
            "channel_name": voice_client.channel.name if voice_client and voice_client.channel else None,
            "current_song": current_song,
            "queue_length": len(queue)
        })

    return jsonify({"success": True, "data": {"guilds": guilds}, "error": None})

@app.route('/api/guilds')
def get_guilds():
    """Obtiene la lista de guilds donde está el bot"""
    print(f"📥 Solicitud API /api/guilds")

    if not discord_client:
        print("   ❌ discord_client es None")
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    print(f"   🤖 Bot: {discord_client.user} (ID: {discord_client.user.id})")

    guilds = []
    for guild in discord_client.guilds:
        voice_client = get_voice_client(guild.id)
        guilds.append({
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "connected": voice_client.is_connected() if voice_client else False
        })

    guild_names = [g['name'] for g in guilds]
    print(f"   📋 Guilds encontrados ({len(guilds)}): {guild_names}")

    return cors_jsonify({"success": True, "data": {"guilds": guilds}, "error": None})
    return jsonify({"success": True, "data": {"guilds": guilds}, "error": None})

@app.route('/api/channels/<string:guild_id>')
def get_voice_channels(guild_id):
    """Obtiene los canales de voz disponibles de un guild"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    # Buscar guild en la lista de guilds del bot (más confiable que get_guild)
    guild = None
    guild_id_int = int(guild_id)
    for g in discord_client.guilds:
        if g.id == guild_id_int:
            guild = g
            break

    if not guild:
        print(f"Guild {guild_id} no encontrado. Guilds disponibles: {[g.id for g in discord_client.guilds]}")
        return cors_jsonify({"success": False, "error": "Servidor no encontrado", "data": None})

    # Obtener canales de voz (excluir AFK y categorías)
    voice_channels = []
    for channel in guild.voice_channels:
        # Calcular usuarios conectados
        member_count = len(channel.members)
        voice_channels.append({
            "id": str(channel.id),
            "name": channel.name,
            "member_count": member_count,
            "user_limit": channel.user_limit if channel.user_limit > 0 else "∞"
        })

    # Ordenar por posición
    voice_channels.sort(key=lambda x: x["name"])

    return cors_jsonify({
        "success": True,
        "data": {"channels": voice_channels},
        "error": None
    })

@app.route('/api/connect/<string:guild_id>', methods=['POST'])
def connect_to_channel(guild_id):
    """Conecta el bot a un canal de voz específico"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    data = request.get_json()
    if not data or 'channel_id' not in data:
        return cors_jsonify({"success": False, "error": "ID de canal requerido", "data": None})

    channel_id = data['channel_id']

    # Buscar guild en la lista de guilds del bot
    guild = None
    print(f"Guilds disponibles: {[g.id for g in discord_client.guilds]}")
    for g in discord_client.guilds:
        if str(g.id) == guild_id:
            guild = g
            break

    if not guild:
        return cors_jsonify({"success": False, "error": "Servidor no encontrado", "data": None})

    print(channel_id)
    # Buscar el canal
    channel = guild.get_channel(int(channel_id))
    if not channel or not isinstance(channel, discord.VoiceChannel):
        return cors_jsonify({"success": False, "error": "Canal de voz no encontrado", "data": None})

    # Verificar si ya está conectado
    voice_client = get_voice_client(guild_id)
    if voice_client and voice_client.is_connected():
        if voice_client.channel.id == channel.id:
            return cors_jsonify({"success": True, "data": {"message": "Ya conectado a este canal"}, "error": None})
        # Mover a otro canal
        asyncio.run_coroutine_threadsafe(voice_client.move_to(channel), discord_client.loop)
        return cors_jsonify({"success": True, "data": {"message": f"Movido a {channel.name}"}, "error": None})

    # Conectar al canal (ejecutar en el loop del bot)
    async def do_connect():
        try:
            await channel.connect(timeout=30.0, reconnect=True)
            return True
        except Exception as e:
            print(f"Error conectando: {e}")
            return False

    future = asyncio.run_coroutine_threadsafe(do_connect(), discord_client.loop)
    try:
        success = future.result(timeout=35)
        if success:
            return cors_jsonify({"success": True, "data": {"message": f"Conectado a {channel.name}"}, "error": None})
        else:
            return cors_jsonify({"success": False, "error": "No se pudo conectar al canal", "data": None})
    except Exception as e:
        return cors_jsonify({"success": False, "error": f"Timeout al conectar: {str(e)}", "data": None})

@app.route('/api/disconnect/<string:guild_id>', methods=['POST'])
def disconnect_from_channel(guild_id):
    """Desconecta el bot del canal de voz"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client or not voice_client.is_connected():
        return cors_jsonify({"success": False, "error": "No conectado a ningún canal", "data": None})

    async def do_disconnect():
        await voice_client.disconnect()
        return True

    future = asyncio.run_coroutine_threadsafe(do_disconnect(), discord_client.loop)
    try:
        future.result(timeout=10)
        return cors_jsonify({"success": True, "data": {"message": "Desconectado"}, "error": None})
    except Exception as e:
        return cors_jsonify({"success": False, "error": str(e), "data": None})

@app.route('/api/queue/<string:guild_id>')
def get_queue(guild_id):
    """Obtiene la cola de reproducción de un guild"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    guild_id_int = int(guild_id)
    queue = discord_client.music_queues.get(guild_id_int, [])
    voice_client = get_voice_client(guild_id)

    # Información del canal actual
    current_channel = None
    if voice_client and voice_client.channel:
        current_channel = {
            "id": voice_client.channel.id,
            "name": voice_client.channel.name
        }

    return jsonify({
        "success": True,
        "data": {
            "queue": queue,
            "playing": voice_client.is_playing() if voice_client else False,
            "paused": voice_client.is_paused() if voice_client else False,
            "connected": voice_client.is_connected() if voice_client else False,
            "current_channel": current_channel
        },
        "error": None
    })

@app.route('/api/play/<string:guild_id>', methods=['POST'])
def play_song(guild_id):
    """Agrega una canción a la cola y la reproduce si no hay nada sonando"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"success": False, "error": "URL requerida", "data": None})

    url = data['url']
    is_playlist = data.get('playlist', False)

    # Importar funciones necesarias
    from utils.GetInfoSongFromYTMusic import GetInfoSongYTM, GenerateQueueRecommended
    from utils.youtube import get_youtube_audio

    # Convertir guild_id a int para la cola
    guild_id_int = int(guild_id)

    # Inicializar cola si no existe
    if guild_id_int not in discord_client.music_queues:
        discord_client.music_queues[guild_id_int] = []

    # Obtener info de la canción
    try:
        song_data = GetInfoSongYTM(url)
        if not song_data:
            return jsonify({"success": False, "error": "No se pudo obtener información de la canción", "data": None})

        queue = discord_client.music_queues[guild_id_int]
        voice_client = get_voice_client(guild_id)

        if voice_client and voice_client.is_playing():
            # Agregar a la cola
            queue.insert(1 if len(queue) > 0 else 0, song_data)
            return jsonify({"success": True, "data": {"message": "Agregado a la cola", "song": song_data}, "error": None})
        else:
            # Reproducir inmediatamente
            if not queue:
                queue.append(song_data)
            else:
                queue[0] = song_data

            # Generar cola recomendada
            GenerateQueueRecommended(url, discord_client, guild_id_int, is_playlist)

            # REPRODUCIR LA CANCIÓN
            if voice_client and voice_client.is_connected():
                try:
                    # Obtener URL de audio de YouTube
                    audio_url = get_youtube_audio(song_data['url_yt'])
                    if not audio_url:
                        return jsonify({"success": False, "error": "No se pudo obtener el audio de YouTube", "data": None})

                    # Crear source de FFmpeg
                    source = discord.FFmpegPCMAudio(
                        executable="ffmpeg",
                        source=audio_url,
                        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                    )

                    # Callback cuando termine la canción
                    def after_play(err):
                        if err:
                            print(f"⚠️ Error al finalizar la canción: {err}")
                        else:
                            print("🎧 Canción terminada. Reproduciendo siguiente...")
                            asyncio.run_coroutine_threadsafe(
                                play_next_song(guild_id_int, voice_client),
                                discord_client.loop
                            )

                    # Reproducir
                    voice_client.play(source, after=after_play)
                    print(f"🎵 Reproduciendo: {song_data['title']}")

                except Exception as e:
                    print(f"❌ Error al reproducir: {e}")
                    return jsonify({"success": False, "error": f"Error al reproducir: {str(e)}", "data": None})

            return jsonify({"success": True, "data": {"message": "Reproduciendo ahora", "song": song_data}, "error": None})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "data": None})

@app.route('/api/skip/<string:guild_id>', methods=['POST'])
def skip_song(guild_id):
    """Salta a la siguiente canción"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    if not voice_client.is_playing():
        return jsonify({"success": False, "error": "No hay reproducción activa", "data": None})

    voice_client.stop()  # Esto activa el callback after_play

    return jsonify({"success": True, "data": {"message": "Canción saltada"}, "error": None})

@app.route('/api/pause/<string:guild_id>', methods=['POST'])
def pause_song(guild_id):
    """Pausa la reproducción"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    if not voice_client.is_playing():
        return jsonify({"success": False, "error": "No hay reproducción activa", "data": None})

    voice_client.pause()
    return jsonify({"success": True, "data": {"message": "Reproducción pausada"}, "error": None})

@app.route('/api/resume/<string:guild_id>', methods=['POST'])
def resume_song(guild_id):
    """Reanuda la reproducción"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    if not voice_client.is_paused():
        return jsonify({"success": False, "error": "La reproducción no está pausada", "data": None})

    voice_client.resume()
    return jsonify({"success": True, "data": {"message": "Reproducción reanudada"}, "error": None})

@app.route('/api/volume/<string:guild_id>', methods=['POST'])
def set_volume(guild_id):
    """Ajusta el volumen (0-100)"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    data = request.get_json()
    if not data or 'volume' not in data:
        return jsonify({"success": False, "error": "Volumen requerido (0-100)", "data": None})

    volume = data['volume']
    if not isinstance(volume, (int, float)) or volume < 0 or volume > 100:
        return jsonify({"success": False, "error": "Volumen debe estar entre 0 y 100", "data": None})

    voice_client = get_voice_client(guild_id)
    print(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    # Convertir 0-100 a 0.0-1.0
    volume_float = volume / 100.0
    voice_client.source.volume = volume_float

    return jsonify({"success": True, "data": {"message": f"Volumen ajustado a {volume}%"}, "error": None})

@app.route('/api/queue/<string:guild_id>', methods=['DELETE'])
def clear_queue(guild_id):
    """Limpia toda la cola excepto la canción actual"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    guild_id_int = int(guild_id)
    if guild_id_int in discord_client.music_queues:
        queue = discord_client.music_queues[guild_id_int]
        # Mantener solo la primera canción (la que está sonando)
        if len(queue) > 1:
            discord_client.music_queues[guild_id_int] = [queue[0]]
        return jsonify({"success": True, "data": {"message": "Cola limpiada"}, "error": None})

    return jsonify({"success": False, "error": "No hay cola para este guild", "data": None})

@app.route('/api/queue/<string:guild_id>/<int:index>', methods=['DELETE'])
def remove_from_queue(guild_id, index):
    """Elimina una canción específica de la cola (no puede ser la que está sonando)"""
    if not discord_client:
        return cors_jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    guild_id_int = int(guild_id)
    if guild_id_int not in discord_client.music_queues:
        return jsonify({"success": False, "error": "No hay cola para este guild", "data": None})

    queue = discord_client.music_queues[guild_id_int]

    if index == 0:
        return jsonify({"success": False, "error": "No se puede eliminar la canción actual", "data": None})

    if index < 0 or index >= len(queue):
        return jsonify({"success": False, "error": "Índice fuera de rango", "data": None})

    removed_song = queue.pop(index)
    return jsonify({"success": True, "data": {"message": "Canción eliminada", "song": removed_song}, "error": None})

async def play_next_song(guild_id, voice_client):
    """Reproduce la siguiente canción en la cola"""
    try:
        queue = discord_client.music_queues.get(guild_id, [])

        if not queue or len(queue) <= 1:
            print("🎵 Cola vacía o solo queda la canción actual.")
            return

        # Eliminar la canción que terminó
        queue.pop(0)

        # Obtener la siguiente canción
        next_song = queue[0]
        print(f"▶️ Siguiente canción: {next_song['title']}")

        # Obtener URL de audio
        from utils.youtube import get_youtube_audio
        audio_url = get_youtube_audio(next_song['url_yt'])

        if not audio_url:
            print("❌ No se pudo obtener el audio de la siguiente canción")
            return

        # Crear source y reproducir
        source = discord.FFmpegPCMAudio(
            executable="ffmpeg",
            source=audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )

        def after_play(err):
            if err:
                print(f"⚠️ Error al finalizar la canción: {err}")
            else:
                print("🎧 Canción terminada. Reproduciendo siguiente...")
                asyncio.run_coroutine_threadsafe(
                    play_next_song(guild_id, voice_client),
                    discord_client.loop
                )

        voice_client.play(source, after=after_play)
        print(f"🎵 Reproduciendo: {next_song['title']}")

    except Exception as e:
        print(f"❌ Error en play_next_song: {e}")
        import traceback
        traceback.print_exc()

def run_web_server(client, host='0.0.0.0', port=5000, debug=False):
    """Inicia el servidor web en un thread separado"""
    init_web_server(client)

    def server():
        app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)

    web_thread = threading.Thread(target=server, daemon=True)
    web_thread.start()
    print(f"🌐 Servidor web iniciado en http://{host}:{port}")

if __name__ == '__main__':
    app.run(debug=True)
