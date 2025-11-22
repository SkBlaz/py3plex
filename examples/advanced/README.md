# Advanced Topics

This directory contains examples for advanced multilayer network analysis techniques. These examples cover specialized topics like embeddings, dynamics, decomposition, and tensor operations.

## Examples by Topic

### Network Embeddings
Transform networks into vector representations for machine learning:
- **`example_embedding_construction.py`** - Construct Node2Vec embeddings
- **`example_embedding_visualization.py`** - Visualize network embeddings
- **`example_n2v_embedding.py`** - Node2Vec embedding examples

### Network Dynamics and Processes
Simulate processes on networks:
- **`example_random_walks.py`** - Random walks on multilayer networks
- **`example_spreading.py`** - Simple spreading/diffusion processes
- **`example_sir_multiplex.py`** - SIR epidemic simulation on multiplex networks
- **`example_multiplex_dynamics.py`** - General dynamics on multiplex networks

### Network Decomposition and Classification
Break down networks and classify nodes:
- **`example_decomposition_and_classification.py`** - Decompose networks for node classification
- **`example_network_decomposition.py`** - Network decomposition techniques
- **`example_network_decomposition_different_meta_paths.py`** - Decomposition with meta-paths
- **`example_decomposition_ground_truth.py`** - Decomposition with ground truth evaluation
- **`example_semantic_enrichment.py`** - Enrich networks with semantic information
- **`example_CBSSD.py`** - Cross-layer Betweenness-based Structural Similarity Decomposition
- **`example_PPR.py`** - Personalized PageRank examples

### Advanced Network Operations
Specialized multilayer operations:
- **`example_inverse_network.py`** - Create inverse (transposed) networks
- **`example_layer_extraction.py`** - Extract and analyze individual layers
- **`example_manipulation.py`** - Advanced network manipulation techniques
- **`example_multiplex_aggregate.py`** - Aggregate multiplex networks
- **`example_multilayer_vectorized_aggregation.py`** - Vectorized aggregation (high performance)
- **`example_vectorized_aggregation.py`** - Vectorized multilayer operations

### Tensor and Matrix Operations
Work with tensorial representations:
- **`example_tensorial_manipulation.py`** - Tensor-based network operations
- **`example_tensorial_manipulation_headless.py`** - Tensor operations (non-interactive)
- **`example_supra_adjacency.py`** - Supra-adjacency matrix operations
- **`example_incidence_gadget_encoding.py`** - Incidence gadget encoding for multiplex networks
- **`example_numeric_encoding.py`** - Numeric encoding schemes

### Geometric Network Analysis
Apply differential geometry to networks:
- **`example_ricci_curvature.py`** - Ollivier-Ricci curvature and Ricci flow

## When to Use These Examples

### Use Embeddings When:
- You need feature representations for ML tasks
- You want to visualize high-dimensional networks
- You need to compute node similarities

### Use Dynamics When:
- Modeling information/disease spread
- Studying cascading processes
- Analyzing temporal evolution

### Use Decomposition When:
- Networks are heterogeneous
- You need to classify nodes
- You want to simplify complex networks

### Use Tensor Operations When:
- Working with mathematical formulations
- Implementing custom algorithms
- Optimizing performance

## Performance Notes

⚠️ **Note**: Many examples in this category:
- May require significant computation time
- Might need external datasets
- Can be memory-intensive

Most are marked with `SKIP_CI: slow` or `SKIP_CI: external_deps`.

## Related Examples

- [Network Analysis](../network_analysis/) - Basic metrics and centrality
- [Communities](../communities/) - Community detection
- [Workflows](../workflows/) - Complete analysis pipelines
