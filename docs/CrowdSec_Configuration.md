# CrowdSec

Parses host and container logs to detect malicious activity and bans offending IPs at the firewall level. Monitors SSH auth logs, Docker container logs, and HTTP traffic.

Running v1.7.8.

```bash
sudo cscli decisions list                  # active bans
sudo cscli decisions delete -i [IP]        # remove a ban
sudo cscli decisions add -i [IP]           # manual ban
sudo cscli metrics                         # scenario hit rates
sudo cscli hub list                        # installed parsers and scenarios
```

`cscli metrics` is the most useful for tuning. It surfaces both false positives (own IP flagged after a VPN reconnect) and scenarios that aren't triggering when they should.
