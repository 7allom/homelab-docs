#!/bin/bash

TOKEN="YOUR_DUCKDNS_TOKEN"
DOMAIN="YOUR_DUCKDNS_DOMAIN"

# Ask ifconfig.me what your public IPs are
MY_IPV4=$(curl -s -4 ifconfig.me)
MY_IPV6=$(curl -s -6 ifconfig.me)

# Fire the API request to update records
if [ -n "$MY_IPV4" ] && [ -n "$MY_IPV6" ]; then
    curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${MY_IPV4}&ipv6=${MY_IPV6}" > /dev/null
fi
