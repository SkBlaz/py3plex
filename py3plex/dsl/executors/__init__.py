"""DSL executors package.

This package contains specialized execution engines for different query types.
The main executor for SELECT/COMMUNITIES queries is in executor.py (sibling module).
This package contains benchmark and other specialized executors.
"""

from py3plex.dsl.executors.benchmark_executor import execute_benchmark

__all__ = ["execute_benchmark"]
