# CrowdSec → Ntfy Alerts

CrowdSec's HTTP notification plugin posts directly to the local `ntfy` container (`http://localhost:8095`) rather than relying on a third-party alerting service. Ban decisions trigger a push notification to a mobile device in near real time.

## HTTP plugin config
`/etc/crowdsec/notifications/http.yaml`:

```yaml
type: http
name: http_default
format: |
  {
    "topic": "YOUR_NTFY_TOPIC",
    "title": "CrowdSec Alert",
    "message": "Ban triggered for IP: {{.Source.IP}} based on scenario: {{.Scenario}}",
    "priority": 4,
    "tags": ["warning", "skull"]
  }
url: http://localhost:8095/
method: POST
headers:
  Content-Type: "application/json"
```

## Profile trigger
`profiles.yaml` needs a matching entry to actually invoke the notification plugin on ban decisions; the plugin config alone doesn't fire without it. Current version in `config/crowdsec/profiles.yaml`.
