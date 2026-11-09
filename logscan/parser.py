"""Log file parsing module for logscan."""

import re
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional, List, Dict


@dataclass
class LogEntry:
    """A single parsed log line."""
    timestamp: Optional[datetime] = None
    level: str = "INFO"
    message: str = ""
    raw: str = ""
    line_number: int = 0
    source: str = ""
    extra: Dict[str, str] = field(default_factory=dict)


# ─── Timestamp patterns ───────────────────────────────────────────────────
_TS_PATTERNS = [
    (re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"),
     lambda m: datetime.fromisoformat(m.group(1).replace("T", " "))),
    (re.compile(r"([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})"),
     lambda m: datetime.strptime(f"2026 {m.group(1)} {m.group(2)} {m.group(3)}", "%Y %b %d %H:%M:%S")),
    (re.compile(r"(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})"),
     lambda m: datetime.strptime(m.group(1), "%d/%b/%Y:%H:%M:%S")),
]

_LEVEL_RE = re.compile(
    r"\b(DEBUG|TRACE|INFO|NOTICE|WARNING|WARN|ERROR|ERR|CRITICAL|FATAL|SEVERE|ALERT|EMERG)\b",
    re.IGNORECASE,
)
_LEVEL_MAP = {
    "TRACE": "TRACE", "DEBUG": "DEBUG", "INFO": "INFO",
    "NOTICE": "NOTICE", "WARN": "WARNING", "WARNING": "WARNING",
    "ERR": "ERROR", "ERROR": "ERROR", "CRITICAL": "CRITICAL",
    "FATAL": "FATAL", "SEVERE": "SEVERE", "ALERT": "ALERT", "EMERG": "EMERG",
}


class LogParser:
    """Parse log files into structured LogEntry objects.

    Supports plain text, syslog, nginx/apache, JSON lines, custom regex.
    """

    def __init__(self, pattern: Optional[str] = None, timestamp_format: Optional[str] = None):
        self.custom_pattern = re.compile(pattern) if pattern else None
        self.custom_ts_format = timestamp_format

    def parse_file(self, path: str, encoding: str = "utf-8",
                   max_lines: Optional[int] = None) -> List[LogEntry]:
        entries = []
        with open(path, "r", encoding=encoding, errors="replace") as f:
            for i, line in enumerate(f, 1):
                if max_lines and i > max_lines:
                    break
                line = line.rstrip("\n\r")
                if not line.strip():
                    continue
                entries.append(self.parse_line(line, i, source=os.path.basename(path)))
        return entries

    def parse_stream(self, lines: Iterator[str], source: str = "<stream>") -> Iterator[LogEntry]:
        for i, line in enumerate(lines, 1):
            line = line.rstrip("\n\r")
            if not line.strip():
                continue
            yield self.parse_line(line, i, source=source)

    def parse_line(self, line: str, line_number: int = 0, source: str = "") -> LogEntry:
        entry = LogEntry(raw=line, line_number=line_number, source=source)

        if self.custom_pattern:
            m = self.custom_pattern.search(line)
            if m:
                gd = m.groupdict()
                entry.message = gd.get("message", line)
                if gd.get("level"):
                    entry.level = _LEVEL_MAP.get(gd["level"].upper(), gd["level"].upper())
                if gd.get("timestamp"):
                    entry.timestamp = self._parse_ts(gd["timestamp"])
                for k, v in gd.items():
                    if k not in ("timestamp", "level", "message"):
                        entry.extra[k] = v
                return entry

        if line.strip().startswith("{"):
            try:
                import json
                obj = json.loads(line)
                entry.message = obj.get("message", obj.get("msg", str(obj)))
                entry.level = _LEVEL_MAP.get(str(obj.get("level", "INFO")).upper(), "INFO")
                ts = obj.get("timestamp") or obj.get("time") or obj.get("@timestamp")
                if ts:
                    entry.timestamp = self._parse_ts(str(ts))
                for k, v in obj.items():
                    if k not in ("message", "msg", "level", "timestamp", "time", "@timestamp"):
                        entry.extra[k] = str(v)
                return entry
            except (json.JSONDecodeError, ImportError):
                pass

        entry.timestamp = self._extract_timestamp(line)
        lm = _LEVEL_RE.search(line)
        if lm:
            entry.level = _LEVEL_MAP.get(lm.group(1).upper(), lm.group(1).upper())
        entry.message = line
        return entry

    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        for pat, fn in _TS_PATTERNS:
            m = pat.search(line)
            if m:
                try:
                    return fn(m)
                except (ValueError, TypeError):
                    continue
        return None

    def _parse_ts(self, ts_str: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            pass
        for pat, fn in _TS_PATTERNS:
            m = pat.search(ts_str)
            if m:
                try:
                    return fn(m)
                except (ValueError, TypeError):
                    continue
        return None
