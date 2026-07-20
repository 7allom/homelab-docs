# Double NAT Routing & Remote Access

The server sits behind two routers (an ISP modem, followed by a TP-Link sub-router). Isolating the homelab behind a secondary router creates a hard physical security boundary, limiting the blast radius of any potential container compromise while allowing for custom firewall rules that do not interfere with the household's standard internet traffic. 

Because of this physical isolation, remote access requires forwarding through both routers, anchored by DuckDNS since the public IP isn't static.

## Dynamic DNS
A systemd timer updates DuckDNS with the current IPv4/IPv6 address every 5 minutes. See [DuckDNS Automation](docs/DuckDNS_Automation.md).

## Routing path
Only one service cross the double NAT:
- UDP 51820 to the AmneziaWG interface

AmneziaWG's native obfuscation removes the need to disguise the tunnel on port 443, since it isn't identifiable as VPN traffic to begin with.

**Inbound connection path (VPN example):**
1. DuckDNS resolves to the current ISP public IP
2. ISP router forwards UDP 51820 to the TP-Link's static WAN IP
3. TP-Link forwards UDP 51820 to the server's static LAN IP (`192.168.0.109`)
4. UFW permits the traffic and hands it to `awg0`

## Troubleshooting remote access
Check in this order when a handshake fails from outside the network:
1. Does the DuckDNS domain resolve to the current public IP?
2. Did the ISP router drop the static lease, assigning the TP-Link a new IP?
3. Is UFW allowing 51820/udp, and is `awg-quick up awg0` active?
