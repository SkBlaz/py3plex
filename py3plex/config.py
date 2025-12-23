"""
Centralized configuration for py3plex.

This module provides default settings for visualization, layout algorithms,
and other configurable aspects of the library. Users can override these
settings by modifying the values after import.

Example:
    >>> from py3plex import config
    >>> config.DEFAULT_NODE_SIZE = 15
    >>> config.DEFAULT_EDGE_ALPHA = 0.5
"""

from typing import Dict, List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Visualization Settings
# ─────────────────────────────────────────────────────────────────────────────

# Default node appearance
DEFAULT_NODE_SIZE: int = 10
DEFAULT_NODE_ALPHA: float = 0.8
DEFAULT_NODE_EDGE_WIDTH: float = 0.5

# Default edge appearance
DEFAULT_EDGE_WIDTH: float = 1.0
DEFAULT_EDGE_ALPHA: float = 0.13
DEFAULT_EDGE_STYLE: str = "solid"  # 'solid', 'dashed', 'dotted'

# Default layer appearance
DEFAULT_LAYER_ALPHA: float = 0.15
DEFAULT_LAYER_EDGE_WIDTH: float = 0.3

# Background shapes for layer visualization
BACKGROUND_SHAPES: List[str] = ["circle", "rectangle", "none"]
DEFAULT_BACKGROUND_SHAPE: str = "circle"

# Multilayer visualization geometry
MULTILAYER_SHADOW_SIZE: float = 0.5  # Shadow offset for background shapes
MULTILAYER_CIRCLE_SIZE: float = 1.05  # Radius for circular layer backgrounds
MULTILAYER_LAYER_OFFSET: float = 1.5  # Spacing between consecutive layers

# ─────────────────────────────────────────────────────────────────────────────
# Color Schemes
# ─────────────────────────────────────────────────────────────────────────────

# Color palettes (in order of preference)
COLOR_PALETTES: Dict[str, List[str]] = {
    "rainbow": [
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#FFA07A",
        "#98D8C8",
        "#F7DC6F",
        "#BB8FCE",
        "#85C1E2",
    ],
    "pastel": [
        "#FFB3BA",
        "#BAFFC9",
        "#BAE1FF",
        "#FFFFBA",
        "#FFD4BA",
        "#E0BBE4",
        "#C7CEEA",
        "#FFDFD3",
    ],
    "vibrant": [
        "#E74C3C",
        "#3498DB",
        "#2ECC71",
        "#F39C12",
        "#9B59B6",
        "#1ABC9C",
        "#E67E22",
        "#34495E",
    ],
    "monochrome": [
        "#2C3E50",
        "#34495E",
        "#7F8C8D",
        "#95A5A6",
        "#BDC3C7",
        "#ECF0F1",
    ],
    # Color-blind safe palettes (from ColorBrewer)
    "colorblind_safe": [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
    ],
    "wong": [  # Bang Wong's color-blind safe palette
        "#000000",  # Black
        "#E69F00",  # Orange
        "#56B4E9",  # Sky Blue
        "#009E73",  # Bluish Green
        "#F0E442",  # Yellow
        "#0072B2",  # Blue
        "#D55E00",  # Vermillion
        "#CC79A7",  # Reddish Purple
    ],
}

DEFAULT_COLOR_PALETTE: str = "colorblind_safe"

# Single color fallbacks
DEFAULT_NODE_COLOR: str = "#1f77b4"  # Matplotlib blue
DEFAULT_EDGE_COLOR: str = "#888888"  # Gray
DEFAULT_LAYER_COLOR: str = "#E8E8E8"  # Light gray

# ─────────────────────────────────────────────────────────────────────────────
# Font Settings
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_FONT_FAMILY: str = "sans-serif"
DEFAULT_FONT_SIZE: int = 10
DEFAULT_LABEL_FONT_SIZE: int = 8
DEFAULT_TITLE_FONT_SIZE: int = 14

# ─────────────────────────────────────────────────────────────────────────────
# Layout Settings
# ─────────────────────────────────────────────────────────────────────────────

# Force-directed layout parameters
FORCE_LAYOUT_ITERATIONS: int = 100
FORCE_LAYOUT_K: float = 0.1  # Spring constant
FORCE_LAYOUT_TEMPERATURE: float = 1.0

# Random layout bounds
RANDOM_LAYOUT_BOUNDS: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0)

# Multilayer layout parameters
MULTILAYER_LAYER_SPACING: float = 1.5  # Vertical spacing between layers
MULTILAYER_NORMALIZE_COORDS: bool = True  # Normalize to unit square

# ─────────────────────────────────────────────────────────────────────────────
# Algorithm Parameters
# ─────────────────────────────────────────────────────────────────────────────

# Community detection
LOUVAIN_RESOLUTION: float = 1.0
LOUVAIN_RANDOMIZE: bool = False

# Random seed for reproducibility (None = random)
RANDOM_SEED: int = 42

# Embedding parameters
NODE2VEC_DIMENSIONS: int = 128
NODE2VEC_WALK_LENGTH: int = 80
NODE2VEC_NUM_WALKS: int = 10
NODE2VEC_P: float = 1.0
NODE2VEC_Q: float = 1.0

# ─────────────────────────────────────────────────────────────────────────────
# Performance Settings
# ─────────────────────────────────────────────────────────────────────────────

# Use sparse matrices for large networks
USE_SPARSE_MATRICES: bool = True
SPARSE_MATRIX_THRESHOLD: int = 1000  # Nodes threshold

# Batch size for visualization operations
VISUALIZATION_BATCH_SIZE: int = 1000

# Cache settings
ENABLE_LAYOUT_CACHE: bool = True
CACHE_SIZE_LIMIT: int = 100  # Number of layouts to cache

# ─────────────────────────────────────────────────────────────────────────────
# Validation Settings
# ─────────────────────────────────────────────────────────────────────────────

# Enable strict validation (raises exceptions on invalid data)
STRICT_VALIDATION: bool = True

# Warn on deprecated features
WARN_DEPRECATED: bool = True

# ─────────────────────────────────────────────────────────────────────────────
# Library Metadata
# ─────────────────────────────────────────────────────────────────────────────

__api_version__ = "1.0.3"
__version__ = "1.0.3"

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def get_color_palette(name: str = None) -> List[str]:
    """
    Get a color palette by name.

    Args:
        name: Palette name. If None, returns the default palette.

    Returns:
        List of color hex codes.

    Raises:
        ValueError: If palette name is not recognized.

    Example:
        >>> from py3plex.config import get_color_palette
        >>> colors = get_color_palette("rainbow")
        >>> print(colors[0])
        '#FF6B6B'
    """
    if name is None:
        name = DEFAULT_COLOR_PALETTE

    if name not in COLOR_PALETTES:
        raise ValueError(
            f"Unknown palette '{name}'. Available palettes: "
            f"{', '.join(COLOR_PALETTES.keys())}"
        )

    return COLOR_PALETTES[name]


def reset_to_defaults() -> None:
    """
    Reset all configuration values to their defaults.

    This is useful for testing or when you want to start fresh.

    Example:
        >>> from py3plex import config
        >>> config.DEFAULT_NODE_SIZE = 20
        >>> config.reset_to_defaults()
        >>> print(config.DEFAULT_NODE_SIZE)
        10
    """
    # This would need to store original values, but for simplicity,
    # users can just reload the module
    import importlib
    import sys

    if "py3plex.config" in sys.modules:
        importlib.reload(sys.modules["py3plex.config"])
