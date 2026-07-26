# CrowdSec → Ntfy Alerts

CrowdSec's HTTP notification plugin posts to ntfy through the same VPN-gated Caddy route as everything else, not a direct container port. Ban decisions trigger a push notification to a mobile device in near real time.

## HTTP plugin config
`/etc/crowdsec/notifications/http.yaml`:

```yaml
type: http
name: local_ntfy_alert
log_level: info
url: https://ntfy.YOUR_DOMAIN.duckdns.org/YOUR_NTFY_TOPIC
method: POST
headers:
  Title: "CrowdSec: Threat Neutralized"
  Tags: "shield,warning"
  Priority: "high"
format: |
  {{range . -}}
  {{$alert := . -}}
  THREAT NEUTRALIZED

  Reason: {{$alert.Scenario}}
  Hits: {{$alert.EventsCount}} attempts
  Time: {{$alert.CreatedAt}}
  Node: {{$alert.MachineID}}

  {{if $alert.Source -}}
  IP: {{$alert.Source.IP}}
  Org: {{if $alert.Source.AsName}}{{$alert.Source.AsName}}{{else}}Unknown{{end}}
  Country: {{if $alert.Source.Cn}}{{$alert.Source.Cn}}{{else}}Unknown{{end}}
  GPS: {{if $alert.Source.Latitude}}{{$alert.Source.Latitude}}, {{$alert.Source.Longitude}}{{else}}Unknown{{end}}
  {{else -}}
  IP: Unknown (Test Payload)
  {{end -}}

  {{range $alert.Decisions -}}
  Action: {{.Type}} for {{.Duration}}
  {{end -}}
  {{end -}}
```

CrowdSec enriches each alert with GeoIP data (org, country, coordinates) when it's available, the template surfaces that alongside the actual ban reason and hit count rather than just a bare IP address.

## Profile trigger
`profiles.yaml` needs a matching entry to actually invoke the notification plugin on ban decisions; the plugin config alone doesn't fire without it. Current version in `config/crowdsec/profiles.yaml`.

