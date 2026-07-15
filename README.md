# Homelab Infrastructure & Routing

Documentation for a self-hosted home server running on CachyOS. The architecture centers on containerized service management, strict edge routing, and keeping internal services off the LAN entirely. Access is gated through a bare-metal VPN and a reverse proxy rather than exposed ports.

## Network & Edge
- Routing: [Double NAT Routing](docs/Double_NAT_Routing.md), [DuckDNS Automation](docs/DuckDNS_Automation.md)
- Hardware firewall: TP-Link sub-router
- Host: static IP `192.168.0.109/24`
- DNS / ad-blocking: `adguardhome`, bound directly to the host interface

## Security
- [UFW Firewall Rules](docs/UFW_Firewall_Rules.md): ports 22/tcp, 51820/udp
- [CrowdSec Configuration](docs/CrowdSec_Configuration.md): intrusion detection and automated banning, v1.7.8
- [AppArmor Profiles](docs/AppArmor_Profiles.md): mandatory access control for host-networked containers
- [AmneziaWG VPN](docs/AmneziaWG_awg0_Interface.md): DPI-resistant WireGuard variant

## Docker Stack
Configuration conventions: [Environment Variables](docs/Environment_Variables_Template.md), [Storage Paths](docs/Docker_Storage_Paths.md), [Permissions](docs/Docker_Permissions.md).

**Gateway & secrets**
- `caddy`: reverse proxy, VPN-gated internal routing, Let's Encrypt via DNS-01 challenge. [Details](docs/Caddy_Reverse_Proxy.md)
- `vaultwarden`: self-hosted password manager, signups disabled, HTTPS-only. [Setup](docs/Vaultwarden_Setup.md) / [Encrypted Backup](docs/Vaultwarden_R2_Backup.md)

**Media automation**
- Playback: `jellyfin` (hardware-accelerated transcoding via `/dev/dri`), `jellyseerr`
- Library management: `sonarr`, `radarr`, `bazarr`
- Acquisition: `prowlarr`, `flaresolverr`, `qbittorrent`
- [Full writeup](docs/Docker_Arr_Stack.md)

**Utilities**
- `ntfy`: push notifications, integrated with CrowdSec alerting
- `bot-instance`: custom Discord bot ([details](docs/Docker_Bot_Instance.md))
- `portainer`: monitoring dashboard for the stack

## Operations
- [Backup strategy](docs/Docker_Config_Backup.md): encrypted, automated, offsite
- [Routine maintenance](docs/System_Maintenance.md)

---

Built and maintained as a personal infrastructure project. Not a tutorial, just a working reference for how the pieces fit together.
