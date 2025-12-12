"""
Prevent pytest doctest collection in Infomap examples/bindings.

These files require the external Infomap binary and SWIG bindings, which
are optional and not installed in fast/CI environments.
"""

collect_ignore_glob = ["*.py"]
