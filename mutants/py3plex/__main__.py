#!/usr/bin/env python
"""
Entry point for running py3plex as a module: python -m py3plex
"""

import sys

from py3plex.cli import main

if __name__ == "__main__":
    sys.exit(main())
