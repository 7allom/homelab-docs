# Portainer

Web UI for monitoring and maintaining the Docker stack. Since the environment is managed declaratively through `docker-compose`, Portainer is used strictly for observability rather than deployment.

- URL: `https://portainer.YOUR_DOMAIN.duckdns.org`
- Bind-mounts `/var/run/docker.sock`, granting root-level control over the Docker daemon. Because of this deep access, the container exposes no local ports and is routed strictly through Caddy's `vpn_only` Access Control List.

Primary uses: tailing logs for containers, monitoring resource usage during heavy loads (Jellyfin transcoding, qBittorrent activity), and pruning unused images and volumes.
