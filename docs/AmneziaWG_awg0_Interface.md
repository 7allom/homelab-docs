# AmneziaWG VPN (awg0)

Bare-metal VPN, run outside of Docker. While standard WireGuard is exceptionally fast, its static headers and predictable packet sizes are easily flagged by Deep Packet Inspection (DPI) firewalls. AmneziaWG resolves this by modifying headers and randomizing packet padding, making the tunnel indistinguishable from normal UDP traffic without sacrificing encryption speed.

- Config: `/etc/amnezia/amneziawg/awg0.conf`
- Port: `51820/udp`
- Service: `sudo systemctl enable --now awg-quick@awg0`

### Firewall and Routing Rules (PostUp / PostDown)

To allow connected clients to access the internet, `iptables` routing rules are required within the interface configuration.

**Configuration:**
```ini
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -s 10.99.99.0/24 -o enp4s0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -s 10.99.99.0/24 -o enp4s0 -j MASQUERADE
```

* `iptables -A FORWARD -i %i -j ACCEPT` & `-o %i`: Permits traffic to be forwarded in and out of the `awg0` interface.
* `iptables -t nat -A POSTROUTING ... -j MASQUERADE`: Translates the VPN peer IP addresses to the host's outgoing interface (`enp4s0`).

```bash
sudo awg-quick up awg0      # start
sudo awg-quick down awg0    # stop
sudo awg                    # status
```

## Adding a peer

Works the same for a phone or a laptop, just change `PEER_NAME` and bump the octet. Pulls the obfuscation parameters (`Jc`, `Jmin`, `Jmax`, `S1`, `S2`, `H1`-`H4`) straight from the server config instead of copying them by hand, since those have to match exactly between the server and every peer or the handshake fails.

```bash
PEER_NAME="laptop"        # or "mobile", "tablet", whatever
PEER_OCTET="4"            # next free number, check awg0.conf for what's already used

CLIENT_PRIV=$(awg genkey)
CLIENT_PUB=$(echo "$CLIENT_PRIV" | awg pubkey)
SERVER_PUB=$(sudo awg show awg0 public-key)
OBFUSCATION_PARAMS=$(sudo grep -E "^(Jc|Jmin|Jmax|S1|S2|H1|H2|H3|H4)" /etc/amnezia/amneziawg/awg0.conf)

sudo awg set awg0 peer "$CLIENT_PUB" allowed-ips 10.99.99.${PEER_OCTET}/32
echo -e "\n[Peer]\nPublicKey = $CLIENT_PUB\nAllowedIPs = 10.99.99.${PEER_OCTET}/32" | sudo tee -a /etc/amnezia/amneziawg/awg0.conf > /dev/null

cat > ~/${PEER_NAME}-client.conf << EOF
[Interface]
PrivateKey = $CLIENT_PRIV
Address = 10.99.99.${PEER_OCTET}/32
# Points to AdGuard Home on the host LAN for internal resolution
DNS = 192.168.0.109
$OBFUSCATION_PARAMS

[Peer]
PublicKey = $SERVER_PUB
Endpoint = YOUR_DOMAIN.duckdns.org:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
```

For mobile, import the resulting `.conf` into the AmneziaWG app directly, or convert it to a QR code with `qrencode` so you don't have to transfer a file. For a laptop, `scp` the file over from the server (same LAN, rides on the existing SSH port, nothing new to open) and either import it through the AmneziaWG desktop client or bring it up directly with `sudo awg-quick up ~/laptop-client.conf`.

Delete the generated `.conf` off the server once it's transferred, it contains the peer's private key and has no reason to sit there afterward.
