# logscan-cli

Lightweight log file analyzer and parser. **Zero external dependencies** (stdlib only).

## Install

```bash
pip install logscan-cli
```

Or grab the wheel from [GitHub Releases](https://github.com/6ixwave/logscan/releases/tag/v0.1.0).

## Quick start

```bash
# Full report
logscan /var/log/app.log

# Filter by level
logscan app.log --level ERROR CRITICAL

# Regex filter
logscan app.log --pattern "timeout|connection"

# JSON output (for scripts/dashboards)
logscan app.log --json

# Limit lines
logscan huge.log --lines 100000

# From stdin
cat app.log | logscan -
```

## Python API

```python
from logscan import LogParser, LogAnalyzer

parser = LogParser()
entries = parser.parse_file("/var/log/syslog")

analyzer = LogAnalyzer(entries)
report = analyzer.full_report()
print(report.level_counts)       # {'INFO': 120, 'ERROR': 5, ...}
print(report.error_rate)         # 0.038

errors = analyzer.filter_by_level("ERROR", "CRITICAL")
spikes = analyzer.spike_detection(threshold=3.0)
```

## Supported formats

| Format | Example |
|--------|---------|
| ISO timestamp | `2026-11-09T10:00:01 INFO msg` |
| Syslog | `Nov  9 10:00:01 host app: msg` |
| Apache/Nginx | `09/Nov/2026:10:00:01 +0000 GET /` |
| JSON Lines | `{"ts":"...","level":"ERROR","msg":"..."}` |
| Custom regex | `LogParser(pattern=r"(?P<level>\w+)\s+(?P<message>.*)")` |

## CLI options

| Flag | Description |
|------|-------------|
| `--level L1 L2` | Filter by log level(s) |
| `--pattern RX` | Regex filter on message |
| `--top N` | Top-N items (default 10) |
| `--json` | JSON output |
| `--lines N` | Max lines to parse |
| `--quiet` | Report only, no sample entries |

## Features

- **Parse**: syslog, nginx, Apache, JSON Lines, custom regex
- **Analyze**: error rate, level distribution, top messages, spike detection
- **Report**: human-readable terminal output with stats
- **Zero deps**: pure Python stdlib, works on 3.10+
- **Cross-platform**: Linux, macOS, Windows

## License

MIT вЂ” use it anywhere, even commercially.

## Related

- [Procedural Material Pack](https://github.com/6ixwave/procedural-material-pack) — 12 free PBR materials for Blender (CC0)

