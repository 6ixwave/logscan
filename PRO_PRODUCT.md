# logscan Pro

## Features (beyond free logscan-cli)
- Multi-file: `logscan dir/ --recursive` (scan entire log directory)
- Grafana export: `logscan app.log --grafana` (Prometheus/Grafana metrics)
- Alerting: `logscan --alert "ERROR count > 100" --webhook <url>`
- GUI: `logscan --gui` (Tkinter dashboard, no install)
- Custom parsers: `logscan --add-parser myformat.json`
- Scheduled scan: `logscan --cron "*/5 * * * *"` (daemon mode)
- Report: `logscan app.log --report --format pdf`

## vs Free
| | Free (pip) | Pro |
|---|---|---|
| Files | Single | Multi + recursive |
| Export | Terminal | Grafana, JSON, PDF |
| Alerts | No | Webhook, email |
| GUI | No | Tkinter dashboard |
| Custom parsers | No | JSON config |
| Daemon | No | --cron mode |

## Price
$5 one-time. Updates free.

## Install
pip install logscan-pro  (or download .whl from Gumroad)
