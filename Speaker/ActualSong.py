from gtts import gTTS
import edge_tts
import os

async def actualSong(song: str, artist: str = "No se, jaja"):
    text = f"Ahora viene {song}, de {artist}"
    tts = edge_tts.Communicate(
        text=text,
        voice="es-CO-GonzaloNeural",
        rate="+12%",   # más rápido = más juvenil
        pitch="+12Hz",  # más agudo = suena más joven
    )
    await tts.save("next_song.mp3")