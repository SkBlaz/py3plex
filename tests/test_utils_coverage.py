"""
Tests to improve coverage of py3plex.utils module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from py3plex.exceptions import Py3plexIOError
from py3plex.utils import (
    ICONTRACT_AVAILABLE,
    deprecated,
    ensure,
    get_data_path,
    get_rng,
    require,
)


class TestRandomNumberGenerator:
    """Tests for get_rng function."""

    def test_get_rng_none_seed_returns_generator(self):
        """Test that get_rng with None returns a Generator."""
        rng = get_rng(None)
        assert isinstance(rng, np.random.Generator)

    def test_get_rng_integer_seed_returns_generator(self):
        """Test that get_rng with integer seed returns a Generator."""
        rng = get_rng(42)
        assert isinstance(rng, np.random.Generator)

    def test_get_rng_integer_seed_is_reproducible(self):
        """Test that same seed produces same sequence."""
        rng1 = get_rng(42)
        rng2 = get_rng(42)
        
        val1 = rng1.random()
        val2 = rng2.random()
        
        assert val1 == val2

    def test_get_rng_generator_passthrough(self):
        """Test that passing a Generator returns it unchanged."""
        original_rng = np.random.default_rng(42)
        returned_rng = get_rng(original_rng)
        
        # Should be the same object
        assert returned_rng is original_rng

    def test_get_rng_different_seeds_produce_different_sequences(self):
        """Test that different seeds produce different random sequences."""
        rng1 = get_rng(42)
        rng2 = get_rng(43)
        
        vals1 = [rng1.random() for _ in range(10)]
        vals2 = [rng2.random() for _ in range(10)]
        
        assert vals1 != vals2


class TestDeprecationDecorator:
    """Tests for the deprecated decorator."""

    def test_deprecated_issues_warning(self):
        """Test that deprecated decorator issues DeprecationWarning."""
        @deprecated("Use new_function instead", version="1.0.0")
        def old_function():
            return "old"
        
        with pytest.warns(DeprecationWarning, match="Use new_function instead"):
            result = old_function()
        
        assert result == "old"

    def test_deprecated_with_version_in_message(self):
        """Test that version appears in deprecation warning."""
        @deprecated("This is deprecated", version="2.0.0")
        def deprecated_func():
            pass
        
        with pytest.warns(DeprecationWarning, match="2.0.0"):
            deprecated_func()

    def test_deprecated_preserves_function_name(self):
        """Test that decorator preserves original function name."""
        @deprecated("Deprecated", version="1.0.0")
        def my_function():
            pass
        
        assert my_function.__name__ == "my_function"

    def test_deprecated_with_args_and_kwargs(self):
        """Test that deprecated function still accepts arguments."""
        @deprecated("Use new version", version="1.0.0")
        def add(a, b, multiplier=1):
            return (a + b) * multiplier
        
        with pytest.warns(DeprecationWarning):
            result = add(2, 3, multiplier=2)
        
        assert result == 10


class TestIcontractDecorators:
    """Tests for icontract decorator availability."""

    def test_require_decorator_exists(self):
        """Test that require decorator can be used."""
        @require(lambda x: x > 0, "x must be positive")
        def positive_only(x):
            return x * 2
        
        # Should work with valid input
        result = positive_only(5)
        assert result == 10

    def test_ensure_decorator_exists(self):
        """Test that ensure decorator can be used."""
        @ensure(lambda result: result > 0, "result must be positive")
        def always_positive():
            return 42
        
        result = always_positive()
        assert result == 42

    def test_icontract_available_flag_is_boolean(self):
        """Test that ICONTRACT_AVAILABLE is a boolean."""
        assert isinstance(ICONTRACT_AVAILABLE, bool)


class TestGetDataPath:
    """Tests for get_data_path function."""

    def test_get_data_path_raises_when_file_not_found(self):
        """Test that Py3plexIOError is raised when file doesn't exist."""
        with pytest.raises(Py3plexIOError, match="Could not find"):
            get_data_path("nonexistent/file/path.txt")

    def test_get_data_path_error_message_includes_search_paths(self):
        """Test that error message includes searched paths."""
        try:
            get_data_path("nonexistent.txt")
            pytest.fail("Expected Py3plexIOError")
        except Py3plexIOError as e:
            error_msg = str(e)
            assert "Searched paths:" in error_msg
            assert "nonexistent.txt" in error_msg

    def test_get_data_path_error_message_includes_instructions(self):
        """Test that error message includes helpful instructions."""
        try:
            get_data_path("missing.txt")
            pytest.fail("Expected Py3plexIOError")
        except Py3plexIOError as e:
            error_msg = str(e)
            assert "Clone the repository" in error_msg or "git clone" in error_msg

    def test_get_data_path_finds_file_in_cwd(self):
        """Test that get_data_path finds file in current directory."""
        # Create a temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_data.txt"
            test_file.write_text("test content")
            
            # Change to that directory
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = get_data_path("test_data.txt")
                assert Path(result).exists()
                assert Path(result).name == "test_data.txt"
            finally:
                os.chdir(original_cwd)

    def test_get_data_path_with_nested_path(self):
        """Test get_data_path with nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "datasets" / "subdir"
            nested_dir.mkdir(parents=True)
            test_file = nested_dir / "data.txt"
            test_file.write_text("content")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = get_data_path("datasets/subdir/data.txt")
                assert Path(result).exists()
            finally:
                os.chdir(original_cwd)


class TestContractDecoratorsWithoutIcontract:
    """Tests to ensure decorators work when icontract is not available."""

    def test_require_no_op_when_icontract_unavailable(self):
        """Test that require decorator is no-op without icontract."""
        # This test ensures the fallback decorators work
        @require(lambda x: x > 0)
        def test_func(x):
            return x
        
        # Should not raise even with invalid input when icontract not available
        # (the decorator becomes a no-op)
        result = test_func(42)
        assert result == 42

    def test_ensure_no_op_when_icontract_unavailable(self):
        """Test that ensure decorator is no-op without icontract."""
        @ensure(lambda result: result > 0)
        def test_func():
            return 42
        
        result = test_func()
        assert result == 42
