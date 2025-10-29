# CrossHair-Testable Pure Functions

This document lists pure or deterministic functions in py3plex that are suitable for testing with CrossHair.

## Selection Criteria

Functions included in this list meet the following requirements:

1. **Clear input/output types**: Functions have complete type hints for arguments and return values
2. **No I/O or global state**: Functions do not perform file I/O, logging, or modify global variables
3. **Small enough for symbolic exploration**: Functions are reasonably sized (typically < 80 lines)
4. **Deterministic behavior**: Functions produce consistent outputs for given inputs

## Function List

### Algorithms/Statistics

- `py3plex/algorithms/statistics/basic_statistics.py:identify_n_hubs`
  - Identify the top N hub nodes in a network based on degree centrality.
  
- `py3plex/algorithms/statistics/basic_statistics.py:core_network_statistics`
  - Compute core statistics for a network.
  
- `py3plex/algorithms/statistics/topology.py:basic_pl_stats`
  - Calculate basic power law statistics for a degree sequence.
  
- `py3plex/algorithms/statistics/stats_comparison.py:bootstrap_confidence_interval`
  - Compute bootstrap confidence intervals for network metrics.
  
- `py3plex/algorithms/statistics/critical_distances.py:center`
  - Computes free space on the figure on both sides.
  
- `py3plex/algorithms/statistics/critical_distances.py:name_length`
  - Calculate length of name string.
  
- `py3plex/algorithms/statistics/critical_distances.py:remove_backslash`
  - Remove backslash characters from strings.

### Core/Converters

- `py3plex/core/converters.py:compute_layout`
  - Compute and normalize layout for a network.

### Core/Supporting

- `py3plex/core/supporting.py:split_to_layers`
  - Split a multilayer network into separate layer subgraphs.
  
- `py3plex/core/supporting.py:add_mpx_edges`
  - Add multiplex edges between corresponding nodes across layers.

### Core/Parsers

- `py3plex/core/parsers.py:parse_gml`
  - Parse a GML network file.
  
- `py3plex/core/parsers.py:parse_gpickle_biomine`
  - Gpickle parser for biomine graphs.
  
- `py3plex/core/parsers.py:parse_matrix`
  - Parser for matrices.
  
- `py3plex/core/parsers.py:parse_matrix_to_nx`
  - Parser for matrices to NetworkX graph.
  
- `py3plex/core/parsers.py:parse_multiedge_tuple_list`
  - Parse a list of edge tuples into a multilayer network.
  
- `py3plex/core/parsers.py:parse_network`
  - A wrapper method for available parsers.
  
- `py3plex/core/parsers.py:parse_nx`
  - Core parser for NetworkX objects.
  
- `py3plex/core/parsers.py:save_gpickle`
  - Save network as gpickle file.
  
- `py3plex/core/parsers.py:load_temporal_edge_information`
  - Load temporal edge information from file.

### Core/Random Generators

- `py3plex/core/random_generators.py:random_multilayer_ER`
  - Generate random multilayer Erdős-Rényi network.
  
- `py3plex/core/random_generators.py:random_multiplex_ER`
  - Generate random multiplex Erdős-Rényi network.
  
- `py3plex/core/random_generators.py:random_multiplex_generator`
  - Generate a multiplex network from a random bipartite graph.

### Utils

- `py3plex/utils.py:get_rng`
  - Get a NumPy random number generator with optional seed.
  
- `py3plex/utils.py:deprecated`
  - Decorator to mark functions/methods as deprecated.
  
- `py3plex/utils.py:warn_if_deprecated`
  - Issue a deprecation warning for a feature.

### Visualization

- `py3plex/visualization/layout_algorithms.py:compute_random_layout`
  - Compute a random layout for the graph.

## Summary

**Total: 27 functions identified**

These functions are distributed across:
- **7** statistics/algorithm functions
- **3** converter functions  
- **9** parser functions
- **3** random generator functions
- **3** utility functions
- **2** visualization functions

## Usage with CrossHair

To test these functions with CrossHair, you can use:

```bash
# Test a specific function
crosshair check py3plex.utils.get_rng

# Test all functions in a module
crosshair check py3plex.utils

# Watch mode for continuous testing
crosshair watch py3plex.algorithms.statistics.basic_statistics

# Test with increased timeout for complex functions
crosshair check --per_condition_timeout=10 py3plex.core.converters.compute_layout
```

## Notes

- Some functions may require additional contracts or preconditions to be effectively tested with CrossHair
- Functions working with NetworkX graphs may need graph construction contracts
- Random generator functions may benefit from seed-based testing strategies
- Parser functions have type hints but involve I/O, so they're listed but may have limited CrossHair applicability

## Next Steps

1. Add CrossHair contracts (`@precondition`, `@postcondition`) to these functions
2. Create dedicated CrossHair test configurations
3. Integrate CrossHair checks into CI/CD pipeline
4. Document any limitations or edge cases discovered during testing
