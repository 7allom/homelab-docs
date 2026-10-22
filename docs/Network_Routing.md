# Network Routing & Remote Access

The server sits on a local subnet (`192.168.1.0/24`). The primary ISP modem handles WAN routing and DHCP, while the TP-Link router operates strictly in Access Point (AP) mode as a bridge.

## Routing path
Only one public port is exposed to the internet:
- **WAN Port 443/udp** forwarded to **LAN Port 51820/udp** on the server (`192.168.1.10`).

Forwarding WAN port 443 to 51820 helps bypass stateless firewalls and network filters that block standard WireGuard traffic, while keeping the server configured on port 51820 locally.

**Inbound connection path (VPN):**
1. DuckDNS resolves to the current ISP public IPv4.
2. The remote client initiates a handshake to `YOUR_DOMAIN.duckdns.org:443`.
3. The router forwards WAN port 443 to `192.168.1.10:51820`.
4. UFW permits `51820/udp` and hands the traffic to the `awg0` interface.
