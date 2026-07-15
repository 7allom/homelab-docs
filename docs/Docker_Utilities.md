# Ntfy

Self-hosted push notification service. Any process on the server (currently CrowdSec) can POST an alert that arrives on a mobile device within seconds.

- Port: `8095`, not published to the host, reached through Caddy or the internal Docker network
- Restart in isolation: `docker compose up -d ntfy`
