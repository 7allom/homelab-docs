# Docker Storage & Bind Mounts

Core paths, defined in `~/containers/.env`:
- `${DOCKER_ROOT}`
- `${MEDIA_ROOT}`
- `${HDD_ROOT}`

## Media paths and hardlinking
These mounts must match identically across the media stack for hardlinking to work; otherwise imports copy files instead of linking them.

- `${MEDIA_ROOT}` maps to `/data` (mounted as `/media` in Jellyfin)
- `${HDD_ROOT}` maps to `/vault`
- `/mnt/data/personalMedia` maps to `/personal`

Applied consistently across qBittorrent, Sonarr, Radarr, Bazarr, and Jellyfin.

The vault drive is mounted by UUID in `/etc/fstab`, keeping the mount point stable across reboots regardless of device naming changes.
