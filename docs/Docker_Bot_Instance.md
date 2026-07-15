# Discord Bot (bot-instance)

A custom Python 3.11 Discord bot running alongside the rest of the stack. Built on `discord.py`, with `yt-dlp` and FFmpeg for audio, and Gemini 2.5 Flash for conversational and moderation features.

Runs on `network_mode: host`. Discord's voice API relies heavily on real-time, dynamic UDP streams. Running the bot inside Docker's default virtual bridge introduces network translation latency, causing the internal NAT to quietly drop audio packets during playback. Binding the container directly to the host network interface bypasses the virtual bridge entirely, ensuring stable voice connections.

- Build context: `./discord-bot` (the Dockerfile compiles `libopus`/`libsodium` for voice support)
- Secrets (`BOT_TOKEN`, `GEMINI_API_KEY`) are isolated in `./discord-bot/.env`, separate from the main stack's `.env`
- Persistent data: `${DOCKER_ROOT}/discord-bot/data:/app/data`, stores `jail_data.json` so moderation state survives container rebuilds

## Features

**AI integration (Gemini 2.5 Flash)**
- Automated welcome/goodbye messages generated per member
- `/ask`: general-purpose assistant command, auto-chunks responses around Discord's 2000-character limit, with exponential backoff on rate limits
- `/roast`: targeted response generator with an optional topic parameter

**Voice**
- `/play`: streams YouTube audio via `yt-dlp` and `FFmpegPCMAudio`
- Dynamic voice channels: joining a designated hub channel creates a temporary private VC, removed automatically once empty

**Utility & Gaming**
- `/squad`: creates an interactive UI View for users to queue up for games. Tracks the active player roster via embedded buttons and automatically disbands if the host leaves

**Moderation**
- `/jail`, `/unjail`: restricts a user to a specific voice channel, actively dragging them back if they attempt to switch channels
- `/flashbang`: brief, audio-based moderation action that temporarily displaces a user, plays a sound file, and returns them
- `/gostudy`, `/endstudy`: enforces focus by assigning a designated study role that mutes text access and forcibly disconnects the target from active voice channels
