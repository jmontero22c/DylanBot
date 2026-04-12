# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dylan is a Discord music bot with personality. It plays music from YouTube/YouTube Music, uses TTS for voice responses, and integrates with Google's Gemini AI for sarcastic greetings.

## Development Commands

### Running the Bot
```bash
# Activate virtual environment first
python main.py
```

### Environment Setup
Create a `.env` file with:
- `TOKEN` - Discord bot token
- `DEV_GUILD` - Development guild/server ID (integer)
- `GEMINI_API_KEY` - Google Gemini API key

### Dependencies
```bash
pip install -r requirements.txt
```

Requirements: `discord.py`, `flask`, `yt-dlp`, `ytmusicapi`, `python-dotenv`, `edge-tts`, `gtts`, `google-genai`

**External Requirement:** FFmpeg must be installed and available in PATH (used for audio playback).

## Architecture

### Core Architecture

**Entry Point (`main.py`)**
- Creates `MyClient` instance with voice intents
- Loads commands via `load_commands()` which calls `setup()` on each command module
- Commands are slash commands registered via Discord's app_commands

**Client (`models/client.py`)**
- `MyClient` extends `discord.Client` with a `CommandTree` for slash commands
- Key state: `self.music_queues = {}` - maps `guild_id` to a list of song dicts
- Commands sync to `DEV_GUILD` (development server only, not global)

### Command Pattern

Each command module in `commands/` exports an async `setup(client)` function that registers slash commands using the `@client.tree.command()` decorator. Commands include:
- `play` - Music playback with YouTube/YouTube Music integration
- `skip` - Skip current song
- `hello` - Voice greeting
- `versicle` - Bible verses via voice

### Music System (`commands/play.py`)

The music system uses a queue-based architecture:

1. **Song Queue**: `client.music_queues[guild_id]` is a list of song dicts with keys: `title`, `artist`, `album`, `videoId`, `url_ytm`, `url_yt`
2. **Auto-Queue Generation**: `GenerateQueueRecommended()` uses YouTube Music API to populate related songs when queue is empty
3. **Audio Pipeline**: yt-dlp extracts audio URL → FFmpegPCMAudio streams it → `voice_client.play()` with `after=` callback triggers next song
4. **FFmpeg Options**: Uses `-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5` for stable streaming

### Voice/TTS System (`Speaker/`)

Uses `edge_tts` library with specific voice configurations:
- Default voice: `es-MX-JorgeNeural` for greetings/verses
- Colombian voice (`es-CO-GonzaloNeural`) for "now playing" announcements
- Generated audio saved to: `tts.mp3`, `next_song.mp3`, `versicle.mp3`

### YouTube Integration (`utils/`)

- `youtube.py`: yt-dlp wrapper for audio extraction and thumbnail retrieval
- `GetInfoSongFromYTMusic.py`: YouTube Music API via `ytmusicapi` for recommendations and song metadata
- URL parsing handles both `watch?v=` and `youtu.be/` formats
- `MAX_QUEUE_SIZE = 20` limits auto-generated queue

### Gemini AI (`GeminiAI/index.py`)

Integrated with Google's Gemini API for AI-generated greetings. Currently used in `play.py` to generate sarcastic welcome messages when users join voice channels.

## File Organization

- `commands/` - Slash command implementations
- `models/` - Core client class
- `utils/` - YouTube/YouTube Music API wrappers and utilities
- `Speaker/` - TTS functionality using edge_tts
- `GeminiAI/` - Google Gemini AI integration
- `Discord/` - Additional command handlers
- `resources/` - Static assets (audio files, verse JSON)

## Important Implementation Notes

- Commands sync to a single dev guild (`DEV_GUILD`), not globally
- Bot expects FFmpeg executable named exactly "ffmpeg" in PATH
- Queue auto-populates from YouTube Music recommendations; does NOT work with YouTube Mix playlists
- TTS files are generated at runtime and gitignored
- YouTube Music API has an 80-second timeout configured via `requests.Session`
