"""Dependency metadata checks must collect without Python 3.11's tomllib."""

from pathlib import Path
import subprocess
import sys


def test_dependency_checks_import_without_tomllib():
    script = """
import runpy
import sys
try:
    import tomllib as parser
except ModuleNotFoundError:
    import tomli as parser
sys.modules['tomli'] = parser
sys.modules['tomllib'] = None
checks = runpy.run_path(sys.argv[1])
checks['test_gensim_and_rdflib_are_not_core_dependencies']()
checks['test_gensim_and_rdflib_live_in_algos_extra']()
# Python 3.8 cannot evaluate list[str]/set[str] at function definition time.
assert checks['_dependency_names'].__annotations__['specs'] == 'list[str]'
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(Path(__file__).with_name("test_dependency_cleanup.py")),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
