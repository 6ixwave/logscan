"""Log analysis module for logscan."""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from .parser import LogEntry


@dataclass
class AnalysisReport:
    total_lines: int = 0
    time_range: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    level_counts: Dict[str, int] = field(default_factory=dict)
    top_errors: List[Tuple[int, str]] = field(default_factory=list)
    top_sources: List[Tuple[int, str]] = field(default_factory=list)
    messages_per_minute: List[Tuple[datetime, int]] = field(default_factory=list)
    unique_messages: int = 0
    avg_line_length: float = 0.0
    error_rate: float = 0.0


class LogAnalyzer:
    """Analyze parsed log entries for patterns, rates, and anomalies."""

    def __init__(self, entries: List[LogEntry]):
        self.entries = entries

    def full_report(self, top_n: int = 10) -> AnalysisReport:
        rpt = AnalysisReport()
        rpt.total_lines = len(self.entries)
        if not self.entries:
            return rpt

        timestamps = [e.timestamp for e in self.entries if e.timestamp]
        if timestamps:
            rpt.time_range = (min(timestamps), max(timestamps))

        levels = Counter(e.level for e in self.entries)
        rpt.level_counts = dict(levels.most_common())

        error_levels = {"ERROR", "CRITICAL", "FATAL", "SEVERE", "ALERT", "EMERG"}
        error_count = sum(v for k, v in levels.items() if k in error_levels)
        rpt.error_rate = error_count / len(self.entries)

        err_msgs = Counter(e.message[:200] for e in self.entries if e.level in error_levels)
        rpt.top_errors = err_msgs.most_common(top_n)

        srcs = Counter(e.source for e in self.entries if e.source)
        rpt.top_sources = srcs.most_common(top_n)

        per_min = Counter()
        for e in self.entries:
            if e.timestamp:
                key = e.timestamp.replace(second=0, microsecond=0)
                per_min[key] += 1
        rpt.messages_per_minute = sorted(per_min.items())

        rpt.unique_messages = len(set(e.message[:200] for e in self.entries))
        rpt.avg_line_length = sum(len(e.raw) for e in self.entries) / len(self.entries)
        return rpt

    def filter_by_level(self, *levels: str) -> List[LogEntry]:
        upper = {l.upper() for l in levels}
        return [e for e in self.entries if e.level.upper() in upper]

    def filter_by_time(self, start=None, end=None) -> List[LogEntry]:
        result = []
        for e in self.entries:
            if e.timestamp is None:
                continue
            if start and e.timestamp < start:
                continue
            if end and e.timestamp > end:
                continue
            result.append(e)
        return result

    def filter_by_pattern(self, pattern: str) -> List[LogEntry]:
        import re
        rx = re.compile(pattern, re.IGNORECASE)
        return [e for e in self.entries if rx.search(e.message)]

    def group_by_minute(self) -> Dict[datetime, List[LogEntry]]:
        groups = defaultdict(list)
        for e in self.entries:
            if e.timestamp:
                key = e.timestamp.replace(second=0, microsecond=0)
                groups[key].append(e)
        return dict(sorted(groups.items()))

    def spike_detection(self, threshold: float = 3.0) -> List[Tuple[datetime, int, float]]:
        per_min = self.group_by_minute()
        if len(per_min) < 3:
            return []
        counts = [len(v) for v in per_min.values()]
        mean = sum(counts) / len(counts)
        if mean == 0:
            return []
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)
        std = variance ** 0.5
        if std == 0:
            return []
        spikes = []
        for ts, entries in per_min.items():
            c = len(entries)
            z = (c - mean) / std
            if z > threshold:
                spikes.append((ts, c, round(z, 2)))
        return sorted(spikes)

    def top_messages(self, n: int = 10) -> List[Tuple[int, str]]:
        counter = Counter(e.message[:200] for e in self.entries)
        return counter.most_common(n)

    def timeline(self, bucket_seconds: int = 60) -> List[Tuple[datetime, int]]:
        buckets = Counter()
        for e in self.entries:
            if e.timestamp:
                epoch = int(e.timestamp.timestamp())
                aligned = epoch - (epoch % bucket_seconds)
                key = datetime.fromtimestamp(aligned)
                buckets[key] += 1
        return sorted(buckets.items())
