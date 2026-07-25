# Monitoring (Prometheus, Grafana, Alloy)

Metrics and dashboards for the stack: host resources, per-container usage, and Caddy's reverse proxy traffic.

Prometheus stores the time-series data, Grafana turns it into dashboards. Alloy is the collector in between, it bundles node_exporter and cAdvisor internally as components, so host and container metrics both come from one container instead of running them separately, and pushes everything to Prometheus rather than getting scraped.

## Why push instead of scrape

Prometheus normally pulls metrics on its own schedule. Alloy changes that here, it collects and pushes to Prometheus's write endpoint instead. Prometheus needs an extra flag to accept that:
```
--web.enable-remote-write-receiver
```
Without it, pushed data just gets rejected.

## Alloy config

`${DOCKER_ROOT}/alloy/config/config.alloy`:
```alloy
prometheus.exporter.cadvisor "cadvisor" {
  docker_host = "unix:///var/run/docker.sock"
  storage_duration = "5m"
}

prometheus.scrape "docker_scraper" {
  targets    = prometheus.exporter.cadvisor.cadvisor.targets
  forward_to = [prometheus.remote_write.prometheus.receiver]
}

prometheus.exporter.unix "host" {
  procfs_path    = "/host/proc"
  sysfs_path     = "/host/sys"
  rootfs_path    = "/rootfs"
  udev_data_path = "/host/run/udev/data"
}

prometheus.scrape "host_scraper" {
  targets    = prometheus.exporter.unix.host.targets
  forward_to = [prometheus.remote_write.prometheus.receiver]
}

prometheus.remote_write "prometheus" {
  endpoint {
    url = "http://prometheus:9090/api/v1/write"
  }
}
```

The `*_path` values need to line up with whatever the container's volumes actually mount to, same as any bind-mounted exporter.

## Caddy metrics

Caddy has a built-in `/metrics` endpoint, no plugin needed:
```caddyfile
{
    admin 0.0.0.0:2019
    servers {
        metrics {
            per_host
        }
    }
}
```
`per_host` breaks metrics down by subdomain instead of lumping everything into one number. The `admin 0.0.0.0:2019` line matters more than it looks, Caddy's admin API binds to localhost only by default, so without this, nothing else on the network can reach it even with the port published.

Port 2019 is the full admin API, not just metrics, so it's reachable by anything on the same Docker network, not published to the host or routed publicly.

## Prometheus config

`${DOCKER_ROOT}/prometheus/config/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'caddy'
    static_configs:
      - targets: ['caddy:2019']
```
Only Caddy needs a scrape job here, host and container metrics come in through Alloy's push instead.

## Permissions

Both Prometheus and Grafana run as non-root inside their containers, and both crash on startup if the host folders they're mounted to aren't accessible to those users.

Prometheus's config file needs to be world-readable, and every folder leading to it needs to be traversable too:
```bash
chmod 644 ~/containers/prometheus/config/prometheus.yml
chmod o+x ~/containers/prometheus
chmod o+x ~/containers/prometheus/config
```

Prometheus's data folder needs to be owned by its container's user (UID `65534`):
```bash
sudo chown -R 65534:65534 ~/containers/prometheus/data
```

Grafana's data folder needs to be owned by its container's user (UID `472`):
```bash
sudo chown -R 472:472 ~/containers/grafana/data
```

## Bringing it up

```bash
mkdir -p ~/containers/prometheus/{config,data}
mkdir -p ~/containers/grafana/data
mkdir -p ~/containers/alloy/config
# save prometheus.yml and config.alloy into their folders, then set permissions as above

cd ~/containers
docker compose up -d prometheus grafana alloy
docker compose ps
```

In Grafana, add Prometheus as a data source at `http://prometheus:9090`, then import dashboards by ID: `1860` (Node Exporter Full), `12486` (alternative host dashboard), `19908` (cAdvisor/Docker), `25216` (Caddy).

`1860` occasionally shows blank panels even when the metrics are actually there, a stale variable selection rather than missing data. `12486` is a solid fallback if it doesn't.
