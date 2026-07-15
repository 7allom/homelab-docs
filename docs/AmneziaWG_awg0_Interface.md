# AmneziaWG VPN (awg0)

Bare-metal VPN, run outside of Docker. While standard WireGuard is exceptionally fast, its static headers and predictable packet sizes are easily flagged by Deep Packet Inspection (DPI) firewalls. AmneziaWG resolves this by modifying headers and randomizing packet padding, making the tunnel indistinguishable from normal UDP traffic without sacrificing encryption speed.

- Config: `/etc/amnezia/amneziawg/awg0.conf`
- Port: `51820/udp`
- Service: `sudo systemctl enable --now awg-quick@awg0`

```bash
sudo awg-quick up awg0      # start
sudo awg-quick down awg0    # stop
sudo awg                    # status
```

## Adding a mobile peer

```bash
CLIENT_PRIV=$(awg genkey)
CLIENT_PUB=$(echo "$CLIENT_PRIV" | awg pubkey)
SERVER_PUB=$(sudo awg show awg0 public-key)

sudo awg set awg0 peer "$CLIENT_PUB" allowed-ips 10.99.99.3/32
echo -e "\n[Peer]\nPublicKey = $CLIENT_PUB\nAllowedIPs = 10.99.99.3/32" | sudo tee -a /etc/amnezia/amneziawg/awg0.conf > /dev/null

cat > ~/mobile-client.conf << EOF
[Interface]
PrivateKey = $CLIENT_PRIV
Address = 10.99.99.3/32
# Points to AdGuard Home on the host LAN for internal resolution
DNS = 192.168.0.109

[Peer]
PublicKey = $SERVER_PUB
Endpoint = YOUR_DOMAIN.duckdns.org:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
```

Increment the last octet of `10.99.99.x` for each additional peer. Import the resulting config into the AmneziaWG mobile client, or convert it to a QR code with `qrencode`.
