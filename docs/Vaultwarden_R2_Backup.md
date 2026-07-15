# Vaultwarden Encrypted R2 Backup

Nightly, zero-downtime, end-to-end encrypted backup of the Vaultwarden database to Cloudflare R2. Uses `sqlite3` for the live snapshot, `rclone` for encryption and transfer, and `systemd` for scheduling.

- Data path: `~/containers/vaultwarden/data`
- R2 bucket: `user-vault-backups`
- Rclone config: `~/.config/rclone/rclone.conf`

## Rclone configuration
Two layers: a base connection to R2, wrapped in a local encryption layer.

`[cloudflare_s3]` connects via the S3 API. Requires `no_check_bucket = true`, since the R2 token has Object Read/Write permissions only, not bucket-list. Without this setting, rclone attempts to verify the bucket exists before uploading and fails with a 403.

`[vault_secure]` is the `crypt` remote wrapping `cloudflare_s3:user-vault-backups`. Both filenames and contents are encrypted locally with AES-256 before leaving the server.

The encryption password and salt for `vault_secure` are stored in Vaultwarden itself and recorded separately offline.

## Backup script
`/usr/local/bin/backup_vault.sh`, `chmod 700`, root-only:

```bash
#!/bin/bash

VAULT_DATA_DIR="~/containers/vaultwarden/data"
BACKUP_TEMP_DIR="/tmp/vault_backup_tmp"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# snapshots the live sqlite database without stopping the container,
# copies attachments and config, compresses, and hands off to rclone
```

Live snapshotting was chosen deliberately over stopping the container. Vaultwarden's uptime matters more than perfect snapshot consistency, and SQLite's online backup API handles concurrent access safely.
