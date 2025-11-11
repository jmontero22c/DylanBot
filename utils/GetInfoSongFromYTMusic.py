from ytmusicapi import YTMusic
from utils.debug_youtube import SaveInfoJSONVideo
from utils.youtube import get_youtube_id_url
import requests
import functools
import yt_dlp

MAX_QUEUE_SIZE = 20

test_session = requests.Session()
test_session.request = functools.partial(test_session.request, timeout=80)

ytmusic = YTMusic(requests_session=test_session)

def GenerateQueueRecommended(url, client, guild_id, is_playlist=False):    

    # Si ya hay canciones en la cola, no hacer nada
    if(len(client.music_queues[guild_id]) > 1): return
  
    video_id = get_youtube_id_url(url, is_playlist)
    
    if(video_id is None):
        print("Error", video_id)
        return
      
    #No funciona con los mix de youtube
    if is_playlist:
        createQueueFromPlaylist(client, guild_id, video_id)
        return
    
    watch_data = ytmusic.get_watch_playlist(videoId=video_id)
    tracks = watch_data.get("tracks", [])
    
    if(len(client.music_queues[guild_id]) == 1):
      tracks.pop(0)
    
    for track in tracks:
      if(len(client.music_queues[guild_id]) >= MAX_QUEUE_SIZE):
          break
        
      info_song = {
        "title": track.get("title"),
        "artist": track["artists"][0]["name"] if track.get("artists") else None,
        "album": track.get("album", {}).get("name") if track.get("album") else None,
        "videoId": track.get("videoId"),
        "url_ytm": f"https://music.youtube.com/watch?v={track['videoId']}",
        "url_yt": f"https://www.youtube.com/watch?v={track['videoId']}"
      }
        
      client.music_queues[guild_id].append(info_song)  
      print(f"Added to queue: {info_song['title']} by {info_song['artist']}", )
      
        
    SaveInfoJSONVideo(client.music_queues[guild_id], output_file="queue_info.json")
    
    
def GetInfoSongYTM(url, client, guild_id):
    video_id = url.split("v=")[1].split("&")[0]
    watch_data = ytmusic.get_watch_playlist(videoId=video_id)
    tracks = watch_data.get("tracks", [])
    if tracks:
        track = tracks[0]
        info_song = {
            "title": track.get("title"),
            "artist": track["artists"][0]["name"] if track.get("artists") else None,
            "album": track.get("album", {}).get("name") if track.get("album") else None,
            "videoId": track.get("videoId"),
            "url_ytm": f"https://music.youtube.com/watch?v={track['videoId']}",
            "url_yt": f"https://www.youtube.com/watch?v={track['videoId']}"
        }
        return info_song
      
def createQueueFromPlaylist(client, guild_id, video_id):
  
  songs = ytmusic.get_watch_playlist(videoId=video_id, limit=MAX_QUEUE_SIZE, shuffle=False)
  
  for song in songs.get("tracks", []):
    info_song = {
      "title": song.get("title"),
      "artist": song["author"] if song.get("author") else None,
      "album": song.get("album", {}).get("name") if song.get("album") else None,
      "videoId": song.get("videoId"),
      "url_ytm": f"https://music.youtube.com/watch?v={song['videoId']}",
      "url_yt": f"https://www.youtube.com/watch?v={song['videoId']}"
    }
      
    client.music_queues[guild_id].append(info_song)  
    print(f"Added to queue: {info_song['title']} by {info_song['artist']}", )
    
  SaveInfoJSONVideo(client.music_queues[guild_id], output_file="queue_info.json")
  return