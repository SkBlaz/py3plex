# Algorithm Selection Guide

This guide helps you choose the right algorithm for your multilayer network analysis task.

## Community Detection

### When to use which algorithm?

**Louvain (Multilayer Modularity)**
- **Use when**: You want non-overlapping communities with fast computation
- **Best for**: Medium to large networks (100-100,000 nodes)
- **Complexity**: O(n log n) average case
- **Pros**: Fast, well-established, hierarchical communities
- **Cons**: Resolution limit, non-overlapping only
- **API**: `py3plex.algorithms.community_detection.multilayer_modularity.louvain_multilayer()`
- **Accepts seed**: Yes (`random_state` parameter)

**Infomap**
- **Use when**: You need overlapping communities and information-theoretic approach
- **Best for**: Networks with clear flow structure (citation, web links)
- **Complexity**: O(n log n) typical
- **Pros**: Overlapping communities, theoretically grounded
- **Cons**: Requires external binary or package installation
- **API**: `py3plex.algorithms.community_detection.community_wrapper.infomap_communities()`
- **Accepts seed**: No (currently)

**Label Propagation**
- **Use when**: You have very large networks and need speed
- **Best for**: Large networks (>100,000 nodes)
- **Complexity**: O(m) where m is edges
- **Pros**: Very fast, simple
- **Cons**: Non-deterministic, less stable
- **API**: Via NetworkX integration
- **Accepts seed**: No (currently)

## Centrality Measures

### Which centrality metric should I use?

**PageRank**
- **Use when**: Analyzing importance with link structure (web, citations)
- **Best for**: Directed networks with clear flow
- **Complexity**: O(n + m) per iteration
- **Interpretation**: Probability of random walker visiting node
- **API**: `py3plex.algorithms.node_ranking.node_ranking.py`

**Betweenness Centrality**
- **Use when**: Finding bridges and bottlenecks
- **Best for**: Small to medium networks (<5,000 nodes)
- **Complexity**: O(n³) or O(nm) with optimizations
- **Interpretation**: Fraction of shortest paths through node
- **Warning**: Very slow on large networks

**Closeness Centrality**
- **Use when**: Measuring accessibility or information spread speed
- **Best for**: Connected networks
- **Complexity**: O(n²) or O(nm)
- **Interpretation**: Inverse of average distance to all nodes
- **Note**: Requires connected components

**Degree Centrality**
- **Use when**: Quick importance approximation needed
- **Best for**: Any network size
- **Complexity**: O(n)
- **Interpretation**: Number of connections
- **Pros**: Very fast, intuitive

## Visualization

### Choosing a layout algorithm

**Force-Directed (Spring/ForceAtlas2)**
- **Use when**: You want intuitive, visually appealing layouts
- **Best for**: Small to medium networks (10-5,000 nodes)
- **Complexity**: O(n² log n) per iteration with Barnes-Hut
- **Pros**: Reveals structure, aesthetically pleasing
- **Cons**: Slow for large networks, non-deterministic
- **API**: `py3plex.visualization.layout_algorithms.compute_force_directed_layout()`
- **Accepts seed**: Yes (as of v0.95a)

**Random Layout**
- **Use when**: Need quick baseline or testing
- **Best for**: Any size
- **Complexity**: O(n)
- **Pros**: Instant, deterministic with seed
- **Cons**: No structural information
- **API**: `py3plex.visualization.layout_algorithms.compute_random_layout()`
- **Accepts seed**: Yes (as of v0.95a)

**Circular Layout**
- **Use when**: Emphasizing connections over spatial clustering
- **Best for**: Any size, especially with layered structure
- **Complexity**: O(n)
- **Pros**: Fast, deterministic, good for small networks
- **Cons**: Limited structural insight
- **API**: Via NetworkX (`nx.circular_layout()`)

**Spectral Layout**
- **Use when**: Want structure-based layout for medium networks
- **Best for**: 100-10,000 nodes
- **Complexity**: O(n²) due to eigenvalue computation
- **Pros**: Mathematically principled, reveals clusters
- **Cons**: Requires connected graph
- **API**: Via NetworkX (`nx.spectral_layout()`)

### Large network visualization strategies

For networks with >10,000 nodes:
1. **Aggregate view**: Visualize layer-aggregated network first
2. **Sampling**: Show representative subgraph
3. **Matrix visualization**: Use supra-adjacency matrix heatmap
4. **Layer-wise faceting**: Visualize each layer separately

## Network Construction

### Supra-Adjacency Matrix

**Sparse (Default)**
- **Use when**: Networks with >1,000 nodes or >5 layers
- **Memory**: O(non-zero edges)
- **API**: `network.get_supra_adjacency_matrix(mtype="sparse")`
- **Pros**: Scalable, memory-efficient
- **Cons**: Slower random access

**Dense**
- **Use when**: Small networks (<1,000 nodes, <5 layers) needing fast linear algebra
- **Memory**: O(n² × L²)
- **API**: `network.get_supra_adjacency_matrix(mtype="dense")`
- **Warning**: Will refuse construction above size thresholds without `force=True`

## Embeddings

**Node2Vec**
- **Use when**: Need feature vectors for downstream ML tasks
- **Best for**: Classification, clustering, link prediction
- **Complexity**: O(walks × walk_length × m)
- **Pros**: Flexible, captures structure and proximity
- **Cons**: Requires binary or pure Python alternative
- **API**: `py3plex.wrappers.node2vec_embedding`

## Performance Guidelines

| Network Size | Recommended Algorithms |
|--------------|----------------------|
| <100 nodes | Any algorithm works |
| 100-1,000 | Most algorithms except betweenness on >500 |
| 1,000-10,000 | Louvain, PageRank, degree centrality, sparse supra |
| 10,000-100,000 | Label propagation, degree only, matrix viz only |
| >100,000 | Streaming algorithms, sampling required |

## Reproducibility Checklist

To ensure reproducible results:
- ✅ Set `random_state` or `seed` parameter in all algorithms that support it
- ✅ Use `py3plex.utils.get_rng(seed)` for custom random operations
- ✅ Document software versions in publications
- ✅ Save network structure alongside results

## Getting Help

- **Examples**: See `examples/` directory for working code
- **API Docs**: https://skblaz.github.io/py3plex/
- **Issues**: https://github.com/SkBlaz/py3plex/issues
- **Papers**: Check `README.md` for citation information
