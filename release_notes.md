# logscan v0.1.0

Zero-dependency log file analyzer and parser.

## Features
- Parse: syslog, nginx, Apache, JSON Lines, custom regex
- Analyze: error rate, level distribution, top messages, spike detection
- CLI: `logscan /var/log/app.log --level ERROR --top 10`

## Install
``
pip install logscan
``

## Quick start
``
logscan server.log --top 5
logscan app.log --level ERROR --pattern "timeout|refused"
logscan json.log --format json
``

## License
MIT
