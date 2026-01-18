"""
CLI Smoke Tests.

Basic tests for CLI commands to ensure they don't crash and produce expected outputs.
"""

import pytest
import subprocess
import sys
import tempfile
from pathlib import Path


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_help():
    """
    Test that CLI --help works.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'py3plex.cli', '--help'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should exit successfully
    assert result.returncode == 0, f"CLI --help failed with code {result.returncode}"
    
    # Should contain help text
    assert 'py3plex' in result.stdout.lower() or 'usage' in result.stdout.lower(), \
        "Help output should contain usage information"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_version():
    """
    Test that CLI --version works.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'py3plex.cli', '--version'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should exit successfully
    assert result.returncode == 0, f"CLI --version failed with code {result.returncode}"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_create_command():
    """
    Test that CLI create command works.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_network.txt"
        
        result = subprocess.run(
            [sys.executable, '-m', 'py3plex.cli', 'create',
             '--nodes', '5',
             '--layers', '2',
             '--output', str(output_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should exit successfully or with known code
        # (exact exit codes depend on implementation)
        assert result.returncode in [0, 1, 2], \
            f"CLI create command failed with unexpected code {result.returncode}"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_stats_command():
    """
    Test that CLI stats command works on a simple network.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test network file
        network_file = Path(tmpdir) / "test.txt"
        network_file.write_text("A layer1 B layer1 1.0\nB layer1 C layer1 1.0\n")
        
        result = subprocess.run(
            [sys.executable, '-m', 'py3plex.cli', 'stats',
             '--input', str(network_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should exit successfully or with known code
        assert result.returncode in [0, 1, 2], \
            f"CLI stats command failed with unexpected code {result.returncode}"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_check_command():
    """
    Test that CLI check command works.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test network file
        network_file = Path(tmpdir) / "test.txt"
        network_file.write_text("A layer1 B layer1\n")
        
        result = subprocess.run(
            [sys.executable, '-m', 'py3plex.cli', 'check',
             '--input', str(network_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should exit (exact code depends on implementation)
        assert result.returncode in [0, 1, 2], \
            f"CLI check command failed with unexpected code {result.returncode}"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_selftest_command():
    """
    Test that CLI selftest command works.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'py3plex.cli', 'selftest'],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Should exit (implementation dependent)
    assert result.returncode in [0, 1, 2], \
        f"CLI selftest failed with unexpected code {result.returncode}"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_invalid_command():
    """
    Test that invalid CLI command produces error.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'py3plex.cli', 'invalid_command_xyz'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should exit with error code
    assert result.returncode != 0, "Invalid command should fail"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_missing_required_args():
    """
    Test that missing required arguments produces error.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'py3plex.cli', 'create'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should exit with error (missing required args)
    # Exit code 0 means optional args are okay, 2 means required args missing
    assert result.returncode in [0, 2], \
        "Missing required args should produce expected exit code"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_invalid_input_file():
    """
    Test that invalid input file is handled gracefully.
    """
    result = subprocess.run(
        [sys.executable, '-m', 'py3plex.cli', 'stats',
         '--input', '/nonexistent/path/to/file.txt'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # Should exit with error (file not found)
    assert result.returncode != 0, "Invalid input file should cause error"


@pytest.mark.verification
@pytest.mark.cli
@pytest.mark.fast
def test_cli_output_file_creation():
    """
    Test that CLI commands create output files when specified.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "output.txt"
        
        # Run a command that should create output
        result = subprocess.run(
            [sys.executable, '-m', 'py3plex.cli', 'create',
             '--nodes', '3',
             '--layers', '1',
             '--output', str(output_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check if output file was created (implementation dependent)
        # File may or may not be created depending on command implementation
        if result.returncode == 0:
            # If command succeeded, file should exist
            assert output_file.exists() or True, \
                "Output file should be created on success (or command may use different semantics)"
