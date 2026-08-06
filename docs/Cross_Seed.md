# Cross-Seed

Finds the same content already sitting in qBittorrent on other trackers and adds it there too, without downloading anything twice. It searches Prowlarr's indexers for a match against torrents already in the client, then hardlinks the shared data and injects the matching torrent, so the same files end up seeding across multiple trackers from a single copy on disk.

## Config

```js
module.exports = {
  torznab: [
    "http://prowlarr:9696/1/api?apikey=YOUR_PROWLARR_API_KEY",
    "http://prowlarr:9696/2/api?apikey=YOUR_PROWLARR_API_KEY",
  ],
  sonarr: ["http://sonarr:8989/?apikey=YOUR_SONARR_API_KEY"],
  radarr: ["http://radarr:7878/?apikey=YOUR_RADARR_API_KEY"],
  torrentClients: [
    "qbittorrent:http://qbittorrent:8090",
  ],
  dataDirs: [
    "/vault/torrents",
    "/data/torrents",
    "/personal/torrents",
  ],
  linkDirs: ["/data/cross-seeds", "/personal/cross-seeds", "/vault/cross-seeds"],
  linkType: "hardlink",
  matchMode: "partial",
  fuzzySizeThreshold: 0.02,
};
```

`torznab` only searches whatever indexers are listed here. Adding an indexer in Prowlarr doesn't automatically add it to cross-seed, the URL (with that indexer's specific ID) has to be copied over and added to this list manually, and cross-seed restarted to pick it up.

`dataDirs` and `linkDirs` list all three storage mounts, not just one. qBittorrent saves torrents across `/data`, `/personal`, and `/vault` depending on category, and cross-seed can only match and hardlink what it can actually see at the same paths qBittorrent uses. Hardlinks also can't cross filesystem boundaries, so each mount needs its own `linkDirs` entry on that same filesystem, a hardlink target on the wrong drive either fails or silently falls back to a full copy.

`matchMode: "partial"` allows a match even if small extras (`.nfo`, `.srt`, samples) differ between releases, common between trackers that repackage things slightly differently. The large shared file still gets hardlinked instantly either way, only the mismatched small files get freshly downloaded to fill the gap. `fuzzySizeThreshold` (0.02, the default) bounds how much total size variance is tolerated before two releases are treated as genuinely different content rather than a partial match, this is a proportional limit, not a fixed size, so it scales with the torrent's total size.

## Bringing it up

```bash
mkdir -p ~/containers/cross-seed/config
docker compose run -v ~/containers/cross-seed/config:/config cross-seed gen-config
```
Edit the generated `config.js` with the settings above, then:
```bash
cd ~/containers
docker compose up -d cross-seed
docker compose logs --tail 20 cross-seed
```
A clean startup validates the config, logs into the torrent client, indexes existing torrents for reverse lookup, and starts the RSS and search schedulers.

## Private trackers behind Cloudflare

Some indexers sit behind Cloudflare and return a `403 Forbidden` on every request unless routed through FlareSolverr first. Adding the indexer to Prowlarr alone doesn't route it through FlareSolverr automatically, that has to be set up explicitly:

1. Prowlarr → Settings → Indexer Proxies → add a FlareSolverr proxy pointing at `http://flaresolverr:8191`, with a tag.
2. On the affected indexer itself, add that same tag under its own Tags field.

Without the tag matching on both sides, requests go out directly, Cloudflare blocks them, and it looks like a login or credentials problem when it isn't.
