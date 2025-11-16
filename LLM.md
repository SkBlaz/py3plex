# Py3plex LLM Development Checklist

![Py3plex Visualization Showcase](example_images/py3plex_showcase.png)

This file tracks development tasks and improvements for py3plex, particularly for LLM-assisted development.

## Selftest Coverage Status

✅ **Selftest enhanced (12 tests, covers main functionality)**
- Core dependencies (numpy, networkx, matplotlib, scipy, pandas)
- Basic graph creation and manipulation
- Visualization module
- Multilayer graph creation and layer operations
- Community detection (Louvain)
- File I/O (GraphML format)
- Centrality statistics (degree, betweenness, versatility, layer density)
- Multilayer manipulation (split_to_layers, aggregate_edges, subnetwork)
- Random generators (Erdős-Rényi multilayer networks)
- NetworkX wrapper (monoplex_nx_wrapper for centrality)
- New I/O system (schema-based JSON/CSV with MultiLayerGraph)
- Advanced multilayer statistics (node_activity, edge_overlap, layer_density, degree_vector)

**Examples covered by selftest:**
- ✅ basic/example_random_generator.py (random ER multilayer)
- ✅ basic/example_networkx_wrapper.py (nx wrapper centrality)
- ✅ basic/example_new_io.py (schema-based I/O)
- ✅ multilayer/example_vectorized_aggregation.py (aggregate_layers)
- ✅ multilayer/example_manipulation.py (add/remove nodes/edges)
- ✅ centrality_and_statistics/example_versatility.py (versatility centrality)
- ✅ centrality_and_statistics/example_multilayer_statistics.py (17 multilayer stats)

**Not included in selftest (requires external deps or slow):**
- Community detection examples requiring datasets (SKIP_CI: external_deps)
- Embeddings examples requiring node2vec binary (SKIP_CI: external_deps)
- Decomposition examples (SKIP_CI: slow)
- Dynamics examples requiring datasets (SKIP_CI: external_deps)
- Visualization examples with rendering (tested via module init check)

## Completed Tasks

✅ Add __version__ attribute to py3plex.__init__.py for version detection
✅ Document add_nodes() requires dict format with 'source' and 'type' keys
✅ Document add_edges() requires dict format with 'source', 'target', and 'layer' keys
✅ Add example code to multi_layer_network docstring showing dict-based API
✅ Implement __repr__ for multi_layer_network showing node/edge/layer counts
✅ Add type hints to multi_layer_network.add_nodes() and add_edges()
✅ Create quick reference guide for node dict structure in documentation
✅ Create quick reference guide for edge dict structure in documentation
Standardize method naming convention documentation (add_nodes vs add_node)
✅ Add to_networkx() method to multi_layer_network class
✅ Add from_networkx() class method to multi_layer_network
✅ Document layer parameter confusion in add_edges (layer vs layer_from vs layer_to)
Add validation for malformed edgelist files with clear error messages
Add warnings for files with missing values or irregular column counts
Implement round-trip test suite for all supported IO formats
Document expected behavior for self-loops in IO operations
Document expected behavior for negative weights in IO operations
✅ Add optional dependency documentation for python-louvain
✅ Add optional dependency documentation for igraph
✅ Expand help() docstrings for py3plex main module
✅ Expand help() docstrings for py3plex.core module
✅ Add inline examples to all public method docstrings (save_network, summary)
Create naming pattern guide for visualization methods
✅ Add tab completion hints via __all__ exports
Improve error message clarity for TypeError in add_nodes
Add contextual help messages to all custom exceptions
Rate and document all exception messages for clarity (target 4-5/5)
Add suggested fixes to exception messages where applicable
Document performance characteristics for large graphs (50K+ nodes)
Add memory usage guidelines for different graph sizes
Document expected load times for 1M+ edge datasets
Create performance benchmark reference table
Add stress test suite for memory leak detection
Implement memory profiling decorators for key operations
Add NetworkX compatibility layer documentation
Document attribute preservation in NetworkX conversions
Add pandas DataFrame conversion examples
Add numpy array conversion examples
Add igraph conversion examples (when available)
Document information loss in format conversions
Create conversion matrix showing supported paths
✅ Add hypergraph support or document lack thereof clearly
Add proper validation for NaN values in weights
Add clear warnings for edge case handling
Document directed vs undirected algorithm compatibility
Add pre-condition checks for algorithm requirements
Implement better error messages for missing nodes in algorithms
Add algorithm runtime complexity documentation
Create algorithm selection guide based on graph properties
✅ Add visualization performance guidelines for graph sizes
Document layout algorithm characteristics and use cases
Add timeout warnings for slow layout computations
Implement progress bars for long-running visualizations
Add support for unicode labels or document limitations
Document font rendering issues with CJK characters
Add layout algorithm comparison benchmarks
Create visualization quick start guide
Add method discovery guide using dir() output
Document return types for all public methods
Add constructor parameter documentation
Create API ergonomics improvement roadmap
Implement consistent parameter naming across methods
Add deprecation warnings for confusing parameter names
Create migration guide for API changes
Document relationship between NetworkX and py3plex APIs
Add code examples for common API confusion points
Implement input validation with actionable error messages
Add data type checking at API boundaries
Create comprehensive test suite for error conditions
Document expected exceptions for each method
Add error handling best practices guide
Create troubleshooting section in documentation
Implement centralized logging configuration
Add debug mode documentation
Create development environment setup guide
Add contribution guidelines for new algorithms
Document testing requirements for pull requests
Add benchmark requirements for performance-critical changes
Implement continuous benchmarking in CI
Add regression detection for performance
Create release checklist including benchmark validation
Document versioning strategy
Add changelog generation automation
Implement semantic versioning enforcement
Create backward compatibility policy
Add deprecation schedule documentation
