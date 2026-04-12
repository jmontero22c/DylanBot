import yt_dlp

def get_image_youtube_video(url):
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('thumbnail','Couldnt find thumbnail')
    except Exception as e:
            print("❌ Error al obtener miniatura de YouTube:", e)
            return None

def get_youtube_audio(url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
            print("❌ Error al obtener audio de YouTube:", e)
            return None
    
def get_youtube_id_url(url: str, is_playlist: bool = False) -> str:
    try:
        firstPart = url.split("/")[-1]
        if(firstPart.startswith("watch?v=")):
            # Example: https://www.youtube.com/watch?v=Shl5Z8eBpkM&list=RDShl5Z8eBpkM&index=20
            if not is_playlist:
                video_id = url.split("v=")[1].split("&")[0]
            else:
                video_id = url.split("v=")[1]
            return video_id
        else:
            # Example: https://youtu.be/NNGd3uANaes?list=RDNNGd3uANaes
            if not is_playlist:
                video_id = url.split("/")[-1].split("?")[0]
            else:
                video_id = url.split("/")[-1]
                
            video_id = video_id.replace("?","&")
            return video_id
    except Exception as e:
        return None
    
    