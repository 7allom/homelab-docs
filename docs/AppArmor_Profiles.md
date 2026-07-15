# AppArmor Profiles

Mandatory access control at the host level, particularly relevant for containers running `network_mode: host` (the Discord bot), which bypass Docker's usual network isolation.

Permission errors that don't trace back to application logs are usually an AppArmor denial, worth checking first when debugging host-networked containers.

```bash
sudo aa-status                              # loaded profiles, enforce/complain state
sudo aa-complain /etc/apparmor.d/[profile]  # log violations without blocking, for debugging
sudo aa-enforce /etc/apparmor.d/[profile]   # restore enforcement
```
