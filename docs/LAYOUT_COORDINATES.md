# Visualization Layout Coordinate Conventions

This document describes the coordinate systems and conventions used in py3plex visualization layouts, particularly for multilayer networks.

## Table of Contents

1. [Overview](#overview)
2. [Coordinate Systems](#coordinate-systems)
3. [Single-Layer Layouts](#single-layer-layouts)
4. [Multilayer Layouts](#multilayer-layouts)
5. [Edge Rendering](#edge-rendering)
6. [Examples](#examples)

## Overview

Py3plex uses different coordinate conventions depending on the type of network and visualization:

- **Single-layer networks**: Standard 2D coordinates (x, y)
- **Multilayer networks**: 2D or 3D coordinates depending on projection
- **Diagonal projection**: Layers arranged diagonally with 2D coordinates
- **3D visualization**: Full 3D coordinates (x, y, z) where z represents layer

## Coordinate Systems

### 2D Coordinate System (Default)

```
y
↑
│     Node positions
│     (x, y) tuples
│
└──────────→ x
(0,0)
```

**Properties:**
- Origin: Lower-left corner (0, 0) or center depending on layout
- X-axis: Horizontal, increases to the right
- Y-axis: Vertical, increases upward
- Range: Typically normalized to [0, 1] or [-1, 1]

### 3D Coordinate System

```
z (layer)
↑
│  y
│ ↗
│/
└──────────→ x
```

**Properties:**
- X, Y: Node positions within layer
- Z: Layer index or offset
- Used for true 3D visualizations (rare, mostly use 2D projections)

## Single-Layer Layouts

### Force-Directed Layout

**Algorithm**: ForceAtlas2 or NetworkX spring layout

**Coordinates**:
- Computed by simulating physical forces
- Nodes repel each other
- Edges act as springs
- Result depends on initial positions and iteration count

**Normalization**:
```python
from py3plex.visualization.layout_algorithms import compute_force_directed_layout

# Coordinates returned as dictionary: {node: [x, y]}
positions = compute_force_directed_layout(G, seed=42)

# Normalize to [0, 1] if needed
x_vals = [pos[0] for pos in positions.values()]
y_vals = [pos[1] for pos in positions.values()]
x_min, x_max = min(x_vals), max(x_vals)
y_min, y_max = min(y_vals), max(y_vals)

normalized = {
    node: [
        (pos[0] - x_min) / (x_max - x_min),
        (pos[1] - y_min) / (y_max - y_min)
    ]
    for node, pos in positions.items()
}
```

### Random Layout

**Algorithm**: Random uniform distribution

**Coordinates**:
```python
from py3plex.visualization.layout_algorithms import compute_random_layout

# Coordinates in [0, 1] × [0, 1]
positions = compute_random_layout(G, seed=42)
# Returns: {node: [x, y]} where 0 <= x, y <= 1
```

### Circular Layout

**Algorithm**: Nodes arranged in a circle

**Coordinates**:
- Nodes placed on unit circle
- Angular spacing: 360° / num_nodes
- Center at origin or (0.5, 0.5)

## Multilayer Layouts

### Diagonal Projection (Default)

The most common multilayer visualization in py3plex arranges layers diagonally.

**Coordinate Mapping**:
```
Layer 0    Layer 1    Layer 2
   ●          ●          ●
   │ ╲        │ ╲        │
   │  ╲       │  ╲       │
   ●   ●      ●   ●      ●
        ╲          ╲
         ╲          ╲
```

**Formula**:
For a node at position `(x_layer, y_layer)` in layer `k`:
```python
x_display = x_layer + k * layer_spacing_x
y_display = y_layer - k * layer_spacing_y
```

**Default Spacing** (from config.py):
```python
MULTILAYER_LAYER_SPACING = 1.5  # Distance between layer projections
```

**Example**:
```python
from py3plex.visualization import multilayer

# Nodes in layer 0 at (0.5, 0.5)
# With spacing 1.5, appear at:
#   Layer 0: (0.5, 0.5)
#   Layer 1: (0.5 + 1.5, 0.5 - 1.5) = (2.0, -1.0)
#   Layer 2: (0.5 + 3.0, 0.5 - 3.0) = (3.5, -2.5)
```

### Vertical Stack Layout

Alternative layout stacking layers vertically:

**Coordinate Mapping**:
```
Layer 2  ●───●───●
         
Layer 1  ●───●───●
         
Layer 0  ●───●───●
```

**Formula**:
```python
x_display = x_layer
y_display = y_layer + k * vertical_spacing
```

### Horizontal Layout

Layers arranged side-by-side:

**Coordinate Mapping**:
```
●───●   ●───●   ●───●
│   │   │   │   │   │
●───●   ●───●   ●───●
Layer0  Layer1  Layer2
```

**Formula**:
```python
x_display = x_layer + k * (layer_width + horizontal_gap)
y_display = y_layer
```

## Edge Rendering

### Intralayer Edges

**Definition**: Edges within the same layer

**Coordinates**: Both endpoints in same layer coordinate space
```python
# Edge from node_i to node_j in layer k
start = (x_i + k*spacing, y_i - k*spacing)
end = (x_j + k*spacing, y_j - k*spacing)
```

**Rendering**: Straight lines or Bezier curves (for clarity)

### Interlayer Edges

**Definition**: Edges connecting nodes across layers

**Coordinates**: Endpoints in different layer spaces
```python
# Edge from node_i in layer k to node_j in layer k+1
start = (x_i + k*spacing, y_i - k*spacing)
end = (x_j + (k+1)*spacing, y_j - (k+1)*spacing)
```

**Rendering**: 
- Typically dashed lines to distinguish from intralayer edges
- Lower alpha to reduce visual clutter
- May use different colors

**Example**:
```python
from py3plex import config

# Intralayer edge styling
intralayer_style = {
    'alpha': config.DEFAULT_EDGE_ALPHA,  # 0.13
    'width': config.DEFAULT_EDGE_WIDTH,  # 1.0
    'style': 'solid'
}

# Interlayer edge styling
interlayer_style = {
    'alpha': config.DEFAULT_LAYER_ALPHA,  # 0.15
    'width': config.DEFAULT_LAYER_EDGE_WIDTH,  # 0.3
    'style': 'dashed'
}
```

## Node Positioning in Multilayer Networks

### Same Node Across Layers

For multiplex networks, the same node appears in multiple layers:

**Convention**: Use **same local coordinates** in each layer
```python
# Node 'A' position in all layers
node_pos_local = (0.3, 0.7)  # Local coordinates

# Display positions
layer_0_pos = (0.3, 0.7)
layer_1_pos = (0.3 + spacing, 0.7 - spacing)
layer_2_pos = (0.3 + 2*spacing, 0.7 - 2*spacing)
```

**Rationale**: Maintains visual consistency and highlights layer structure

### Different Nodes Across Layers

For general multilayer networks, nodes may be different in each layer:

**Convention**: Compute layout independently per layer or use global optimization

## Examples

### Example 1: Simple Two-Layer Network

```python
import networkx as nx
from py3plex.core.multinet import multi_layer_network

# Create network
mlnet = multi_layer_network()

# Layer 0: Triangle
G0 = nx.Graph([(1, 2), (2, 3), (3, 1)])
mlnet.add_layer(G0, layer_id=0)

# Layer 1: Line
G1 = nx.Graph([(1, 2), (2, 3)])
mlnet.add_layer(G1, layer_id=1)

# Add interlayer edges
mlnet.add_edges([(1, 1, 0, 1), (2, 2, 0, 1), (3, 3, 0, 1)])

# Visualize
# Node positions will be computed with diagonal projection
# Layer 0 at (x, y)
# Layer 1 at (x + spacing, y - spacing)
```

### Example 2: Custom Layout

```python
import matplotlib.pyplot as plt
from py3plex import config

# Define custom positions
positions = {
    (1, 0): (0.0, 0.0),  # Node 1, layer 0
    (2, 0): (1.0, 0.0),
    (3, 0): (0.5, 0.87),
    (1, 1): (2.0, -2.0),  # Node 1, layer 1 (shifted)
    (2, 1): (3.0, -2.0),
    (3, 1): (2.5, -1.13),
}

# Plot with custom positions
fig, ax = plt.subplots(figsize=(10, 6))

# Use config for consistent styling
node_colors = config.get_color_palette('rainbow')
node_size = config.DEFAULT_NODE_SIZE * 10

# Draw nodes
for (node, layer), (x, y) in positions.items():
    ax.scatter(x, y, s=node_size, c=[node_colors[layer]], 
               alpha=config.DEFAULT_NODE_ALPHA)
```

### Example 3: Normalized Coordinates

```python
def normalize_positions(positions, target_range=(0, 1)):
    """Normalize positions to target range."""
    coords = list(positions.values())
    x_coords = [c[0] for c in coords]
    y_coords = [c[1] for c in coords]
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    normalized = {}
    for node, (x, y) in positions.items():
        norm_x = (x - x_min) / x_range if x_range > 0 else 0.5
        norm_y = (y - y_min) / y_range if y_range > 0 else 0.5
        
        # Scale to target range
        target_min, target_max = target_range
        target_span = target_max - target_min
        norm_x = target_min + norm_x * target_span
        norm_y = target_min + norm_y * target_span
        
        normalized[node] = (norm_x, norm_y)
    
    return normalized
```

## Best Practices

1. **Always specify seed** for reproducibility:
   ```python
   positions = compute_force_directed_layout(G, seed=config.RANDOM_SEED)
   ```

2. **Normalize coordinates** for consistent visualization:
   ```python
   if config.MULTILAYER_NORMALIZE_COORDS:
       positions = normalize_positions(positions)
   ```

3. **Use config defaults** for consistency:
   ```python
   from py3plex import config
   layer_spacing = config.MULTILAYER_LAYER_SPACING
   ```

4. **Document coordinate transformations** in custom layouts

5. **Test with different network sizes** to ensure scalability

## Troubleshooting

### Nodes Overlap
- Increase `layer_spacing` in diagonal projection
- Use force-directed layout with higher iterations
- Increase figure size

### Edges Not Visible
- Increase edge alpha: `config.DEFAULT_EDGE_ALPHA = 0.3`
- Increase edge width: `config.DEFAULT_EDGE_WIDTH = 2.0`
- Use solid lines for interlayer edges

### Layout Not Reproducible
- Always specify seed: `seed=42`
- Use same layout algorithm version
- Check for floating-point precision issues

## References

- MuxViz: De Domenico et al. (2015). Journal of Complex Networks, 3(2), 159-176.
- ForceAtlas2: Jacomy et al. (2014). PloS one, 9(6), e98679.

For implementation details, see:
- `py3plex/visualization/layout_algorithms.py`
- `py3plex/visualization/multilayer.py`
- `py3plex/config.py`
