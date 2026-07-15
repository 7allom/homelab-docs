# Docker Configuration Backup

Weekly encrypted backup of `~/containers` (the full compose setup, including `docker-compose.yml`, per-service configuration, and `.env` files) to Google Drive.

Since the `.env` files contain live API keys and tokens, the archive is encrypted locally with `rclone crypt` before leaving the server. Cache directories are excluded to keep archive size reasonable.

- Source: `~/containers`
- Destination: `config_secure:`, an rclone crypt remote wrapping `gdrive:ServerBackups/`
- Rclone config: `~/.config/rclone/rclone.conf`

## Systemd units

`/etc/systemd/system/container-backup.service`:
```ini
[Unit]
Description=Weekly Docker Containers Configuration Backup
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/bash -c '/usr/bin/tar -czf /home/user/containers_backup.tar.gz --exclude="*/cache" /home/user/containers && /usr/bin/rclone copy /home/user/containers_backup.tar.gz config_secure: --update --config="/home/user/.config/rclone/rclone.conf"'

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/container-backup.timer`:
```ini
[Unit]
Description=Run Weekly Docker Containers Configuration Backup Timer

[Timer]
OnCalendar=Sun *-*-* 00:00:00
Persistent=true
Unit=container-backup.service

[Install]
WantedBy=timers.target
```

The service uses absolute paths rather than `~`, since it runs as root and `~` would resolve incorrectly in that context.

## Commands
```bash
sudo systemctl start container-backup.service                       # run manually
sudo journalctl -u container-backup.service -n 20 --no-pager         # check last run
sudo rclone --config ~/.config/rclone/rclone.conf ls config_secure:  # verify upload

# restore
sudo rclone --config ~/.config/rclone/rclone.conf copy config_secure:containers_backup.tar.gz ~/
```

The `crypt` wrapper matters here specifically because this archive carries live credentials (`.env` files with tokens and API keys) to a third-party cloud account, so encrypting locally before upload is non-negotiable.
