# Nextcloud (Family File Storage)

A self-hosted Drive replacement for the family, separate from everything else in the stack. Runs on Postgres and Redis instead of Nextcloud's default SQLite, since SQLite locks the whole database on every write and multiple people syncing files at once makes that noticeable fast.

VPN-only, same as Portainer and qBittorrent. The alternative was leaving it open to the public internet so family members wouldn't need AmneziaWG installed, but that trades away the one thing every other service in this stack has in common, no exposed login surface, for convenience. Everyone already needs the VPN for other things, so the extra step isn't new friction, just one more thing running through it.

```yaml
  nextcloud-db:
    image: postgres:17
    container_name: nextcloud-db
    <<: *default-logging
    environment:
      - POSTGRES_DB=nextcloud
      - POSTGRES_USER=nextcloud
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
    volumes:
      - ${DOCKER_ROOT}/nextcloud/db:/var/lib/postgresql/data
    restart: unless-stopped

  nextcloud-redis:
    image: redis:alpine
    container_name: nextcloud-redis
    <<: *default-logging
    restart: unless-stopped

  nextcloud:
    image: nextcloud:latest
    container_name: nextcloud
    <<: *default-logging
    depends_on:
      - nextcloud-db
      - nextcloud-redis
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
      - TZ=${TZ}
      - POSTGRES_HOST=nextcloud-db
      - POSTGRES_DB=nextcloud
      - POSTGRES_USER=nextcloud
      - POSTGRES_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
      - REDIS_HOST=nextcloud-redis
      - NEXTCLOUD_TRUSTED_DOMAINS=cloud.YOUR_DOMAIN.duckdns.org
      - OVERWRITEPROTOCOL=https
      - OVERWRITEHOST=cloud.YOUR_DOMAIN.duckdns.org
      - OVERWRITECLIURL=https://cloud.YOUR_DOMAIN.duckdns.org
      - TRUSTED_PROXIES=172.18.0.0/16
    volumes:
      - ${DOCKER_ROOT}/nextcloud/html:/var/www/html
      - /mnt/data/family-files:/var/www/html/data
    restart: unless-stopped
```

Postgres is pinned to a specific major version (`17`, not `latest`) on purpose. A database container that silently jumps major versions on an update can leave the data files in a format the new version refuses to start against, since major version bumps need an explicit migration step, not just a new image tag. Learned that one firsthand rebuilding this: the data directory got initialized under 16 early on, then the image moved to 17, and Postgres just fatal-looped on every restart until the old data directory was wiped and reinitialized clean.

`OVERWRITEPROTOCOL`, `OVERWRITEHOST`, and `OVERWRITECLIURL` exist because Caddy terminates SSL and talks to Nextcloud over plain HTTP internally. Without them, Nextcloud doesn't reliably know it's being reached over HTTPS through a proxy, and generates broken or empty asset paths instead, which shows up as a blank grey page with nothing failing loudly in the console. `TRUSTED_PROXIES` tells it to trust the connection info Caddy passes along rather than treating Caddy itself as the client.

## Caddy route

```caddyfile
    @nextcloud host cloud.YOUR_DOMAIN.duckdns.org
    handle @nextcloud {
        import vpn_only
        reverse_proxy nextcloud:80
    }
```

Covered by the same wildcard cert as everything else, no separate SSL setup needed.

## Setup

First boot takes a minute or two while the database schema initializes. Visit the domain over the VPN and the setup wizard should auto-detect the Postgres/Redis connection from the environment variables already passed in, no need to fill in the database fields manually.

Once the admin account is created:
- **Settings → Users**: one account per family member, with an individual storage quota set per person in the same screen.
- **Settings → Security**: 2FA, worth turning on for the admin account at minimum, even behind the VPN.

Sharing permissions (view-only, edit, expiring links) are set per-file or per-folder through the normal Files app, not globally.
