# Embedding Examples

This directory contains examples for creating and visualizing network embeddings.

## Examples

### Embedding Construction

- **`example_embedding_construction.py`** - Complete workflow: load network → create embedding → visualize with t-SNE
- **`example_n2v_embedding.py`** - Node2vec embedding generation and usage

### Embedding Visualization

- **`example_embedding_visualization.py`** - Visualize embeddings in 2D space using t-SNE

## What are Network Embeddings?

Network embeddings map nodes to low-dimensional vectors that preserve network structure. These vectors can be used for:
- **Visualization**: Project networks into 2D/3D space
- **Classification**: Node classification with ML algorithms
- **Link prediction**: Predict missing edges
- **Clustering**: Find similar nodes

## Node2Vec Algorithm

Node2vec uses biased random walks to learn embeddings:
- **p parameter**: Return parameter (likelihood of returning to previous node)
- **q parameter**: In-out parameter (BFS vs. DFS behavior)
- **walk_length**: Length of random walks
- **num_walks**: Number of walks per node
- **dimensions**: Embedding vector size

## Usage

```bash
# Create and visualize embeddings
python example_embedding_construction.py

# Generate node2vec embeddings
python example_n2v_embedding.py
```

## Installation Notes

**Node2vec binary** (required for some examples):
- These examples use an external node2vec binary
- Install from: https://github.com/snap-stanford/snap/tree/master/examples/node2vec
- Alternative: Use Python implementation: `pip install node2vec`

**Note**: Examples will indicate if the binary is not found.

## Workflow

Typical embedding workflow:
1. Load or create network
2. Save as edgelist format
3. Call node2vec binary to generate embeddings
4. Load embeddings back into py3plex
5. Visualize with t-SNE or use for downstream tasks

## Output Formats

Embeddings can be exported as:
- **JSON**: For web applications
- **NumPy arrays**: For ML workflows
- **Position dictionaries**: For custom visualization

## Related Directories

- See [../visualization/](../visualization/) for using embeddings in layouts
- See [../decomposition_and_classification/](../decomposition_and_classification/) for using embeddings in classification
- See [../dynamics/](../dynamics/) for random walk algorithms that power node2vec
