# Routine Maintenance

CachyOS is a rolling-release distribution and container images update frequently, so the stack requires regular, deliberate upkeep.

## Host updates
Confirm no active downloads or backups are running, then:
```bash
sudo pacman -Syu
```
Reboot (`sudo reboot`) if the update includes a kernel or systemd change, common on CachyOS, since those require a restart to take effect.

## Container updates
Independent of host updates:
```bash
cd ~/containers
docker compose pull
docker compose up -d
```
Per-container downtime is limited to the few seconds it takes to swap images.

## Bot instance exception
`bot-instance` is built locally rather than pulled from a registry, so `docker compose pull` has no effect on it. Rebuilding after a code change requires `docker compose up -d --build bot-instance`.
