# Media Stack (*Arr)

All services share identical mount paths (`${MEDIA_ROOT}`, `${HDD_ROOT}`) across downloaders and organizers to preserve hardlinking. Imports link rather than copy, avoiding duplicate storage.

- **Jellyfin**: hardware-accelerated transcoding via `/dev/dri`. Resource-capped at 4 CPUs / 4096M to prevent transcode load from affecting the rest of the host.
- **qBittorrent**: capped at 2 CPUs / 2048M, pinned to Cloudflare DNS (1.1.1.1 / 1.0.0.1) internally, running the `libtorrentv1` tag for tracker compatibility.
- **Prowlarr + FlareSolverr**: FlareSolverr isn't exposed to the host; Prowlarr reaches it over the internal Docker network at `http://flaresolverr:8191`.
- **Sonarr / Radarr / Bazarr**: standard configuration, using `PUID`/`PGID` to write files as the local user rather than root.
- **Jellyseerr**: request front-end, routed through Caddy rather than exposed directly.
