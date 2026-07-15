# UFW Host Firewall

Docker manipulates `iptables` directly, bypassing UFW entirely. Published container ports rely on the TP-Link router not forwarding them, not on UFW. UFW here is scoped strictly to the host's native services (SSH, the VPN interface).

## Restoring rules from scratch
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow 22/tcp        # SSH
sudo ufw allow 51820/udp     # AmneziaWG

sudo ufw enable
sudo ufw status verbose
```

The Discord bot runs on `network_mode: host` and only requires outbound UDP for voice traffic. Since UFW allows outbound by default, no additional inbound rule is needed.
