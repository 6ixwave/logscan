"""Basic tests for logscan. Run: python tests/test_logscan.py"""
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logscan import LogParser, LogAnalyzer, LogEntry


def make_log(tmpdir, lines):
    path = os.path.join(tmpdir, "test.log")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def test_parse_basic():
    with tempfile.TemporaryDirectory() as d:
        p = make_log(d, [
            "2026-11-09 10:00:01 INFO Hello world",
            "2026-11-09 10:00:02 ERROR Something broke",
            "2026-11-09 10:00:03 WARNING Careful",
        ])
        entries = LogParser().parse_file(p)
        assert len(entries) == 3
        assert entries[0].level == "INFO"
        assert entries[1].level == "ERROR"
        assert entries[2].level == "WARNING"
        assert entries[0].timestamp == datetime(2026, 11, 9, 10, 0, 1)
        assert "Hello world" in entries[0].message


def test_parse_json():
    with tempfile.TemporaryDirectory() as d:
        p = make_log(d, [
            '{"timestamp":"2026-11-09T10:00:00","level":"ERROR","message":"disk full"}',
            '{"timestamp":"2026-11-09T10:00:01","level":"INFO","message":"ok"}',
        ])
        entries = LogParser().parse_file(p)
        assert len(entries) == 2
        assert entries[0].level == "ERROR"
        assert entries[0].timestamp == datetime(2026, 11, 9, 10, 0, 0)


def test_analyzer_report():
    with tempfile.TemporaryDirectory() as d:
        lines = [f"2026-11-09 10:00:{i:02d} INFO msg{i}" for i in range(10)]
        lines += [f"2026-11-09 10:01:{i:02d} ERROR err{i}" for i in range(3)]
        p = make_log(d, lines)
        entries = LogParser().parse_file(p)
        rpt = LogAnalyzer(entries).full_report()
        assert rpt.total_lines == 13
        assert rpt.level_counts.get("INFO") == 10
        assert rpt.level_counts.get("ERROR") == 3
        assert abs(rpt.error_rate - 3 / 13) < 0.01


def test_filter_by_level():
    with tempfile.TemporaryDirectory() as d:
        p = make_log(d, [
            "2026-11-09 10:00:01 INFO ok",
            "2026-11-09 10:00:02 ERROR bad",
            "2026-11-09 10:00:03 WARNING warn",
        ])
        entries = LogParser().parse_file(p)
        errs = LogAnalyzer(entries).filter_by_level("ERROR")
        assert len(errs) == 1
        assert "10:00:02" in errs[0].message


def test_filter_by_pattern():
    with tempfile.TemporaryDirectory() as d:
        p = make_log(d, [
            "2026-11-09 10:00:01 INFO timeout on api",
            "2026-11-09 10:00:02 INFO ok",
            "2026-11-09 10:00:03 ERROR connection refused",
        ])
        entries = LogParser().parse_file(p)
        matched = LogAnalyzer(entries).filter_by_pattern("timeout|refused")
        assert len(matched) == 2


def test_spike_detection():
    with tempfile.TemporaryDirectory() as d:
        lines = []
        for m in range(5):
            lines.append(f"2026-11-09 10:{m:02d}:00 INFO normal")
        for i in range(50):
            lines.append(f"2026-11-09 10:05:{i % 60:02d} INFO burst")
        p = make_log(d, lines)
        entries = LogParser().parse_file(p)
        spikes = LogAnalyzer(entries).spike_detection(threshold=2.0)
        assert len(spikes) >= 1
        assert spikes[0][1] == 50


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
