# Network Dynamics Examples

This directory contains examples for spreading processes, random walks, and other dynamic processes on networks.

## Examples

### Random Walks

- **`example_random_walks.py`** - Comprehensive random walk examples including:
  - Basic random walks with weighted edges
  - Node2Vec biased random walks (p/q parameters)
  - Multiple walk generation
  - Multilayer network walks
  - Statistical validation

### Spreading Processes

- **`example_spreading.py`** - Spreading/diffusion processes on multilayer networks
- **`example_multiplex_dynamics.py`** - Dynamics specific to multiplex network structures

## Key Concepts

### Random Walks
Stochastic processes where a walker moves randomly from node to neighbors:
- **Basic random walk**: Uniform random selection
- **Weighted random walk**: Selection proportional to edge weights
- **Biased random walk**: Node2Vec-style with return/forward bias

### Node2Vec Parameters
- **p (return parameter)**: Controls likelihood of returning to previous node
  - Low p: More likely to return (local exploration)
  - High p: Less likely to return (forward movement)
- **q (in-out parameter)**: Controls BFS vs. DFS behavior
  - Low q: BFS-like (explore immediate neighborhood)
  - High q: DFS-like (explore farther from source)

### Spreading Processes
Models of information, disease, or influence spreading:
- **SI model**: Susceptible → Infected
- **SIS model**: Susceptible ↔ Infected
- **SIR model**: Susceptible → Infected → Recovered
- **Threshold models**: Activation when threshold of neighbors infected

## Usage

```bash
# Comprehensive random walk examples
python example_random_walks.py

# Spreading process simulation
python example_spreading.py

# Multiplex-specific dynamics
python example_multiplex_dynamics.py
```

## Applications

Random walks and spreading processes are used for:
- **Node embeddings**: Node2vec uses random walks (see [../embeddings/](../embeddings/))
- **Community detection**: Infomap uses random walks
- **Ranking**: PageRank is a random walk-based algorithm
- **Sampling**: Exploring large networks efficiently
- **Epidemic modeling**: Understanding disease spread
- **Information diffusion**: Social network cascades

## Statistical Properties

The `example_random_walks.py` demonstrates:
- Weighted edge traversal frequencies
- Uniformity on complete graphs
- Backtracking rates with different p/q values
- Cross-layer transition probabilities

## Related Directories

- See [../embeddings/](../embeddings/) for node2vec embeddings based on random walks
- See [../multilayer/](../multilayer/) for multilayer-specific dynamics
- See [../community_detection/](../community_detection/) for Infomap (uses random walks)
