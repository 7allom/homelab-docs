# AdGuard Home

Handles local DNS resolution and network-wide ad blocking.

Port 53 is bound directly to the host's static IP (`192.168.0.109`) for both TCP and UDP, keeping DNS traffic off Docker's internal routing entirely. The web UI runs on 8083 rather than the default 80, since Caddy needs 80 available for Let's Encrypt. Port 3000 serves the initial setup wizard and stays open for re-provisioning if needed.

All three ports are pinned to the host IP rather than published to `0.0.0.0`, so only traffic on the intended interface can reach them.

> **Note:** DoT (`tls://`) is not used as upstream DNS. ISPs drop persistent connections on port 853, causing `connection timed out` errors and severe DNS lag. DoH (port 443) and DoQ (UDP) bypass this TCP filtering.

## Boot Order & Systemd Dependencies

> **The Problem:** I rebooted the server and come back to a completely dead internet connection. Checking the logs, AdGuard Home was crashing on startup with exit code `127` (Command Not Found). 

It turned out to be a startup race condition. The Docker daemon was starting up before my primary drive was actually mounted. Because of this, Docker was passing an empty directory into the AdGuard container, which is why it couldn't find its own executable and threw the 127 error.

The permanent fix is to tell systemd to hold off on starting Docker until the specific storage directories are actually ready. I also added my secondary media drives to this rule so the rest of the media stack doesn't face the same issue.

Create an override for the Docker service:
```bash
sudo systemctl edit docker.service
```

Drop this block at the very top of the file:
```ini
[Unit]
Wants=network-online.target
After=network-online.target
RequiresMountsFor=/home/YOUR_USER/containers /mnt/data /mnt/Vault
```

- `network-online.target`: Ensures the host actually has its network connection established before bringing up the containers.
- `RequiresMountsFor`: Forces Docker to wait until the primary container directory (`/home/YOUR_USER/containers`) is fully mounted, completely eliminating the AdGuard Home exit code 127. The media drives (`/mnt/data` and `/mnt/Vault`) are included here simply to protect the rest of the media stack from the same exact failure.

Reload the daemon to apply it:
```bash
sudo systemctl daemon-reload
```
