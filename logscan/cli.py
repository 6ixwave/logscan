"""CLI entry point for logscan."""

import argparse
import json
import sys
from pathlib import Path

from .parser import LogParser
from .analyzer import LogAnalyzer


def main():
    ap = argparse.ArgumentParser(
        prog="logscan",
        description="Lightweight log file analyzer — parse, filter, summarize.",
    )
    ap.add_argument("file", help="Path to log file (or '-' for stdin)")
    ap.add_argument("--level", nargs="*", help="Filter by level(s)")
    ap.add_argument("--pattern", help="Regex to filter messages")
    ap.add_argument("--top", type=int, default=10, help="Top N items")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--lines", type=int, help="Max lines to parse")
    ap.add_argument("--quiet", action="store_true", help="Only show report")
    args = ap.parse_args()

    parser = LogParser()
    if args.file == "-":
        entries = list(parser.parse_stream(sys.stdin, source="<stdin>"))
    else:
        p = Path(args.file)
        if not p.exists():
            print(f"ERROR: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        entries = parser.parse_file(str(p), max_lines=args.lines)

    if args.level:
        entries = LogAnalyzer(entries).filter_by_level(*args.level)
    if args.pattern:
        entries = LogAnalyzer(entries).filter_by_pattern(args.pattern)

    analyzer = LogAnalyzer(entries)
    report = analyzer.full_report(top_n=args.top)

    if args.json:
        out = {
            "total": report.total_lines,
            "time_range": [str(t) for t in report.time_range],
            "levels": report.level_counts,
            "error_rate": round(report.error_rate, 4),
            "top_errors": report.top_errors,
            "top_messages": analyzer.top_messages(args.top),
            "unique_messages": report.unique_messages,
            "avg_line_length": round(report.avg_line_length, 1),
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"{'='*50}")
        print(f"  LOGSCAN REPORT: {args.file}")
        print(f"{'='*50}")
        print(f"  Lines:      {report.total_lines}")
        if report.time_range[0]:
            print(f"  Time range: {report.time_range[0]} -> {report.time_range[1]}")
        print(f"  Error rate: {report.error_rate:.2%}")
        print(f"  Levels:     {report.level_counts}")
        print(f"  Unique msgs: {report.unique_messages}")
        print(f"{'-'*50}")
        if report.top_errors:
            print(f"  TOP ERRORS (top {args.top}):")
            for msg, cnt in report.top_errors:
                print(f"    [{cnt:4d}] {msg[:80]}")
        print(f"{'-'*50}")
        top = analyzer.top_messages(args.top)
        print(f"  TOP MESSAGES:")
        for msg, cnt in top:
            print(f"    [{cnt:4d}] {msg[:80]}")
        print(f"{'='*50}")

        if not args.quiet:
            print(f"\n  SAMPLE ENTRIES (first 20):")
            for e in entries[:20]:
                ts = e.timestamp.strftime("%H:%M:%S") if e.timestamp else "         "
                print(f"  {ts} [{e.level:8s}] {e.message[:100]}")


if __name__ == "__main__":
    main()
