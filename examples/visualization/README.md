# Visualization Examples

This directory contains examples for visualizing networks using various layouts and rendering techniques.

## Examples

### Basic Visualization

- **`example_visualization.py`** - Basic network plotting with hairball plots and force-directed layouts
- **`example_multilayer_visualization.py`** - Specialized visualizations for multilayer networks
- **`example_community_visualization.py`** - Visualizing community structure with colored nodes

### Advanced Visualization

- **`example_plot_intact.py`** - Visualizing large biological networks (IntAct dataset)
- **`example_twitter_multiplex_visualization.py`** - Multiplex network visualization with Twitter data
- **`example_animation.py`** - Creating animated network visualizations

### Layout Algorithms

- **`benchmark_layouts.py`** - Comparing different layout algorithms (force-directed, circular, etc.)

## Key Features

- **Hairball plots**: Intuitive network visualizations
- **Force-directed layouts**: Physics-based node positioning
- **Community coloring**: Highlight network structure
- **Custom coordinates**: Use embeddings or other coordinates for layout
- **Multilayer-specific**: Visualize layer structure

## Usage

```bash
# Basic visualization
python example_visualization.py

# Visualize with community colors
python example_community_visualization.py

# Compare layout algorithms
python benchmark_layouts.py
```

## Common Parameters

Most visualization examples support:
- `layout_algorithm`: Choose from "force", "circular", "random", "custom_coordinates"
- `iterations`: Number of layout iterations for force-directed algorithms
- `scale_by_size`: Scale node size by degree
- `color_list`: Custom node colors (e.g., for communities)

## Related Directories

- See [../community_detection/](../community_detection/) for finding communities to visualize
- See [../embeddings/](../embeddings/) for using embeddings as visualization coordinates
