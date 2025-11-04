"""
Visualization module for py3plex.

This module provides visualization tools for multilayer networks, including:
- Multilayer network layouts (diagonal, hairball, force-directed)
- Color utilities for node and edge coloring
- Embedding visualization tools
- Layout algorithms

Most common imports:
    from py3plex.visualization.multilayer import hairball_plot, draw_multilayer_default
    from py3plex.visualization.colors import colors_default
    from py3plex.visualization.embedding_visualization import embedding_tools
"""

# Import most commonly used visualization functions for convenience
from .multilayer import (
    hairball_plot,
    draw_multilayer_default,
    draw_multiedges,
    interactive_hairball_plot,
)

from .colors import (
    colors_default,
    colors_blue,
    all_color_names,
    hex_to_RGB,
    RGB_to_hex,
    linear_gradient,
    color_dict,
)

# Make matplotlib.pyplot available for convenience
from .multilayer import plt

__all__ = [
    # Main visualization functions
    "hairball_plot",
    "draw_multilayer_default",
    "draw_multiedges",
    "interactive_hairball_plot",
    # Color utilities
    "colors_default",
    "colors_blue",
    "all_color_names",
    "hex_to_RGB",
    "RGB_to_hex",
    "linear_gradient",
    "color_dict",
    # matplotlib.pyplot for convenience
    "plt",
]
