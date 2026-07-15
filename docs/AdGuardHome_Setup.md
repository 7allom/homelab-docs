# AdGuard Home

Handles local DNS resolution and network-wide ad blocking.

Port 53 is bound directly to the host's static IP (`192.168.0.109`) for both TCP and UDP, keeping DNS traffic off Docker's internal routing entirely. The web UI runs on 8083 rather than the default 80, since Caddy needs 80 available for Let's Encrypt. Port 3000 serves the initial setup wizard and stays open for re-provisioning if needed.

All three ports are pinned to the host IP rather than published to `0.0.0.0`, so only traffic on the intended interface can reach them.
