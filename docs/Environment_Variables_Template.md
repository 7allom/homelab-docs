# Secrets & Environment Template (.env)

API keys and absolute paths are centralized in a single `.env` file (`~/containers/.env`) rather than scattered across the compose file, so a path change is a one-line edit rather than a dozen.

```ini
# --- user identification ---
# run `id` to find these; ensures the *Arr stack writes as 'user' rather than root
PUID=1000
PGID=1000

# --- system ---
# centralizing timezone avoids sync mismatches between Sonarr, Radarr, and qBittorrent
TZ=Asia/Riyadh

# --- paths ---
DOCKER_ROOT=~/containers
MEDIA_ROOT=/path/to/media
HDD_ROOT=/path/to/vault

# --- secrets ---
DUCKDNS_TOKEN=
BOT_TOKEN=
GEMINI_API_KEY=
```
