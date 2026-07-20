# Samba (Family File Storage)

Network drive for the family, replacing an attempt at running this through Nextcloud. Nextcloud worked but for what this actually needed, a few private folders with per-person storage limits, it meant carrying a database, a cache layer, and a reverse proxy dependency for something a plain network share does natively. Runs on the host directly rather than in Docker, since per-user Linux accounts and filesystem quotas are what make the permission and quota model work, not something that benefits from being containerized.

## Setup

```bash
sudo pacman -S samba
```

One system account per family member, no shell access, Samba-only:
```bash
sudo useradd -M -s /usr/sbin/nologin PERSON
sudo smbpasswd -a PERSON
```

`smbpasswd` needs `/etc/samba/smb.conf` to already exist, even minimally, or it fails with "Can't load /etc/samba/smb.conf". Create a bare-bones one first if the package didn't ship one:
```bash
sudo mkdir -p /etc/samba
sudo tee /etc/samba/smb.conf << 'EOF'
[global]
   workgroup = WORKGROUP
   server string = Homelab Family Storage
   security = user
   map to guest = never
EOF
```

If `testparm` then errors with a generic "Error loading services" and no detail, check the file's permissions before anything else, it needs to be world-readable:
```bash
sudo chmod 644 /etc/samba/smb.conf
```

## Storage and quotas (Btrfs)

The storage drive here is Btrfs, which handles quotas completely differently from ext4/XFS. There's no `usrquota` fstab option or `quota-tools` involved, Btrfs uses its own qgroup system, and quotas only apply at the subvolume level, not to a plain directory. Each person's folder has to actually be a Btrfs subvolume, not just a `mkdir`'d folder, or there's nothing for a qgroup to attach to.

Enable quotas on the filesystem, once:
```bash
sudo btrfs quota enable /mnt/data
```

Create each person's folder as a subvolume instead of a plain directory:
```bash
sudo btrfs subvolume create /mnt/data/family-files/PERSON
sudo chown PERSON:PERSON /mnt/data/family-files/PERSON
sudo chmod 2770 /mnt/data/family-files/PERSON
```
The `2` sets the setgid bit, so new files created inside inherit the folder's group automatically.

Set the limit per subvolume, single hard ceiling, no soft/hard split like traditional quotas:
```bash
sudo btrfs qgroup limit 20G /mnt/data/family-files/PERSON
```

Same pattern works for a shared folder if it should have its own cap too, not just the private ones.

After creating subvolumes or setting limits, Btrfs may report `WARNING: qgroup data inconsistent, rescan recommended`. Clear it with:
```bash
sudo btrfs quota rescan /mnt/data
```
If a rescan is already running, a second call fails with `ERROR: quota rescan failed: Operation now in progress`, that's not a failure, just wait a few seconds and check again without re-triggering it:
```bash
sudo btrfs qgroup show -pcre /mnt/data
```
That shows every qgroup, its current usage, and its limit in one table.

## Config

Add the share blocks below `[global]` in `/etc/samba/smb.conf`:
```ini
[person1]
   path = /mnt/data/family-files/person1
   valid users = person1
   read only = no
   browsable = yes

[shared]
   path = /mnt/data/family-files/shared
   valid users = person1, person2, user
   read only = no
   browsable = yes
```

`valid users` on each share is the actual permission boundary, each person only sees their own private folder plus the shared one, enforced by Samba itself, not a UI setting.

Validate before restarting, catches a typo before it takes down the running service:
```bash
sudo testparm
```

## Running it

```bash
sudo systemctl enable --now smb nmb
```

Confirm the shares are actually being served, from the server itself:
```bash
smbclient -L localhost -U person1
```

Scoped to LAN and VPN only, same trust boundary as the rest of the stack, never exposed publicly:
```bash
sudo ufw allow from 192.168.0.0/24 to any port 445
sudo ufw allow from 10.99.99.0/24 to any port 445
```

## Connecting

Windows: `\\192.168.0.109\person1` in File Explorer.
Mac: Finder → Go → Connect to Server → `smb://192.168.0.109/person1`.
Linux: `smb://192.168.0.109/person1` in the file manager, or `smbclient //192.168.0.109/person1 -U person1` from a terminal.

Both prompt for the Samba username and password set with `smbpasswd`, separate from any system login. Files opened directly from the mounted share edit in place over the network, no download-edit-reupload step, that part works the same as any local file.

Worth testing that `valid users` is actually being enforced, not just present in the config, by logging in as one person and confirming they can't browse into someone else's share.
