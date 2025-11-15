# Multilayer Flow Visualization Implementation

## Overview
This implementation adds a new "flow" or "alluvial" style visualization for multilayer networks to py3plex, as requested in the issue "new viz".

## What was implemented

### 1. Core Function: `draw_multilayer_flow()`
**Location:** `py3plex/visualization/multilayer.py`

A new high-level visualization function that creates layered flow diagrams showing:
- Each layer as a horizontal band (y-axis position determined by layer index)
- Nodes positioned along the x-axis within each layer
- Node activity encoded as color and size (default: intra-layer degree)
- Inter-layer connections as thick "flow ribbons" (Bezier curves)
- Flow ribbon width encodes aggregated edge weight/multiplicity

**Function signature:**
```python
def draw_multilayer_flow(
    graphs,                    # List of NetworkX graphs (one per layer)
    multilinks,                # Dict of edge_type -> list of inter-layer edges
    labels=None,               # Optional layer labels
    node_activity=None,        # Optional custom activity values
    ax=None,                   # Matplotlib axes (creates new if None)
    display=True,              # Whether to call plt.show()
    layer_gap=3.0,            # Vertical spacing between layers
    node_size=30,             # Base node marker size
    node_cmap="viridis",      # Colormap for node activity
    flow_alpha=0.3,           # Transparency for flow ribbons
    flow_min_width=0.2,       # Min line width for flows
    flow_max_width=4.0,       # Max line width for flows
    aggregate_by=(...),       # Aggregation strategy (for future extension)
    **kwargs
)
```

### 2. Integration with `visualize_network()`
**Location:** `py3plex/core/multinet.py`

Extended the `multi_layer_network.visualize_network()` method to support:
- `style='flow'` - New layered flow visualization
- `style='alluvial'` - Alias for 'flow' (common name in data viz)

**Usage:**
```python
network = multi_layer_network()
network.load_network("data.txt", input_type="multiedgelist")
network.visualize_network(style='flow')
```

### 3. Comprehensive Tests
**Location:** `tests/test_multilayer_visualizations.py`

Added two new test functions:
- `test_draw_multilayer_flow()` - Tests direct function usage with various parameters
- `test_visualize_network_flow_style()` - Tests integration via visualize_network

All 41 existing visualization tests continue to pass.

### 4. Example Script
**Location:** `examples/visualization/example_multilayer_flow.py`

Demonstrates three use cases:
1. Basic usage through `visualize_network(style='flow')`
2. Custom parameters with `draw_multilayer_flow()`
3. Side-by-side comparison with diagonal layout

## Technical Details

### Design Decisions

1. **Node Positioning:** Nodes are sorted by activity (descending) within each layer for better visual layout
2. **Activity Calculation:** Default uses intra-layer degree (with edge weights if available)
3. **Flow Aggregation:** Groups inter-layer edges by (source_layer, source_node, target_layer, target_node)
4. **Bezier Curves:** Reuses existing `bezier.draw_bezier()` utility for smooth flow ribbons
5. **Color Mapping:** Activity values normalized per-layer to [0,1] for consistent coloring

### Compatibility

- **Backward Compatible:** All existing functionality remains unchanged
- **Matplotlib Version:** Fixed deprecation warning for `get_cmap()` (works with matplotlib 3.7+)
- **NetworkX:** Works with standard NetworkX graph objects
- **Python:** Tested with Python 3.12

### Code Quality

- Follows existing code patterns from `draw_multilayer_default()` and `draw_multiedges()`
- Comprehensive docstrings with examples
- Type hints for key parameters
- Minimal changes (surgical approach)
- No breaking changes to existing APIs

## Usage Examples

### Example 1: Simple Usage
```python
from py3plex.core import multinet

network = multinet.multi_layer_network()
network.load_network("network.txt", input_type="multiedgelist")
network.visualize_network(style='flow', show=True)
```

### Example 2: Custom Parameters
```python
from py3plex.visualization.multilayer import draw_multilayer_flow

labels, graphs, multilinks = network.get_layers()

draw_multilayer_flow(
    graphs,
    multilinks,
    labels=labels,
    layer_gap=5.0,
    node_size=80,
    node_cmap="RdYlBu",
    flow_alpha=0.5,
    flow_max_width=6.0
)
```

## Visual Output

The visualization creates:
- **Horizontal bands** representing layers (labeled on the left)
- **Colored nodes** where color intensity indicates activity level
- **Smooth curves** connecting nodes between layers
- **Line thickness** proportional to flow strength (edge weight/count)

This style is particularly useful for:
- Understanding node participation across layers
- Visualizing flow of information/influence between layers
- Identifying key connectors in multilayer structures
- Creating publication-quality figures for multilayer analysis

## Testing

Run tests with:
```bash
pytest tests/test_multilayer_visualizations.py::test_draw_multilayer_flow -v
pytest tests/test_multilayer_visualizations.py::test_visualize_network_flow_style -v
```

Run example:
```bash
python examples/visualization/example_multilayer_flow.py
```

## Files Changed

1. `py3plex/visualization/multilayer.py` - Added `draw_multilayer_flow()` function (~220 lines)
2. `py3plex/core/multinet.py` - Extended `visualize_network()` to support flow style (~40 lines)
3. `tests/test_multilayer_visualizations.py` - Added 2 test functions (~70 lines)
4. `examples/visualization/example_multilayer_flow.py` - New example script (~180 lines)

**Total additions:** ~510 lines
**Lines modified:** ~5 lines (docstrings)

## Future Enhancements

The implementation is designed to be extensible:

1. **Community-based aggregation:** The `aggregate_by` parameter is reserved for future use to support aggregating flows by communities rather than individual nodes

2. **Custom node ordering:** Could add support for custom node ordering functions beyond activity-based sorting

3. **Flow bundling:** Could implement edge bundling algorithms to reduce visual clutter in dense networks

4. **Interactive features:** Could extend with plotly for interactive hovering and filtering

## Conclusion

This implementation successfully addresses the requirements in the issue:
- ✅ Shows layers as horizontal bands
- ✅ Positions nodes along x-axis within each layer
- ✅ Encodes intra-layer activity as node color/size
- ✅ Shows inter-layer edges as flow ribbons with width encoding
- ✅ Provides high-level API through visualize_network()
- ✅ Reuses existing utilities (Bezier curves)
- ✅ Follows existing code patterns
- ✅ Includes comprehensive tests and examples
