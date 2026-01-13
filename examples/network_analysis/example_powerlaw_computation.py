"""
Compute and Visualize Power-Law Distributions in Networks

Teaches:
- Fit and visualize power-law distributions on node degrees
- Compare power-law fitting on simple NetworkX graphs vs. multilayer networks
- Test for scale-free properties using built-in statistical tests

Prerequisites:
- mpmath library for power-law fitting: pip install mpmath
- Optional dataset: epigenetics.gpickle (from py3plex datasets)

SKIP_CI: external_deps - Requires specific dataset files
"""

import networkx as nx

try:
    import mpmath
    MPMATH_AVAILABLE = True
except ImportError:
    MPMATH_AVAILABLE = False
    print("Warning: mpmath not installed. Install with: pip install mpmath")
    print("This example requires mpmath for power law fitting.")
    exit(0)

from py3plex.algorithms.statistics.topology import plot_power_law
from py3plex.core import multinet
from py3plex.utils import get_dataset_path
from py3plex.exceptions import Py3plexIOError

print("=" * 70)
print("POWER-LAW DISTRIBUTION ANALYSIS")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# Example 1: Power-law analysis on a simple NetworkX graph
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1] Analyzing power-law distribution on a NetworkX powerlaw cluster graph...")
print("-" * 70)
G = nx.powerlaw_cluster_graph(1000, 3, 0.5, 1573)
print(f"Generated network: {len(G.nodes())} nodes, {len(G.edges())} edges")
val_vect = sorted(dict(nx.degree(G)).values(), reverse=True)
print(f"Degree distribution: {len(val_vect)} values")
plot_power_law(val_vect, "", "Node degree", "individual node")
print("Power-law plot saved/displayed successfully")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 2: Power-law analysis on a multilayer network
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[2] Analyzing power-law distribution on a multilayer network...")
print("-" * 70)
try:
    dataset_path = get_dataset_path("epigenetics.gpickle")
    multilayer_network = multinet.multi_layer_network().load_network(
        dataset_path,
        directed=False,
        input_type="gpickle_biomine")
    print(f"Loaded multilayer network from: {dataset_path}")
except Py3plexIOError:
    print("Required dataset not found. Skipping multilayer example.")
    print("Note: This example can still run with just the NetworkX graph above.")
    exit(0)

val_vect = sorted(dict(nx.degree(multilayer_network.core_network)).values(),
                  reverse=True)
print(f"Multilayer degree distribution: {len(val_vect)} values")
plot_power_law(val_vect, "", "Node degree", "individual node")
print("Multilayer power-law plot saved/displayed successfully")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 3: Statistical test for scale-free properties
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3] Testing for scale-free properties...")
print("-" * 70)
scale_free_result = multilayer_network.test_scale_free()
print(f"Scale-free test result: {scale_free_result}")

print("\n" + "=" * 70)
print("POWER-LAW ANALYSIS COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  [OK] Power-law distributions are common in many real-world networks")
print("  [OK] The fitting process considers multiple alternative distributions")
print("  [OK] Scale-free properties can be statistically validated")
print("  [OK] This analysis works on any node property (not just degree)")

