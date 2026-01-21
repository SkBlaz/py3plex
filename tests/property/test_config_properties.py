#!/usr/bin/env python3
"""
Property-based tests for config module.

Tests configuration values, types, and helper functions.
"""

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck

# Import config module
try:
    from py3plex import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    pytest.skip("config module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Configuration Constants
# ============================================================================

@pytest.mark.property
def test_config_has_required_constants():
    """Test that config module has all required constant definitions."""
    required_constants = [
        'DEFAULT_NODE_SIZE',
        'DEFAULT_NODE_ALPHA',
        'DEFAULT_EDGE_WIDTH',
        'DEFAULT_EDGE_ALPHA',
        'COLOR_PALETTES',
        'DEFAULT_COLOR_PALETTE',
        'RANDOM_SEED',
    ]
    
    for constant in required_constants:
        assert hasattr(config, constant), \
            f"config module should define {constant}"


@pytest.mark.property
def test_numeric_config_values_are_positive():
    """Test that numeric configuration values are positive."""
    positive_values = [
        config.DEFAULT_NODE_SIZE,
        config.DEFAULT_EDGE_WIDTH,
        config.FORCE_LAYOUT_ITERATIONS,
        config.NODE2VEC_DIMENSIONS,
        config.NODE2VEC_WALK_LENGTH,
        config.NODE2VEC_NUM_WALKS,
    ]
    
    for value in positive_values:
        assert value > 0, \
            "Numeric configuration values should be positive"


@pytest.mark.property
def test_alpha_values_in_valid_range():
    """Test that alpha (transparency) values are in [0, 1] range."""
    alpha_values = [
        config.DEFAULT_NODE_ALPHA,
        config.DEFAULT_EDGE_ALPHA,
        config.DEFAULT_LAYER_ALPHA,
    ]
    
    for alpha in alpha_values:
        assert 0 <= alpha <= 1, \
            f"Alpha value {alpha} should be in range [0, 1]"


@pytest.mark.property
def test_color_palettes_are_valid():
    """Test that all color palettes contain valid hex colors."""
    import re
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    
    for palette_name, colors in config.COLOR_PALETTES.items():
        assert isinstance(colors, list), \
            f"Palette {palette_name} should be a list"
        assert len(colors) > 0, \
            f"Palette {palette_name} should not be empty"
        
        for color in colors:
            assert hex_pattern.match(color), \
                f"Color {color} in palette {palette_name} should be valid hex"


@pytest.mark.property
def test_default_color_palette_exists():
    """Test that the default color palette is defined in COLOR_PALETTES."""
    assert config.DEFAULT_COLOR_PALETTE in config.COLOR_PALETTES, \
        "DEFAULT_COLOR_PALETTE should be a valid palette name"


@pytest.mark.property
def test_background_shapes_are_valid():
    """Test that background shapes list is valid."""
    assert isinstance(config.BACKGROUND_SHAPES, list), \
        "BACKGROUND_SHAPES should be a list"
    assert len(config.BACKGROUND_SHAPES) > 0, \
        "BACKGROUND_SHAPES should not be empty"
    assert config.DEFAULT_BACKGROUND_SHAPE in config.BACKGROUND_SHAPES, \
        "DEFAULT_BACKGROUND_SHAPE should be in BACKGROUND_SHAPES"


# ============================================================================
# Property Tests: get_color_palette function
# ============================================================================

@pytest.mark.property
def test_get_color_palette_with_none_returns_default():
    """Test that get_color_palette(None) returns the default palette."""
    result = config.get_color_palette(None)
    expected = config.COLOR_PALETTES[config.DEFAULT_COLOR_PALETTE]
    
    assert result == expected, \
        "get_color_palette(None) should return default palette"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(palette_name=st.sampled_from(list(config.COLOR_PALETTES.keys())))
def test_get_color_palette_returns_valid_palette(palette_name):
    """Test that get_color_palette returns valid palettes for known names."""
    result = config.get_color_palette(palette_name)
    expected = config.COLOR_PALETTES[palette_name]
    
    assert result == expected, \
        f"get_color_palette should return palette for {palette_name}"
    assert isinstance(result, list), \
        "Result should be a list"
    assert len(result) > 0, \
        "Result should not be empty"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(invalid_name=st.text(min_size=1, max_size=20).filter(
    lambda s: s not in config.COLOR_PALETTES
))
def test_get_color_palette_raises_on_invalid_name(invalid_name):
    """Test that get_color_palette raises ValueError for invalid names."""
    with pytest.raises(ValueError, match="Unknown palette"):
        config.get_color_palette(invalid_name)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(palette_name=st.sampled_from(list(config.COLOR_PALETTES.keys())))
def test_get_color_palette_is_idempotent(palette_name):
    """Test that calling get_color_palette multiple times returns same result."""
    result1 = config.get_color_palette(palette_name)
    result2 = config.get_color_palette(palette_name)
    
    assert result1 == result2, \
        "get_color_palette should be idempotent"


# ============================================================================
# Property Tests: Configuration Types
# ============================================================================

@pytest.mark.property
def test_config_types_are_correct():
    """Test that configuration values have expected types."""
    # Integer types
    assert isinstance(config.DEFAULT_NODE_SIZE, int)
    assert isinstance(config.FORCE_LAYOUT_ITERATIONS, int)
    assert isinstance(config.RANDOM_SEED, int)
    
    # Float types
    assert isinstance(config.DEFAULT_NODE_ALPHA, float)
    assert isinstance(config.DEFAULT_EDGE_ALPHA, float)
    assert isinstance(config.FORCE_LAYOUT_K, float)
    
    # String types
    assert isinstance(config.DEFAULT_EDGE_STYLE, str)
    assert isinstance(config.DEFAULT_COLOR_PALETTE, str)
    assert isinstance(config.DEFAULT_FONT_FAMILY, str)
    
    # Boolean types
    assert isinstance(config.STRICT_VALIDATION, bool)
    assert isinstance(config.WARN_DEPRECATED, bool)
    assert isinstance(config.USE_SPARSE_MATRICES, bool)
    
    # Dict types
    assert isinstance(config.COLOR_PALETTES, dict)
    
    # List types
    assert isinstance(config.BACKGROUND_SHAPES, list)


@pytest.mark.property
def test_version_strings_are_valid():
    """Test that version strings are properly formatted."""
    import re
    version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
    
    assert version_pattern.match(config.__version__), \
        "__version__ should be in x.y.z format"
    assert version_pattern.match(config.__api_version__), \
        "__api_version__ should be in x.y.z format"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
