# DuckDNS Dynamic IP Automation

Keeps `YOUR_DOMAIN.duckdns.org` pointed at the current public IP, which the ISP rotates periodically. Required for AmneziaWG to handshake successfully from outside the LAN.

## Update script
`/usr/local/bin/duckdns.sh`, `chmod 700`:

```bash
TOKEN="YOUR_DUCKDNS_TOKEN"
DOMAIN="YOUR_DOMAIN"

# 1. Fetch public IPv4 only
MY_IPV4=$(curl -s -4 ifconfig.me)

# 2. Push IPv4 only (omitting ipv6 ensures no AAAA record is updated)
if [ -n "$MY_IPV4" ]; then
    curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${MY_IPV4}" > /dev/null
fi
```
> I noticed that letting DuckDNS publish IPv6 (`AAAA`) records caused operating systems to favor IPv6 routing, which conflicted with the AWG virtual interface and caused dropped handshakes.
## Timer
Runs once, one minute after boot, then every 5 minutes thereafter (`duckdns.service` / `duckdns.timer`).
