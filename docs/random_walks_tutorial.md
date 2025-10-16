# Random Walk Primitives Tutorial

This tutorial covers the comprehensive random walk functionality in Py3plex, designed for graph-based algorithms like Node2Vec, DeepWalk, and diffusion processes.

## Table of Contents

1. [Introduction](#introduction)
2. [Basic Random Walks](#basic-random-walks)
3. [Node2Vec Biased Walks](#node2vec-biased-walks)
4. [Multiple Walk Generation](#multiple-walk-generation)
5. [Multilayer Network Walks](#multilayer-network-walks)
6. [Advanced Topics](#advanced-topics)

## Introduction

Random walks are fundamental for many graph algorithms:

- **Node2Vec** and **DeepWalk**: Learn node embeddings
- **Personalized PageRank**: Compute node importance
- **Diffusion processes**: Model information propagation
- **Community detection**: Identify network structure

### Key Features

✅ **Weighted edge sampling** - Respects edge weights automatically  
✅ **Node2Vec biased walks** - Second-order walks with p/q parameters  
✅ **Deterministic seeding** - Reproducible results across runs  
✅ **Multilayer support** - Layer-aware walks with cross-layer transitions  
✅ **Comprehensive testing** - 41 tests validating correctness properties  

## Basic Random Walks

### Simple Example

```python
from py3plex.algorithms.general.walkers import basic_random_walk
import networkx as nx

# Create a graph
G = nx.karate_club_graph()

# Perform a random walk
walk = basic_random_walk(
    G, 
    start_node=0, 
    walk_length=10,
    seed=42  # for reproducibility
)

print(f"Walk: {walk}")
# Output: [0, 13, 1, 19, 1, 0, 31, 32, 31, 24, 27]
```

### Weighted Graphs

Edge weights are automatically used when `weighted=True` (default):

```python
# Create weighted graph
G = nx.Graph()
G.add_weighted_edges_from([
    (0, 1, 10.0),  # high weight -> visited more often
    (0, 2, 1.0),   # low weight -> visited less often
])

# Weighted walk respects edge weights
walk = basic_random_walk(G, 0, walk_length=20, weighted=True, seed=42)

# Unweighted walk ignores weights (uniform transitions)
walk_uniform = basic_random_walk(G, 0, walk_length=20, weighted=False, seed=42)
```

### Reproducibility

```python
# Same seed produces identical walks
walk1 = basic_random_walk(G, 0, 50, seed=42)
walk2 = basic_random_walk(G, 0, 50, seed=42)
assert walk1 == walk2  # ✓ Identical

# Different seeds produce different walks
walk3 = basic_random_walk(G, 0, 50, seed=123)
assert walk1 != walk3  # ✓ Different
```

## Node2Vec Biased Walks

Second-order random walks with return parameter `p` and in-out parameter `q`.

### Understanding Parameters

When transitioning from node `t → v → x`:

- **If x == t** (return): probability ∝ `weight / p`
- **If x is neighbor of t** (stay close): probability ∝ `weight / 1`
- **If x is not neighbor of t** (explore): probability ∝ `weight / q`

**Parameter Effects:**

| Parameter | Effect | Behavior |
|-----------|--------|----------|
| `p > 1` | Discourage return | Explore forward |
| `p < 1` | Encourage return | Backtrack frequently |
| `q > 1` | Discourage exploration | Stay local (BFS-like) |
| `q < 1` | Encourage exploration | Venture far (DFS-like) |
| `p = q = 1` | No bias | Standard random walk |

### Basic Usage

```python
from py3plex.algorithms.general.walkers import node2vec_walk
import networkx as nx

G = nx.karate_club_graph()

# Balanced walk (no bias)
walk_balanced = node2vec_walk(G, 0, walk_length=20, p=1.0, q=1.0, seed=42)

# BFS-like walk (stay local)
walk_bfs = node2vec_walk(G, 0, walk_length=20, p=1.0, q=2.0, seed=42)

# DFS-like walk (explore outward)
walk_dfs = node2vec_walk(G, 0, walk_length=20, p=1.0, q=0.5, seed=42)
```

### Exploring vs Backtracking

```python
# Triangle graph
G = nx.Graph()
G.add_edges_from([(0, 1), (1, 2), (2, 0)])

# Low p, high q: tends to backtrack
walk_backtrack = node2vec_walk(G, 0, walk_length=20, p=0.1, q=10.0, seed=42)

# High p, low q: tends to explore outward
walk_explore = node2vec_walk(G, 0, walk_length=20, p=10.0, q=0.1, seed=42)
```

## Multiple Walk Generation

Generate multiple walks efficiently with deterministic seeding.

### From All Nodes

```python
from py3plex.algorithms.general.walkers import generate_walks
import networkx as nx

G = nx.karate_club_graph()

# Generate 10 walks from each node
walks = generate_walks(
    G,
    num_walks=10,
    walk_length=10,
    seed=42
)

print(f"Total walks: {len(walks)}")  # 340 (34 nodes × 10 walks)
```

### From Specific Nodes

```python
# Generate walks only from nodes 0, 1, 2
walks = generate_walks(
    G,
    num_walks=5,
    walk_length=15,
    start_nodes=[0, 1, 2],
    seed=42
)

print(f"Total walks: {len(walks)}")  # 15 (3 nodes × 5 walks)
```

### With Node2Vec Bias

```python
# Generate biased walks
walks = generate_walks(
    G,
    num_walks=10,
    walk_length=20,
    p=0.5,
    q=2.0,
    seed=42
)
```

### Edge Sequences

```python
# Return walks as edge sequences
edge_walks = generate_walks(
    G,
    num_walks=5,
    walk_length=10,
    return_edges=True,
    seed=42
)

# Each walk is a list of edges
print(edge_walks[0])  # [(0, 3), (3, 2), (2, 1), ...]
```

## Multilayer Network Walks

Perform walks on multilayer networks with layer constraints.

### Layer-Constrained Walks

```python
from py3plex.algorithms.general.walkers import layer_specific_random_walk
import networkx as nx

# Create graph with layer information in node names
G = nx.Graph()

# Add nodes (format: "nodeID---layerID")
G.add_edges_from([
    ("A---social", "B---social"),
    ("B---social", "C---social"),
    ("A---biological", "B---biological"),
])

# Walk constrained to social layer
walk = layer_specific_random_walk(
    G,
    start_node="A---social",
    walk_length=10,
    layer="social",
    cross_layer_prob=0.0,  # never cross layers
    seed=42
)

# All nodes are in social layer
print(walk)
```

### Cross-Layer Transitions

```python
# Allow 30% probability of crossing layers
walk = layer_specific_random_walk(
    G,
    start_node="A---social",
    walk_length=20,
    layer="social",
    cross_layer_prob=0.3,  # 30% chance to cross
    seed=42
)

# May contain nodes from both layers
```

## Advanced Topics

### Statistical Validation

#### Edge Weight Frequency

```python
import networkx as nx
from collections import Counter

# Create weighted graph
G = nx.Graph()
G.add_weighted_edges_from([
    (0, 1, 1.0),
    (0, 2, 2.0),
    (0, 3, 3.0),
])

# Count visits
visits = Counter()
for i in range(10000):
    walk = basic_random_walk(G, 0, 1, weighted=True, seed=i)
    if len(walk) > 1:
        visits[walk[1]] += 1

# Visit frequency matches weight ratio (1:2:3)
print(visits)  # {1: ~1667, 2: ~3333, 3: ~5000}
```

#### Uniformity Test

```python
# On complete graph, transitions are uniform
G = nx.complete_graph(10)

visits = Counter()
for i in range(10000):
    walk = basic_random_walk(G, 0, 1, weighted=False, seed=i)
    if len(walk) > 1:
        visits[walk[1]] += 1

# All neighbors visited roughly equally (~1111 times each)
```

### Performance Tips

#### Large Graphs

```python
# For large sparse graphs, use basic walks (faster)
G = nx.erdos_renyi_graph(100000, 0.0001, seed=42)

walks = generate_walks(
    G,
    num_walks=10,
    walk_length=100,
    p=1.0,  # No bias = faster
    q=1.0,
    seed=42
)
```

#### Parallel Processing

```python
from multiprocessing import Pool

def generate_batch(seed):
    return generate_walks(G, num_walks=10, walk_length=20, seed=seed)

# Generate walks in parallel
with Pool(4) as pool:
    batch_walks = pool.map(generate_batch, range(10))

# Flatten results
all_walks = [walk for batch in batch_walks for walk in batch]
```

### Integration with Node2Vec

```python
from gensim.models import Word2Vec

# Generate walks
walks = generate_walks(
    G,
    num_walks=80,
    walk_length=10,
    p=1.0,
    q=1.0,
    seed=42
)

# Convert to strings for Word2Vec
walks_str = [[str(node) for node in walk] for walk in walks]

# Train Word2Vec model
model = Word2Vec(
    walks_str,
    vector_size=128,
    window=10,
    min_count=0,
    sg=1,
    workers=4
)

# Get node embedding
embedding = model.wv['0']
```

## References

- **Grover, A., & Leskovec, J. (2016)**. node2vec: Scalable feature learning for networks. *KDD '16*. [https://doi.org/10.1145/2939672.2939754](https://doi.org/10.1145/2939672.2939754)

- **Perozzi, B., Al-Rfou, R., & Skiena, S. (2014)**. DeepWalk: Online learning of social representations. *KDD '14*. [https://doi.org/10.1145/2623330.2623732](https://doi.org/10.1145/2623330.2623732)

## See Also

- [API Documentation](../docfiles/random_walks.rst)
- [Example Code](../examples/example_random_walks.py)
- [Test Suite](../tests/test_random_walks.py)
