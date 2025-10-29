# Multilayer Network Examples

This directory contains examples for multilayer-specific operations, aggregation, and manipulation.

## Examples

### Core Multilayer Operations

- **`example_multilayer_functionality.py`** - Fundamental multilayer network operations
- **`example_multilayer_modularity.py`** - Modularity analysis for multilayer networks
- **`example_supra_adjacency.py`** - Working with supra-adjacency matrix representations

### Aggregation and Manipulation

- **`example_multilayer_vectorized_aggregation.py`** - Efficient vectorized operations on multilayer networks
- **`example_vectorized_aggregation.py`** - Additional vectorized aggregation examples
- **`example_multiplex_aggregate.py`** - Aggregating multiplex networks into single-layer representations
- **`example_manipulation.py`** - Manipulating multilayer network structure

### Advanced Representations

- **`example_tensorial_manipulation.py`** - Tensor-based operations on multilayer networks
- **`example_incidence_gadget_encoding.py`** - Incidence matrix and gadget encoding methods
- **`example_numeric_encoding.py`** - Numeric encoding schemes for multilayer networks

### Input/Output

- **`example_multiplex_generic_parser.py`** - Parsing multiplex network formats

## Key Concepts

### Multilayer Networks
Networks with multiple types of edges (layers) connecting the same set of nodes:
- **Multiplex**: Same nodes, different edge types
- **Interconnected**: Different nodes per layer, with inter-layer connections
- **Temporal**: Layers represent time slices

### Supra-Adjacency Matrix
A block matrix representation where:
- Diagonal blocks = intra-layer adjacencies
- Off-diagonal blocks = inter-layer connections

### Aggregation
Combining multiple layers into a single network:
- **Unweighted**: Union of edges across layers
- **Weighted**: Sum edge weights across layers
- **Max**: Maximum weight per edge
- **Mean**: Average weight per edge

## Usage

```bash
# Core multilayer operations
python example_multilayer_functionality.py

# Work with supra-adjacency matrices
python example_supra_adjacency.py

# Aggregate multiple layers
python example_multiplex_aggregate.py

# Tensor operations
python example_tensorial_manipulation.py
```

## Common Operations

Examples demonstrate:
- Creating multilayer networks from scratch
- Converting between representations (edgelist ↔ supra-adjacency ↔ tensor)
- Layer extraction and manipulation
- Aggregation across layers
- Computing multilayer-specific metrics

## Related Directories

- See [../basic/](../basic/) for loading multilayer networks
- See [../centrality_and_statistics/](../centrality_and_statistics/) for multilayer metrics
- See [../community_detection/](../community_detection/) for multilayer community detection
- See [../visualization/](../visualization/) for multilayer visualization
