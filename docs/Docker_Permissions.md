# Docker Folder Permissions

Avoid recursive `chown`/`chmod` operations across `${DOCKER_ROOT}`. Different containers handle user mapping differently, and a blanket permission change reliably breaks database write access for at least one service.

- The *Arr stack and qBittorrent use `linuxserver.io` images, mapping internal processes to the host via `PUID`/`PGID` in the `.env` file. Setting these to `1000:1000` forces the containers to write downloaded files natively as the host user. This prevents permission conflicts and ensures the entire media library can be managed, moved, or deleted directly from the host without resorting to `sudo`.
- Vaultwarden, Jellyfin, and Caddy run under their own internal defaults (often root) and manage volume permissions independently. Leave these alone.
