from gtts import gTTS
import edge_tts
import os

async def sayHello(text="Buenas Perro hijueputa, cabeza e verga... Masca picha"):
    tts = edge_tts.Communicate(
        text=text,
        voice="es-CO-GonzaloNeural",
        rate="+12%",   # más rápido = más juvenil
        pitch="+50Hz",  # más agudo = suena más joven
    )
    await tts.save("tts.mp3")