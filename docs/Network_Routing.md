# Network Routing & Remote Access

The server sits on a flat local subnet (`192.168.1.0/24`). The primary ISP modem handles WAN routing and DHCP, while the TP-Link router operates strictly in Access Point (AP) mode as a bridge.

## Routing path
Only one service is forwarded through the ISP gateway:
- UDP 51820 (or 443) forwarded directly to the server (`192.168.1.10`) for AmneziaWG.

**Inbound connection path (VPN):**
1. DuckDNS resolves to the current ISP public IPv4.
2. ISP router forwards the VPN port directly to `192.168.1.10`.
3. UFW permits the traffic and hands it to `awg0`.
