"""logscan — lightweight log file analyzer and parser.

Quickly parse, filter, and summarize log files (syslog, nginx, Apache,
custom formats). Zero external dependencies beyond stdlib.
"""

__version__ = "0.1.0"

from .parser import LogParser, LogEntry
from .analyzer import LogAnalyzer

__all__ = ["LogParser", "LogEntry", "LogAnalyzer", "__version__"]
