"""
Tests for py3plex.__main__ module.

This module tests the entry point for running py3plex as a module.
"""

import subprocess
import sys
import pytest


class TestMainModule:
    """Test the __main__ module entry point."""

    def test_main_module_help(self):
        """Test running py3plex as module with --help flag."""
        # Run: python -m py3plex --help
        result = subprocess.run(
            [sys.executable, "-m", "py3plex", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit successfully
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        
        # Should output help text
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower(), (
            "Help text should contain usage information"
        )

    def test_main_module_version(self):
        """Test running py3plex as module with --version flag."""
        # Run: python -m py3plex --version
        result = subprocess.run(
            [sys.executable, "-m", "py3plex", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit successfully
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        
        # Should output version
        output = result.stdout + result.stderr
        assert any(c.isdigit() for c in output), (
            "Version output should contain version number"
        )

    def test_main_module_invalid_command(self):
        """Test running py3plex with invalid command."""
        # Run: python -m py3plex invalid_command
        result = subprocess.run(
            [sys.executable, "-m", "py3plex", "invalid_command_xyz"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit with error
        assert result.returncode != 0, (
            "Invalid command should exit with non-zero code"
        )
