"""Tests for the CLI check command."""

import subprocess
import tempfile
from pathlib import Path


def test_cli_check_help():
    """Test py3plex check --help command."""
    result = subprocess.run(
        ["py3plex", "check", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "input" in result.stdout.lower()
    assert "strict" in result.stdout.lower()


def test_cli_check_nonexistent_file():
    """Test py3plex check with nonexistent file."""
    result = subprocess.run(
        ["py3plex", "check", "/nonexistent/file.csv"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()


def test_cli_check_valid_edgelist():
    """Test py3plex check with valid edgelist."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
        f.write("A B\n")
        f.write("B C\n")
        f.write("C D\n")
        temp_file = f.name

    try:
        result = subprocess.run(
            ["py3plex", "check", temp_file],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Output may be in stdout or stderr (logger output)
        output = result.stdout + result.stderr
        assert "no issues" in output.lower() or "✓" in output
    finally:
        Path(temp_file).unlink()


def test_cli_check_invalid_file():
    """Test py3plex check with file containing errors."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("src,dst,weight\n")
        f.write("A,B,1.0\n")
        f.write("C,D,invalid\n")  # Invalid weight
        temp_file = f.name

    try:
        result = subprocess.run(
            ["py3plex", "check", temp_file],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stdout.lower() or "error" in result.stderr.lower()
    finally:
        Path(temp_file).unlink()


def test_cli_check_warnings_strict():
    """Test py3plex check with warnings in strict mode."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
        f.write("A B\n")
        f.write("B B\n")  # Self-loop (warning)
        temp_file = f.name

    try:
        result = subprocess.run(
            ["py3plex", "check", temp_file, "--strict"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "strict" in result.stdout.lower() or "strict" in result.stderr.lower()
    finally:
        Path(temp_file).unlink()


def test_cli_check_warnings_non_strict():
    """Test py3plex check with warnings in non-strict mode."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".edgelist", delete=False) as f:
        f.write("A B\n")
        f.write("B B\n")  # Self-loop (warning)
        temp_file = f.name

    try:
        result = subprocess.run(
            ["py3plex", "check", temp_file],
            capture_output=True,
            text=True,
        )
        # Should pass with warnings (exit code 0)
        assert result.returncode == 0
        # Check both stdout and stderr (logger output may be in either)
        output = result.stdout + result.stderr
        assert "warning" in output.lower()
    finally:
        Path(temp_file).unlink()
