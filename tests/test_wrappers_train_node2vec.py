"""
Tests for the wrappers.train_node2vec_embedding module.

This module tests the Node2Vec embedding training functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest import mock

import networkx as nx
import pytest

from py3plex.exceptions import ExternalToolError
from py3plex.wrappers.train_node2vec_embedding import (
    call_node2vec_binary,
    DEFAULT_NODE2VEC_BINARY,
)


class TestCallNode2VecBinary:
    """Test the call_node2vec_binary function."""

    def test_call_node2vec_binary_not_found(self):
        """Test that calling non-existent binary raises ExternalToolError."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".edges") as f:
            f.write("0 1 1.0\n")
            input_file = f.name

        output_file = tempfile.mktemp(suffix=".emb")

        try:
            with pytest.raises(ExternalToolError, match="Node2Vec binary not found"):
                call_node2vec_binary(
                    input_file,
                    output_file,
                    binary="/nonexistent/path/to/node2vec"
                )
        finally:
            Path(input_file).unlink()
            if os.path.exists(output_file):
                Path(output_file).unlink()

    def test_call_node2vec_binary_parameters(self):
        """Test that parameters are properly constructed."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(stdout="", stderr="")

                call_node2vec_binary(
                    input_file,
                    output_file,
                    p=0.5,
                    q=2.0,
                    dimension=64,
                    directed=True,
                    weighted=False,
                    binary=mock_binary,
                    timeout=120,
                )

                # Check that subprocess.run was called
                assert mock_run.called
                call_args = mock_run.call_args
                params = call_args[0][0]

                # Verify parameters
                assert mock_binary in params
                assert f"-i:{input_file}" in params
                assert f"-o:{output_file}" in params
                assert "-d:64" in params
                assert "-p:0.5" in params
                assert "-q:2.0" in params

    def test_call_node2vec_binary_directed_flag(self):
        """Test that directed flag is properly passed."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(stdout="", stderr="")

                call_node2vec_binary(
                    input_file,
                    output_file,
                    directed=True,
                    binary=mock_binary,
                )

                params = mock_run.call_args[0][0]
                assert "-d" in params

    def test_call_node2vec_binary_weighted_flag(self):
        """Test that weighted flag is properly passed."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(stdout="", stderr="")

                call_node2vec_binary(
                    input_file,
                    output_file,
                    weighted=True,
                    binary=mock_binary,
                )

                params = mock_run.call_args[0][0]
                assert "-w" in params

    def test_call_node2vec_binary_timeout_error(self):
        """Test that timeout raises ExternalToolError."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                import subprocess
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd=[], timeout=10
                )

                with pytest.raises(ExternalToolError, match="timed out"):
                    call_node2vec_binary(
                        input_file,
                        output_file,
                        binary=mock_binary,
                        timeout=10,
                    )

    def test_call_node2vec_binary_execution_error(self):
        """Test that execution failure raises ExternalToolError."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                import subprocess
                error = subprocess.CalledProcessError(
                    returncode=1,
                    cmd=[],
                )
                error.stdout = "error output"
                error.stderr = "error details"
                mock_run.side_effect = error

                with pytest.raises(ExternalToolError, match="failed with exit code"):
                    call_node2vec_binary(
                        input_file,
                        output_file,
                        binary=mock_binary,
                    )

    def test_call_node2vec_binary_default_binary_path(self):
        """Test that default binary path is used when not specified."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")

        with mock.patch("os.path.isfile", return_value=False):
            with mock.patch("shutil.which", return_value=None):
                with pytest.raises(ExternalToolError):
                    call_node2vec_binary(input_file, output_file)

    def test_call_node2vec_binary_custom_dimension(self):
        """Test with custom embedding dimension."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(stdout="", stderr="")

                call_node2vec_binary(
                    input_file,
                    output_file,
                    dimension=256,
                    binary=mock_binary,
                )

                params = mock_run.call_args[0][0]
                assert "-d:256" in params

    def test_call_node2vec_binary_verbose_flag(self):
        """Test that verbose flag is always included."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(stdout="", stderr="")

                call_node2vec_binary(
                    input_file,
                    output_file,
                    binary=mock_binary,
                )

                params = mock_run.call_args[0][0]
                assert "-v" in params


class TestDefaultBinaryPath:
    """Test default binary path configuration."""

    def test_default_node2vec_binary_constant(self):
        """Test that DEFAULT_NODE2VEC_BINARY is properly defined."""
        assert isinstance(DEFAULT_NODE2VEC_BINARY, str)
        # Should be either the environment variable or the default "./node2vec"
        assert len(DEFAULT_NODE2VEC_BINARY) > 0


class TestErrorMessages:
    """Test error message quality and informativeness."""

    def test_binary_not_found_error_message_helpful(self):
        """Test that binary not found error provides helpful information."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")

        try:
            call_node2vec_binary(
                input_file,
                output_file,
                binary="/nonexistent/binary"
            )
        except ExternalToolError as e:
            error_msg = str(e)
            # Should mention the binary path
            assert "/nonexistent/binary" in error_msg
            # Should provide guidance
            assert "install" in error_msg.lower()
            # Should mention environment variable
            assert "PY3PLEX_NODE2VEC_BINARY" in error_msg

    def test_timeout_error_message_helpful(self):
        """Test that timeout error provides helpful information."""
        input_file = tempfile.mktemp(suffix=".edges")
        output_file = tempfile.mktemp(suffix=".emb")
        mock_binary = "/fake/node2vec"

        with mock.patch("shutil.which", return_value=mock_binary):
            with mock.patch("subprocess.run") as mock_run:
                import subprocess
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd=[], timeout=30
                )

                try:
                    call_node2vec_binary(
                        input_file,
                        output_file,
                        binary=mock_binary,
                        timeout=30,
                    )
                except ExternalToolError as e:
                    error_msg = str(e)
                    # Should mention timeout
                    assert "30" in error_msg
                    # Should provide guidance
                    assert "timeout" in error_msg.lower()
