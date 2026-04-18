"""MetaPath2Vec embedding example for heterogeneous multilayer networks.

Demonstrates how to compute MetaPath2Vec embeddings on a simple author-paper
network with two layers: 'author' and 'paper'.

Usage::

    python examples/advanced/example_metapath2vec.py

# FAST
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np

# ---------------------------------------------------------------------------
# Build a tiny author-paper network directly with networkx (no file needed)
# ---------------------------------------------------------------------------
try:
    import networkx as nx
    from py3plex.core.multinet import multi_layer_network

    net = multi_layer_network(directed=False)
    net.add_nodes([
        {"source": "Alice", "type": "author"},
        {"source": "Bob", "type": "author"},
        {"source": "Carol", "type": "author"},
        {"source": "p1", "type": "paper"},
        {"source": "p2", "type": "paper"},
    ])
    net.add_edges([
        {"source": "Alice", "target": "p1", "source_type": "author", "target_type": "paper"},
        {"source": "Bob", "target": "p1", "source_type": "author", "target_type": "paper"},
        {"source": "Bob", "target": "p2", "source_type": "author", "target_type": "paper"},
        {"source": "Carol", "target": "p2", "source_type": "author", "target_type": "paper"},
    ])
    USE_MULTINET = True
except Exception:
    USE_MULTINET = False


# ---------------------------------------------------------------------------
# Build a minimal network-like object when full py3plex can't load
# ---------------------------------------------------------------------------
class _TinyNetwork:
    """Minimal multilayer network for the example."""

    def __init__(self) -> None:
        import networkx as nx

        G = nx.MultiGraph()
        for a in ["Alice", "Bob", "Carol"]:
            G.add_node((a, "author"))
        for p in ["p1", "p2"]:
            G.add_node((p, "paper"))
        G.add_edge(("Alice", "author"), ("p1", "paper"))
        G.add_edge(("Bob", "author"), ("p1", "paper"))
        G.add_edge(("Bob", "author"), ("p2", "paper"))
        G.add_edge(("Carol", "author"), ("p2", "paper"))
        self.core_network = G

    def get_nodes(self):
        return list(self.core_network.nodes())


# ---------------------------------------------------------------------------
# Run MetaPath2Vec
# ---------------------------------------------------------------------------
from py3plex.embeddings.metapath2vec import MetaPath2VecEmbedder

if USE_MULTINET:
    network = net
else:
    network = _TinyNetwork()

nodes = list(network.get_nodes())  # materialize once; generators are exhausted after first use

embedder = MetaPath2VecEmbedder(
    metapaths=[["author", "paper", "author"]],
    dim=16,
    walk_length=20,
    num_walks=5,
    window_size=3,
    epochs=5,
    negative_samples=3,
    seed=42,
    normalize=True,
)

result = embedder.fit_transform(network, item_ids=nodes)

print(f"Embedding method  : {result.method}")
print(f"Vocabulary size   : {result.matrix.shape[0]} nodes embedded")
print(f"Embedding dim     : {result.matrix.shape[1]}")
print(f"Seed used         : {result.meta.get('seed')}")
print(f"Total training ms : {result.meta.get('total_ms', '?'):.1f}")
print()
print("Sample embeddings (first 3 nodes):")
for item_id, vec in zip(result.item_ids[:3], result.matrix[:3]):
    print(f"  {item_id!s:30s}  norm={np.linalg.norm(vec):.4f}")

# Verify determinism
result2 = MetaPath2VecEmbedder(
    metapaths=[["author", "paper", "author"]],
    dim=16,
    walk_length=20,
    num_walks=5,
    window_size=3,
    epochs=5,
    negative_samples=3,
    seed=42,
    normalize=True,
).fit_transform(network, item_ids=nodes)

if np.allclose(result.matrix, result2.matrix):
    print("\n[OK] Same seed → identical vectors (deterministic)")
else:
    print("\n[WARN] Vectors differ across runs with the same seed")
