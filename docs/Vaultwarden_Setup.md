# Vaultwarden

A lightweight Rust implementation of the Bitwarden server API, fully compatible with official Bitwarden clients while using significantly less resource overhead than the official server.

No ports are exposed directly; all traffic routes through Caddy.

```yaml
vaultwarden:
  image: vaultwarden/server:latest
  container_name: vaultwarden
  <<: *default-logging
  environment:
    - TZ=${TZ}
    - WEBSOCKET_ENABLED=true  # real-time sync across devices
    - SIGNUPS_ALLOWED=false   # closed instance, no new account creation
  volumes:
    - ${DOCKER_ROOT}/vaultwarden/data:/data
  restart: unless-stopped
```

The data volume holds `db.sqlite3`, RSA encryption keys, and attachments. Must remain readable by the host user for the backup script to function correctly.

Requires HTTPS to operate, as Bitwarden clients reject unencrypted connections. Handled by Caddy's DNS-01 challenge.
