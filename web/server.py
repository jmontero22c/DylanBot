from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
# Configurar CORS para permitir cualquier origen (necesario para Vercel)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Referencia al cliente de Discord (se asigna desde main.py)
discord_client = None

def init_web_server(client):
    """Inicializa la referencia al cliente de Discord"""
    global discord_client
    discord_client = client

def get_voice_client(guild_id):
    """Obtiene el voice_client para un guild específico"""
    if not discord_client:
        return None
    for vc in discord_client.voice_clients:
        if vc.guild.id == guild_id:
            return vc
    return None

def get_guild_info(guild_id):
    """Obtiene información del guild"""
    if not discord_client:
        return None
    guild = discord_client.get_guild(guild_id)
    return guild

@app.route('/')
def index():
    """Página principal del panel de control"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Obtiene el estado actual del bot en todos los guilds"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

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
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    guilds = []
    for guild in discord_client.guilds:
        voice_client = get_voice_client(guild.id)
        guilds.append({
            "id": guild.id,
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "connected": voice_client.is_connected() if voice_client else False
        })

    return jsonify({"success": True, "data": {"guilds": guilds}, "error": None})

@app.route('/api/queue/<int:guild_id>')
def get_queue(guild_id):
    """Obtiene la cola de reproducción de un guild"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    queue = discord_client.music_queues.get(guild_id, [])
    voice_client = get_voice_client(guild_id)

    return jsonify({
        "success": True,
        "data": {
            "queue": queue,
            "playing": voice_client.is_playing() if voice_client else False,
            "paused": voice_client.is_paused() if voice_client else False
        },
        "error": None
    })

@app.route('/api/play/<int:guild_id>', methods=['POST'])
def play_song(guild_id):
    """Agrega una canción a la cola"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"success": False, "error": "URL requerida", "data": None})

    url = data['url']
    is_playlist = data.get('playlist', False)

    # Importar funciones necesarias
    from utils.GetInfoSongFromYTMusic import GetInfoSongYTM, GenerateQueueRecommended
    from utils.youtube import get_youtube_id_url

    # Inicializar cola si no existe
    if guild_id not in discord_client.music_queues:
        discord_client.music_queues[guild_id] = []

    # Obtener info de la canción
    try:
        song_data = GetInfoSongYTM(url)
        if not song_data:
            return jsonify({"success": False, "error": "No se pudo obtener información de la canción", "data": None})

        queue = discord_client.music_queues[guild_id]
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
            GenerateQueueRecommended(url, discord_client, guild_id, is_playlist)

            return jsonify({"success": True, "data": {"message": "Reproduciendo ahora", "song": song_data}, "error": None})

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "data": None})

@app.route('/api/skip/<int:guild_id>', methods=['POST'])
def skip_song(guild_id):
    """Salta a la siguiente canción"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    if not voice_client.is_playing():
        return jsonify({"success": False, "error": "No hay reproducción activa", "data": None})

    voice_client.stop()  # Esto activa el callback after_play

    return jsonify({"success": True, "data": {"message": "Canción saltada"}, "error": None})

@app.route('/api/pause/<int:guild_id>', methods=['POST'])
def pause_song(guild_id):
    """Pausa la reproducción"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    if not voice_client.is_playing():
        return jsonify({"success": False, "error": "No hay reproducción activa", "data": None})

    voice_client.pause()
    return jsonify({"success": True, "data": {"message": "Reproducción pausada"}, "error": None})

@app.route('/api/resume/<int:guild_id>', methods=['POST'])
def resume_song(guild_id):
    """Reanuda la reproducción"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    if not voice_client.is_paused():
        return jsonify({"success": False, "error": "La reproducción no está pausada", "data": None})

    voice_client.resume()
    return jsonify({"success": True, "data": {"message": "Reproducción reanudada"}, "error": None})

@app.route('/api/volume/<int:guild_id>', methods=['POST'])
def set_volume(guild_id):
    """Ajusta el volumen (0-100)"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    data = request.get_json()
    if not data or 'volume' not in data:
        return jsonify({"success": False, "error": "Volumen requerido (0-100)", "data": None})

    volume = data['volume']
    if not isinstance(volume, (int, float)) or volume < 0 or volume > 100:
        return jsonify({"success": False, "error": "Volumen debe estar entre 0 y 100", "data": None})

    voice_client = get_voice_client(guild_id)
    if not voice_client:
        return jsonify({"success": False, "error": "No conectado a un canal de voz", "data": None})

    # Convertir 0-100 a 0.0-1.0
    volume_float = volume / 100.0
    voice_client.source.volume = volume_float

    return jsonify({"success": True, "data": {"message": f"Volumen ajustado a {volume}%"}, "error": None})

@app.route('/api/queue/<int:guild_id>', methods=['DELETE'])
def clear_queue(guild_id):
    """Limpia toda la cola excepto la canción actual"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    if guild_id in discord_client.music_queues:
        queue = discord_client.music_queues[guild_id]
        # Mantener solo la primera canción (la que está sonando)
        if len(queue) > 1:
            discord_client.music_queues[guild_id] = [queue[0]]
        return jsonify({"success": True, "data": {"message": "Cola limpiada"}, "error": None})

    return jsonify({"success": False, "error": "No hay cola para este guild", "data": None})

@app.route('/api/queue/<int:guild_id>/<int:index>', methods=['DELETE'])
def remove_from_queue(guild_id, index):
    """Elimina una canción específica de la cola (no puede ser la que está sonando)"""
    if not discord_client:
        return jsonify({"success": False, "error": "Bot no inicializado", "data": None})

    if guild_id not in discord_client.music_queues:
        return jsonify({"success": False, "error": "No hay cola para este guild", "data": None})

    queue = discord_client.music_queues[guild_id]

    if index == 0:
        return jsonify({"success": False, "error": "No se puede eliminar la canción actual", "data": None})

    if index < 0 or index >= len(queue):
        return jsonify({"success": False, "error": "Índice fuera de rango", "data": None})

    removed_song = queue.pop(index)
    return jsonify({"success": True, "data": {"message": "Canción eliminada", "song": removed_song}, "error": None})

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
