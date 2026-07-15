# DuckDNS Dynamic IP Automation

Keeps `YOUR_DOMAIN.duckdns.org` pointed at the current public IP, which the ISP rotates periodically. Required for AmneziaWG to handshake successfully from outside the LAN.

## Update script
`/usr/local/bin/duckdns.sh`, `chmod 700`:

```bash
#!/bin/bash

TOKEN="XXXXX"
DOMAIN="YOUR_DOMAIN"

MY_IPV4=$(curl -s -4 ifconfig.me)
MY_IPV6=$(curl -s -6 ifconfig.me)

if [ -n "$MY_IPV4" ] && [ -n "$MY_IPV6" ]; then
    curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${MY_IPV4}&ipv6=${MY_IPV6}" > /dev/null
fi
```

## Timer
Runs once, one minute after boot, then every 5 minutes thereafter (`duckdns.service` / `duckdns.timer`).
