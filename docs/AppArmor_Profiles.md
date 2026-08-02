# AppArmor Profiles

Mandatory access control at the host level, particularly relevant for containers running `network_mode: host` (the Discord bot), which bypass Docker's usual network isolation.

Permission errors that don't trace back to application logs are usually an AppArmor denial, worth checking first when debugging host-networked containers.

```bash
sudo aa-status                              # loaded profiles, enforce/complain state
sudo aa-complain /etc/apparmor.d/[profile]  # log violations without blocking, for debugging
sudo aa-enforce /etc/apparmor.d/[profile]   # restore enforcement
```

## Local overrides for host services

Same principle applies to any native host service running on a non-standard path, not just Samba. If a service's own profile only covers standard locations, moving its data to somewhere like `/mnt/data` puts it outside what the profile allows, blocked regardless of the actual filesystem permissions.

Never edit the profile in `/etc/apparmor.d/` directly, package updates overwrite it. Exceptions go in the service's override file under `/etc/apparmor.d/local/` instead, which survives updates:
```bash
sudo nano /etc/apparmor.d/local/usr.sbin.smbd
```
Add the required paths inside the file, for example:
```text
/mnt/data/ r,
/mnt/data/** lrwk,
```
Then reload:
```bash
sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.smbd
```
