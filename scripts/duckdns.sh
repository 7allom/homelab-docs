#!/bin/bash

TOKEN="YOUR_DUCKDNS_TOKEN"
DOMAIN="YOUR_DOMAIN"

# 1. Fetch public IPv4 only
MY_IPV4=$(curl -s -4 ifconfig.me)

# 2. Push IPv4 only (omitting ipv6 ensures no AAAA record is updated)
if [ -n "$MY_IPV4" ]; then
    curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${MY_IPV4}" > /dev/null
fi
