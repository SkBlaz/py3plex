#!/usr/bin/env python3
"""
Tests for the centralized configuration module.
"""

import sys
import os

# Add py3plex to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config_imports():
    """Test that config module can be imported."""
    print("Testing config module imports...")

    try:
        from py3plex import config

        print("PASS: Config module imports successfully")
        return True
    except Exception as e:
        print(f"FAIL: Config module import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_config_values():
    """Test that config values are accessible and have expected types."""
    print("\nTesting config values...")

    try:
        from py3plex import config

        # Test basic visualization settings
        assert isinstance(
            config.DEFAULT_NODE_SIZE, int
        ), "DEFAULT_NODE_SIZE should be int"
        assert config.DEFAULT_NODE_SIZE > 0, "DEFAULT_NODE_SIZE should be positive"
        print("PASS: DEFAULT_NODE_SIZE is valid")

        assert isinstance(
            config.DEFAULT_EDGE_ALPHA, float
        ), "DEFAULT_EDGE_ALPHA should be float"
        assert (
            0 <= config.DEFAULT_EDGE_ALPHA <= 1
        ), "DEFAULT_EDGE_ALPHA should be between 0 and 1"
        print("PASS: DEFAULT_EDGE_ALPHA is valid")

        # Test color palettes
        assert isinstance(
            config.COLOR_PALETTES, dict
        ), "COLOR_PALETTES should be dict"
        assert len(config.COLOR_PALETTES) > 0, "COLOR_PALETTES should not be empty"
        assert "rainbow" in config.COLOR_PALETTES, "rainbow palette should exist"
        assert (
            "colorblind_safe" in config.COLOR_PALETTES
        ), "colorblind_safe palette should exist"
        print("PASS: COLOR_PALETTES is valid")

        # Test version info
        assert hasattr(config, "__api_version__"), "__api_version__ should exist"
        assert isinstance(config.__api_version__, str), "__api_version__ should be str"
        print("PASS: __api_version__ is valid")

        return True
    except Exception as e:
        print(f"FAIL: Config values test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_get_color_palette():
    """Test the get_color_palette helper function."""
    print("\nTesting get_color_palette() function...")

    try:
        from py3plex.config import get_color_palette

        # Test default palette
        colors = get_color_palette()
        assert isinstance(colors, list), "get_color_palette should return list"
        assert len(colors) > 0, "Palette should not be empty"
        print("PASS: Default palette works")

        # Test specific palette
        rainbow = get_color_palette("rainbow")
        assert isinstance(rainbow, list), "Rainbow palette should be list"
        assert len(rainbow) > 0, "Rainbow palette should not be empty"
        assert rainbow[0].startswith("#"), "Colors should be hex codes"
        print("PASS: Rainbow palette works")

        # Test colorblind safe palette
        cb_safe = get_color_palette("colorblind_safe")
        assert isinstance(cb_safe, list), "Colorblind safe palette should be list"
        assert len(cb_safe) > 0, "Colorblind safe palette should not be empty"
        print("PASS: Colorblind safe palette works")

        # Test invalid palette name
        try:
            get_color_palette("nonexistent")
            print("FAIL: Should have raised ValueError for invalid palette")
            return False
        except ValueError as e:
            assert "Unknown palette" in str(e), "Should mention unknown palette"
            print("PASS: Invalid palette raises ValueError")

        return True
    except Exception as e:
        print(f"FAIL: get_color_palette test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_version_in_main_init():
    """Test that __api_version__ is accessible from main package."""
    print("\nTesting __api_version__ in main __init__.py...")

    try:
        import py3plex

        assert hasattr(
            py3plex, "__api_version__"
        ), "__api_version__ should be in main package"
        assert isinstance(
            py3plex.__api_version__, str
        ), "__api_version__ should be str"
        assert hasattr(py3plex, "__version__"), "__version__ should be in main package"
        print(f"PASS: py3plex.__api_version__ = {py3plex.__api_version__}")
        print(f"PASS: py3plex.__version__ = {py3plex.__version__}")

        return True
    except Exception as e:
        print(f"FAIL: API version test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_utils_deprecation():
    """Test the deprecation utilities."""
    print("\nTesting deprecation utilities...")

    try:
        import warnings

        # Try to import utils - if numpy is not available, skip this test
        try:
            from py3plex.utils import deprecated, warn_if_deprecated
        except ImportError as e:
            if "numpy" in str(e):
                print("WARNING:  Skipping test (numpy not available)")
                return True
            raise

        # Test deprecated decorator
        @deprecated(
            reason="This is a test",
            version="0.95a",
            alternative="new_test_function()",
        )
        def old_test_function():
            return "test"

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_test_function()
            assert len(w) == 1, "Should generate one warning"
            assert issubclass(
                w[0].category, DeprecationWarning
            ), "Should be DeprecationWarning"
            assert "deprecated" in str(w[0].message).lower(), "Should mention deprecated"
            print("PASS: @deprecated decorator works")

        # Test warn_if_deprecated
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warn_if_deprecated("test_feature", "Just a test", "new_feature")
            assert len(w) == 1, "Should generate one warning"
            assert issubclass(
                w[0].category, DeprecationWarning
            ), "Should be DeprecationWarning"
            print("PASS: warn_if_deprecated() works")

        return True
    except Exception as e:
        print(f"FAIL: Deprecation utilities test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=== Testing Configuration and API Improvements ===\n")

    success = True

    # Run all tests
    success = test_config_imports() and success
    success = test_config_values() and success
    success = test_get_color_palette() and success
    success = test_api_version_in_main_init() and success
    success = test_utils_deprecation() and success

    print("\n" + "=" * 50)
    if success:
        print(
            "PASS: All configuration and API tests passed! New features are working correctly."
        )
        sys.exit(0)
    else:
        print("FAIL: Some tests failed!")
        sys.exit(1)
