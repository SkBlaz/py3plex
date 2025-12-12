"""
Repository-level pytest configuration.

We ignore optional or example-only modules from collection to keep doctest
discovery from importing heavy or optional dependencies during fast runs.
"""

# Ignore optional Infomap examples and bindings (require external dependency)
collect_ignore_glob = [
    "py3plex/algorithms/community_detection/infomap/**/*.py",
]

# Explicit ignores for doctest collection stubbornness
collect_ignore = [
    "py3plex/algorithms/community_detection/infomap",
    "py3plex/algorithms/community_detection/infomap/infomap.py",
]
