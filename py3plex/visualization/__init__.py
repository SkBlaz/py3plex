"""
Visualization module for py3plex.

This module provides visualization tools for multilayer networks, including:
- Multilayer network layouts (diagonal, hairball, force-directed)
- Pymnet style multilayer visualization (inspired by pymnet library)
- Sankey diagrams for inter-layer flows
- Supra-adjacency matrix heatmaps
- Color utilities for node and edge coloring
- Embedding visualization tools
- Layout algorithms

Convenient imports (recommended):
    from py3plex.visualization import hairball_plot, draw_multilayer_default, colors_default
    from py3plex.visualization import draw_multilayer_pymnet  # pymnet style visualization

Traditional imports (also supported for backwards compatibility):
    from py3plex.visualization.multilayer import hairball_plot, draw_multilayer_default
    from py3plex.visualization.colors import colors_default
    from py3plex.visualization.embedding_visualization import embedding_tools
    from py3plex.visualization.sankey import draw_multilayer_sankey
    from py3plex.visualization.pymnet_style import draw_multilayer_pymnet

Visualization API Design:
    All visualization functions follow these conventions:
    - Accept an optional `ax` parameter for the Matplotlib Axes to draw on
    - If `ax` is None, uses the current axes (plt.gca())
    - Return the Axes object to allow further customization
    - Default `display=False` to not call plt.show() automatically
    - Caller controls when to render/save the plot

Example:
    >>> import matplotlib.pyplot as plt
    >>> from py3plex.visualization import draw_multilayer_default
    >>> fig, ax = plt.subplots(figsize=(10, 10))
    >>> ax = draw_multilayer_default(graphs, ax=ax)
    >>> plt.savefig("multilayer.png")  # or plt.show()
"""

# Import most commonly used visualization functions for convenience
from .multilayer import (
    hairball_plot,
    draw_multilayer_default,
    draw_multiedges,
    supra_adjacency_matrix_plot,
    interactive_hairball_plot,
    interactive_diagonal_plot,
)

from .sankey import draw_multilayer_sankey

# Pymnet style visualization
from .pymnet_style import draw_multilayer_pymnet, to_multilayer_graph

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
    "supra_adjacency_matrix_plot",
    "draw_multilayer_sankey",
    "interactive_hairball_plot",
    "interactive_diagonal_plot",
    # Pymnet style visualization
    "draw_multilayer_pymnet",
    "to_multilayer_graph",
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
