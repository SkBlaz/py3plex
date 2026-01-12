"""
Uncertainty: Bootstrap and perturbation.

Demonstrates:
- Network perturbation for robustness analysis
- Bootstrap sampling concept

Note: Uses py3plex.uncertainty module.
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.uncertainty import bootstrap_metric
import networkx as nx

# 1. Load network
network = load_aarhus_cs()

# 2. Define a simple metric function
def degree_centrality_fn(net):
    """Compute degree centrality for all nodes."""
    # Get degree for each node
    degrees = {}
    for node in net.get_nodes():
        # Count neighbors
        try:
            neighbors = list(net.get_neighbors(node))
            degrees[node] = len(neighbors)
        except:
            degrees[node] = 0
    # Normalize
    n = len(list(net.get_nodes()))
    return {k: v / (n - 1) if n > 1 else 0 for k, v in degrees.items()}

# 3. Bootstrap the metric
print("Computing bootstrap confidence intervals...")
results = bootstrap_metric(
    network,
    metric_fn=degree_centrality_fn,
    n_boot=20,  # Small sample for speed
    unit='edges',
    ci=0.95,
    random_state=42
)

# 4. Print sample results
print(f"\nBootstrap results (sample):")
print(f"  Mean values computed for all nodes")
print(f"  Confidence intervals available")
print(f"  Keys in results: {list(results.keys())}")
