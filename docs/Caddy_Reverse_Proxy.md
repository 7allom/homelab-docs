# Caddy Reverse Proxy

Caddy is the entry point for all web traffic. Rather than publishing container ports directly to the LAN, it listens internally on 80/443, handles SSL automatically, and routes requests to the appropriate container by subdomain.

## VPN-gated access

Management interfaces (Portainer, qBittorrent, the *Arr stack) aren't published in `docker-compose.yml`; they exist only within Caddy's internal routing. Access to those routes is further restricted with a reusable snippet that drops any connection not originating from the VPN subnet, localhost, or the Docker bridge:

```caddyfile
(vpn_only) {
    @denied not remote_ip 10.99.99.0/24 127.0.0.1 172.18.0.0/16 192.168.0.109
    abort @denied
}
```

A valid domain and certificate alone aren't enough to reach these services. A connection from outside the VPN or LAN is dropped regardless.

## SSL without exposing 80/443

Ports 80 and 443 remain closed at the router, which rules out the standard HTTP-01 challenge. Caddy instead uses the `serfriz/caddy-duckdns` image to perform a DNS-01 challenge, proving domain ownership through the DuckDNS API via `DUCKDNS_TOKEN`. Let's Encrypt never needs to reach the server directly.

## Local resolution

Because routing relies on wildcard subdomains, local devices need a way to resolve them internally:

- AdGuard Home has a DNS rewrite for `*.mydomain.duckdns.org` pointing to `192.168.0.109`, directing VPN and LAN clients to the host.
- The host's `/etc/hosts` maps the same subdomains to Caddy's internal Docker IP (`172.18.0.200`) for host-to-container traffic.

## Routing configuration

```caddyfile
(vpn_only) {
    @denied not remote_ip 10.99.99.0/24 127.0.0.1 172.18.0.0/16 192.168.0.109
    abort @denied
}

*.YOUR_DOMAIN.duckdns.org {
    tls {
        dns duckdns {env.DUCKDNS_TOKEN}
    }

    @vault host vault.YOUR_DOMAIN.duckdns.org
    handle @vault {
        reverse_proxy vaultwarden:80
    }

    @qbit host qbit.YOUR_DOMAIN.duckdns.org
    handle @qbit {
        import vpn_only
        reverse_proxy qbittorrent:8090
    }

    # same pattern applies to portainer, sonarr, radarr, prowlarr, bazarr, jellyseerr, ntfy
}
```

Vaultwarden is the one service left outside `vpn_only`, since it needs to remain reachable from the Bitwarden client apps regardless of network.
