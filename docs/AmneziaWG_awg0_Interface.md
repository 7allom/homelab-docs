# AmneziaWG VPN (awg0)

Bare-metal VPN, run outside of Docker. While standard WireGuard is exceptionally fast, its static headers and predictable packet sizes are easily flagged by Deep Packet Inspection (DPI) firewalls. AmneziaWG resolves this by modifying headers and randomizing packet padding, making the tunnel indistinguishable from normal UDP traffic without sacrificing encryption speed.

- Config: `/etc/amnezia/amneziawg/awg0.conf`
- Port: `443/udp` 
- Service: `sudo systemctl enable --now awg-quick@awg0`

> Using port 443 can help bypass stateless firewalls
### Firewall and Routing Rules (PostUp / PostDown)

To allow connected clients to access the internet, `iptables` routing rules are required within the interface configuration.

**Configuration:**
```ini
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -s 10.99.99.0/24 -o enp4s0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -s 10.99.99.0/24 -o enp4s0 -j MASQUERADE
```

* `iptables -A FORWARD -i %i -j ACCEPT` & `-o %i`: Permits traffic to be forwarded in and out of the `awg0` interface.
* `iptables -t nat -A POSTROUTING ... -j MASQUERADE`: Translates the VPN peer IP addresses to the host's outgoing interface (`enp4s0`).

> Looked like a DNS issue at first (because it's always DNS), turned out to be missing FORWARD and MASQUERADE rules, UFW drops forwarded traffic by default unless explicitly allowed.

```bash
sudo awg-quick up awg0      # start
sudo awg-quick down awg0    # stop
sudo awg                    # status
```

## Adding a peer

Works the same for a phone or a laptop, just change `PEER_NAME` and bump the octet. Pulls the obfuscation parameters (`Jc`, `Jmin`, `Jmax`, `S1`, `S2`, `H1`-`H4`, `I1`, `HeaderProtectionKey`, `ContentPaddingAddition`) straight from the server config instead of copying them by hand, since those have to match exactly between the server and every peer or the handshake fails.

```bash
PEER_NAME="laptop"        # or "mobile", "tablet", whatever
ENDPOINT_PORT="443"
CONF=/etc/amnezia/amneziawg/awg0.conf

# next free octet = highest one already used + 1
PEER_OCTET=$(( $(sudo grep -oP 'AllowedIPs = 10\.99\.99\.\K[0-9]+' "$CONF" | sort -n | tail -1) + 1 ))

CLIENT_PRIV=$(awg genkey)
CLIENT_PUB=$(echo "$CLIENT_PRIV" | awg pubkey)
SERVER_PUB=$(sudo awg show awg0 public-key)
OBFUSCATION_PARAMS=$(sudo grep -E "^(Jc|Jmin|Jmax|S1|S2|S3|S4|H1|H2|H3|H4|I1|HeaderProtectionKey|ContentPaddingAddition) " "$CONF")

# stop before touching the server if the mandatory key is missing
if ! echo "$OBFUSCATION_PARAMS" | grep -q "^HeaderProtectionKey"; then
  echo "HeaderProtectionKey not found in $CONF, aborting"
  exit 1
fi

sudo awg set awg0 peer "$CLIENT_PUB" allowed-ips 10.99.99.${PEER_OCTET}/32
echo -e "\n[Peer]\nPublicKey = $CLIENT_PUB\nAllowedIPs = 10.99.99.${PEER_OCTET}/32" | sudo tee -a "$CONF" > /dev/null

OUT="$HOME/${PEER_NAME}-client.conf"
cat > "$OUT" << EOF
[Interface]
PrivateKey = $CLIENT_PRIV
Address = 10.99.99.${PEER_OCTET}/32
# Points to AdGuard Home on the host LAN for internal resolution
DNS = YOUR_DNS_IP
$OBFUSCATION_PARAMS

[Peer]
PublicKey = $SERVER_PUB
Endpoint = YOUR_DOMAIN.duckdns.org:${ENDPOINT_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
chmod 600 "$OUT" #only read and write for the root user
echo "wrote $OUT (octet $PEER_OCTET)"
```

For mobile, import the resulting `.conf` into the AmneziaWG app directly, or convert it to a QR code with `qrencode` so you don't have to transfer a file. For a laptop, locally send it and either import it through the AmneziaWG desktop client or bring it up directly with `sudo awg-quick up ~/laptop-client.conf`.

Delete the generated `.conf` off the server once it's transferred, it contains the peer's private key and has no reason to sit there afterward.
