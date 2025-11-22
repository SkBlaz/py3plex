"""
Tests for py3plex __main__ module entry point.

This tests running py3plex as a module: python -m py3plex
"""
import subprocess
import sys


def test_main_module_help():
    """Test that running py3plex as module shows help."""
    result = subprocess.run(
        [sys.executable, "-m", "py3plex", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "py3plex" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_main_module_version():
    """Test that running py3plex as module with --version works."""
    result = subprocess.run(
        [sys.executable, "-m", "py3plex", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Should exit with 0 or show version info
    assert result.returncode == 0 or "version" in result.stdout.lower() or "0.95" in result.stdout
