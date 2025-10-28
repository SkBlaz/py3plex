# Py3plex Examples

This directory contains 50+ example scripts demonstrating the capabilities of py3plex for multilayer network analysis.

## Directory Structure

Examples are organized into the following categories:

### 📁 [basic/](basic/)
Basic operations, IO, and network creation/loading
- Network input/output operations (edgelist, gpickle, etc.)
- Basic network wrappers and generators
- Layer extraction and inverse networks

**Key examples:**
- `example_IO.py` - Reading different input formats
- `example_new_io.py` - Modern IO operations
- `example_random_generator.py` - Random network generation

### 📁 [visualization/](visualization/)
Plotting, layouts, and visual representations
- Hairball plots and multilayer visualizations
- Layout algorithms and customization
- Animation and interactive plots

**Key examples:**
- `example_visualization.py` - Basic network visualization
- `example_multilayer_visualization.py` - Multilayer-specific plots
- `benchmark_layouts.py` - Comparing layout algorithms

### 📁 [community_detection/](community_detection/)
Community finding algorithms
- Louvain and Infomap algorithms
- Multiplex community detection
- Label propagation methods

**Key examples:**
- `example_community_detection.py` - Community detection with Louvain and Infomap
- `example_multiplex_community_detection.py` - Multiplex-specific methods

### 📁 [centrality_and_statistics/](centrality_and_statistics/)
Network metrics, centrality measures, and statistics
- Multilayer centrality measures
- Network statistics and properties
- Entanglement analysis
- Power-law computation

**Key examples:**
- `example_multilayer_centrality.py` - Comprehensive centrality measures
- `example_multilayer_statistics.py` - 17+ multilayer statistics
- `example_entanglement.py` - Entanglement analysis

### 📁 [embeddings/](embeddings/)
Node2vec, embeddings, and representation learning
- Node2vec embedding construction
- Embedding visualization (t-SNE)
- Custom embedding workflows

**Key examples:**
- `example_embedding_construction.py` - Build node2vec embeddings
- `example_n2v_embedding.py` - Node2vec integration

### 📁 [multilayer/](multilayer/)
Multilayer-specific operations, aggregation, and manipulation
- Supra-adjacency matrices
- Tensorial operations
- Multilayer aggregation
- Multiplex network manipulation
- Incidence matrix encoding

**Key examples:**
- `example_multilayer_functionality.py` - Core multilayer operations
- `example_multilayer_modularity.py` - Modularity analysis
- `example_supra_adjacency.py` - Supra-adjacency representations

### 📁 [dynamics/](dynamics/)
Spreading, random walks, and dynamic processes
- Random walk algorithms
- Spreading processes
- Multiplex dynamics

**Key examples:**
- `example_random_walks.py` - Comprehensive random walk examples
- `example_spreading.py` - Network spreading processes
- `example_multiplex_dynamics.py` - Dynamics on multiplex networks

### 📁 [decomposition_and_classification/](decomposition_and_classification/)
Network decomposition and machine learning
- Network decomposition methods
- Personalized PageRank (PPR)
- Classification workflows
- Semantic enrichment
- MultiXrank algorithms

**Key examples:**
- `example_decomposition_and_classification.py` - End-to-end classification
- `example_PPR.py` - Personalized PageRank for node classification
- `example_CBSSD.py` - Community-based semantic subgroup discovery

### 📁 [benchmarks_and_tutorials/](benchmarks_and_tutorials/)
Benchmarking, tutorials, and comparisons
- 10-minute tutorial
- Network comparison tools
- Statistical comparisons

**Key examples:**
- `tutorial_10min.py` - Quick start tutorial
- `compare_multilayer_networks_example.py` - Network comparison methods

## Running Examples

Most examples can be run directly from their subdirectories:

```bash
# From the examples/ directory
cd basic
python example_IO.py

# Or from the repository root
python examples/basic/example_IO.py
```

**Note:** Many examples assume they are run from their subdirectory and use relative paths to access datasets in `../datasets/` or `../../datasets/`. If you encounter path errors, adjust the paths or run from the appropriate directory.

## Dependencies

Some examples require external binaries:
- **node2vec**: Required for embedding examples (install from [node2vec repository](https://github.com/snap-stanford/snap/tree/master/examples/node2vec))
- **infomap**: Required for Infomap community detection (install from [mapequation.org](https://www.mapequation.org/infomap/))

These binaries are no longer bundled with py3plex. Examples will gracefully skip or use alternatives when binaries are not available.

## Contributing

When adding new examples:
1. Place them in the appropriate category subdirectory
2. Use descriptive filenames starting with `example_`
3. Include docstrings explaining what the example demonstrates
4. Update this README if adding a particularly important example

## Documentation

For more information, see:
- **Main documentation**: https://skblaz.github.io/py3plex/
- **API documentation**: Check the `docs/` directory
- **Algorithm citations**: See `docs/ALGORITHM_CITATIONS.md`
