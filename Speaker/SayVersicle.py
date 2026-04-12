import edge_tts

async def sayVersicle(text):
    text = "Versiculo del dia. " + text
    try:
        tts = edge_tts.Communicate(
            text=text,
            # voice="es-CO-GonzaloNeural",
            voice="es-MX-JorgeNeural",
            rate="+12%",   # más rápido = más juvenil
            pitch="+30Hz",  # más agudo = suena más joven
        )
        await tts.save("versicle.mp3")

    except Exception as e:
        print("❌ Error en TTS leyendo versiculo:", e)