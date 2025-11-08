import json
import yt_dlp

def SaveInfoJSONVideo(info: str, output_file="video_info.json"):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Información guardada en {output_file}")
        return info
    except Exception as e:
        print(f"❌ Error al obtener la información: {e}")
        return None
