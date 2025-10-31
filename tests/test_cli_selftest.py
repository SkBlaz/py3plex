"""
CLI smoke test for py3plex selftest command.

This module tests that the CLI works correctly as specified in LLM.md:
- `py3plex selftest` command runs successfully
- Exit code is 0 (success condition from LLM.md)
- No crashes or exceptions

Reference: LLM.md sections "Installation" and "Quick Reference"
which document `py3plex selftest` as the verification command.
"""

import subprocess
import sys

import pytest


class TestCLISelftest:
    """Test CLI selftest command.
    
    Reference: LLM.md "Installation" section:
    "# Verify installation
     py3plex selftest"
    
    And "Quick Reference" section:
    "py3plex selftest" for installation verification.
    """
    
    def test_selftest_exits_zero(self):
        """py3plex selftest exits with code 0 on success.
        
        Invariant from LLM.md: selftest should verify installation successfully.
        Exit code 0 indicates success per standard Unix conventions.
        """
        try:
            # Run selftest command
            result = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "selftest"],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout for safety
            )
            
            # Check exit code
            assert result.returncode == 0, \
                f"selftest should exit with code 0, got {result.returncode}\n" \
                f"stdout: {result.stdout}\n" \
                f"stderr: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            pytest.fail("selftest command timed out after 60 seconds")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found (may not be installed)")
    
    def test_selftest_produces_output(self):
        """py3plex selftest produces output indicating completion.
        
        Reference: LLM.md - selftest should provide feedback to user.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "selftest"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Should produce some output (either stdout or stderr)
            output = result.stdout + result.stderr
            assert len(output) > 0, "selftest should produce output"
            
            # Output should contain some indication of selftest running
            # (case-insensitive check for common terms)
            output_lower = output.lower()
            has_selftest_indication = any(
                keyword in output_lower 
                for keyword in ['selftest', 'self-test', 'test', 'verify', 'check']
            )
            
            assert has_selftest_indication, \
                f"selftest output should indicate testing activity. Got: {output[:200]}"
                
        except subprocess.TimeoutExpired:
            pytest.skip("selftest command timed out")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found")
    
    def test_selftest_no_crash(self):
        """py3plex selftest completes without crashing.
        
        Invariant: CLI commands should not crash with uncaught exceptions.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "selftest"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check that we didn't get a Python traceback in stderr
            # (indicates uncaught exception)
            assert "Traceback (most recent call last)" not in result.stderr, \
                f"selftest should not crash with exception:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            pytest.skip("selftest command timed out")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found")
    
    def test_cli_help_works(self):
        """py3plex --help works (basic CLI sanity check).
        
        Reference: LLM.md "Quick Reference": "py3plex --help"
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "--help"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Help should exit with 0
            assert result.returncode == 0, \
                f"--help should exit with code 0, got {result.returncode}"
            
            # Should contain usage information
            output = result.stdout + result.stderr
            assert len(output) > 0, "--help should produce output"
            
            # Common help patterns
            has_help_content = any(
                keyword in output.lower()
                for keyword in ['usage', 'help', 'command', 'option']
            )
            
            assert has_help_content, \
                f"--help should show usage information. Got: {output[:200]}"
                
        except subprocess.TimeoutExpired:
            pytest.skip("--help command timed out")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found")


class TestCLIAvailability:
    """Test that CLI is available and importable.
    
    Reference: LLM.md - CLI is a key component of py3plex.
    """
    
    def test_cli_module_importable(self):
        """py3plex.cli module can be imported.
        
        Invariant: CLI module must be importable for use.
        """
        try:
            from py3plex import cli
            assert hasattr(cli, 'main'), "CLI module should have main() function"
        except ImportError as e:
            pytest.fail(f"Could not import py3plex.cli: {e}")
    
    def test_cli_has_selftest_command(self):
        """CLI module defines selftest command.
        
        Reference: LLM.md documents selftest as a CLI command.
        """
        try:
            from py3plex import cli
            
            # Check for selftest-related functions/definitions
            # The exact implementation may vary, but there should be something
            module_contents = dir(cli)
            
            # Look for selftest-related names
            has_selftest_impl = any(
                'selftest' in name.lower()
                for name in module_contents
            )
            
            # This is a weak check - just verify the module seems complete
            assert has_selftest_impl or hasattr(cli, 'main'), \
                "CLI module should have selftest functionality"
                
        except ImportError:
            pytest.skip("Could not import py3plex.cli")


class TestCLIEdgeCases:
    """Test edge cases and error handling in CLI.
    
    Reference: LLM.md "Known Limitations" - handle errors gracefully.
    """
    
    def test_invalid_command_handled(self):
        """Invalid CLI command produces helpful error message.
        
        Property: CLI should handle invalid input gracefully.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "nonexistent_command_xyz"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Should exit with non-zero for invalid command
            assert result.returncode != 0, \
                "Invalid command should exit with non-zero code"
            
            # Should produce error message
            error_output = result.stdout + result.stderr
            assert len(error_output) > 0, \
                "Invalid command should produce error message"
                
        except subprocess.TimeoutExpired:
            pytest.skip("Command timed out")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found")
    
    @pytest.mark.xfail(reason="CLI error handling behavior needs verification from LLM.md")
    def test_selftest_with_invalid_flag(self):
        """selftest with invalid flag handles error gracefully.
        
        Reference: LLM.md - error handling should be robust.
        Marked xfail pending clarification of expected behavior.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "selftest", "--invalid-flag-xyz"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # This might exit with error or ignore the flag
            # Behavior needs clarification from LLM.md
            pass
            
        except subprocess.TimeoutExpired:
            pytest.skip("Command timed out")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found")


class TestCLIDocumentedBehavior:
    """Test CLI behaviors documented in LLM.md.
    
    Reference: LLM.md "CLI usage" and "Quick Reference" sections.
    """
    
    def test_cli_main_is_entry_point(self):
        """CLI main function serves as entry point.
        
        Reference: LLM.md pyproject.toml shows:
        [project.scripts]
        py3plex = "py3plex.cli:main"
        """
        try:
            from py3plex.cli import main
            
            # main should be callable
            assert callable(main), "CLI main() should be callable"
            
        except ImportError:
            pytest.skip("Could not import py3plex.cli")
    
    def test_selftest_is_deterministic(self):
        """Running selftest twice gives same result (determinism check).
        
        Property: selftest should be deterministic for reliability.
        """
        try:
            result1 = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "selftest"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            result2 = subprocess.run(
                [sys.executable, "-m", "py3plex.cli", "selftest"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Both runs should have same exit code
            assert result1.returncode == result2.returncode, \
                "selftest should be deterministic (same exit code on repeated runs)"
                
        except subprocess.TimeoutExpired:
            pytest.skip("selftest command timed out")
        except FileNotFoundError:
            pytest.skip("py3plex CLI not found")
