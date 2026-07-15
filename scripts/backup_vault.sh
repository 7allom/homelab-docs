#!/bin/bash

# Configuration paths
VAULT_DATA_DIR="~/containers/vaultwarden/data" # Adjust to match your actual vaultwarden /data path
BACKUP_TEMP_DIR="/tmp/vault_backup_tmp"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_NAME="vaultwarden_backup_${DATE}.tar.gz"

# Create clean workspace
rm -rf "$BACKUP_TEMP_DIR"
mkdir -p "$BACKUP_TEMP_DIR"

# Safely snapshot the live SQLite database without stopping the container
sqlite3 "$VAULT_DATA_DIR/db.sqlite3" ".backup '$BACKUP_TEMP_DIR/db.sqlite3'"

# Copy matching encryption keys, attachments, and configuration files
cp "$VAULT_DATA_DIR/config.json" "$BACKUP_TEMP_DIR/" 2>/dev/null
if [ -d "$VAULT_DATA_DIR/attachments" ]; then
    cp -r "$VAULT_DATA_DIR/attachments" "$BACKUP_TEMP_DIR/"
fi

# Compress the snapshot into a single archive
tar -czf "/tmp/$BACKUP_NAME" -C "$BACKUP_TEMP_DIR" .

# Encrypt locally and sync to Cloudflare R2 via Rclone
rclone --config ~/.config/rclone/rclone.conf copy "/tmp/$BACKUP_NAME" vault_secure:

# Cleanup local temporary files
rm -rf "$BACKUP_TEMP_DIR"
rm "/tmp/$BACKUP_NAME"
