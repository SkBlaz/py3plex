# Visualization Module Import Guide

The py3plex visualization module has been enhanced to provide convenient imports while maintaining full backwards compatibility.

## What Changed

The `py3plex.visualization` module now exports commonly used functions and classes directly, making imports cleaner and more intuitive.

### Before (still works!)

```python
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from py3plex.visualization.embedding_visualization import embedding_tools
```

### After (new convenience imports)

```python
from py3plex.visualization import hairball_plot, plt, colors_default
# embedding_tools still imported from submodule:
from py3plex.visualization.embedding_visualization import embedding_tools
```

## Available Convenience Imports

### Visualization Functions
- `hairball_plot` - Create hairball/force-directed network visualizations
- `draw_multilayer_default` - Draw multilayer networks with diagonal layout
- `draw_multiedges` - Draw networks with multiple edges between nodes
- `interactive_hairball_plot` - Interactive hairball visualization

### Color Utilities
- `colors_default` - Default color palette (list of 200 colors)
- `colors_blue` - Blue color palette
- `all_color_names` - Dictionary of all named colors
- `hex_to_RGB` - Convert hex color to RGB
- `RGB_to_hex` - Convert RGB to hex color
- `linear_gradient` - Generate color gradients
- `color_dict` - Create color dictionaries

### Other
- `plt` - matplotlib.pyplot for convenience

## Examples

### Basic Visualization

```python
from py3plex.visualization import hairball_plot, colors_default, plt
from py3plex.core import multinet

# Create a network
network = multinet.multi_layer_network()
# ... load or create network ...

# Get network representation
colors, graph = network.get_layers(style="hairball")

# Plot
hairball_plot(graph, colors)
plt.show()
```

### Using Color Utilities

```python
from py3plex.visualization import hex_to_RGB, RGB_to_hex, linear_gradient

# Convert colors
rgb = hex_to_RGB("#FF0000")  # [255, 0, 0]
hex_color = RGB_to_hex([255, 0, 0])  # "#ff0000"

# Generate gradient
gradient = linear_gradient("#FF0000", "#0000FF", n=10)
```

## Backwards Compatibility

All existing import patterns continue to work exactly as before. The new exports are provided for convenience and do not break any existing code.

```python
# Old way - still works perfectly
from py3plex.visualization.multilayer import hairball_plot
from py3plex.visualization.colors import colors_default

# New way - also works
from py3plex.visualization import hairball_plot, colors_default

# Both give you the exact same objects
```

## Module Structure

```
py3plex.visualization/
├── __init__.py (exports convenience imports)
├── multilayer.py (main visualization functions)
├── colors.py (color utilities)
├── embedding_visualization/
│   ├── __init__.py (exports embedding modules)
│   ├── embedding_tools.py
│   └── embedding_visualization.py
├── bezier.py (bezier curve utilities)
├── polyfit.py (polynomial fitting utilities)
└── layout_algorithms.py (layout computation)
```

## Testing

The new imports are covered by comprehensive tests in `tests/test_visualization_imports.py`:
- Convenience import functionality
- Backwards compatibility verification  
- Module structure validation
- Import path equivalence checks

Run the tests:
```bash
python -m pytest tests/test_visualization_imports.py -v
```

## Migration Guide

No migration needed! Your existing code will continue to work. However, you may want to simplify imports where possible:

### Optional Simplifications

```python
# Instead of:
from py3plex.visualization.multilayer import hairball_plot, draw_multilayer_default
from py3plex.visualization.colors import colors_default

# You can now write:
from py3plex.visualization import hairball_plot, draw_multilayer_default, colors_default
```

This is purely optional and for convenience - both styles are fully supported.
