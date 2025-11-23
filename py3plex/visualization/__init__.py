"""
Visualization module for py3plex.

This module provides visualization tools for multilayer networks, including:
- Multilayer network layouts (diagonal, hairball, force-directed)
- Sankey diagrams for inter-layer flows
- Color utilities for node and edge coloring
- Embedding visualization tools
- Layout algorithms

Convenient imports (recommended):
    from py3plex.visualization import hairball_plot, draw_multilayer_default, colors_default

Traditional imports (also supported for backwards compatibility):
    from py3plex.visualization.multilayer import hairball_plot, draw_multilayer_default
    from py3plex.visualization.colors import colors_default
    from py3plex.visualization.embedding_visualization import embedding_tools
    from py3plex.visualization.sankey import draw_multilayer_sankey
"""

# Import most commonly used visualization functions for convenience
from .multilayer import (
    hairball_plot,
    draw_multilayer_default,
    draw_multiedges,
    interactive_hairball_plot,
    interactive_diagonal_plot,
)

from .sankey import draw_multilayer_sankey

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
    "draw_multilayer_sankey",
    "interactive_hairball_plot",
    "interactive_diagonal_plot",
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
