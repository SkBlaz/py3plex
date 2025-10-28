"""
Example: MultiXRank - Random Walk with Restart on Universal Multilayer Networks

This example demonstrates the MultiXRank algorithm for node prioritization
in universal multilayer networks with multiple multiplexes connected by
bipartite blocks.

MultiXRank implements random walk with restart (RWR) on a supra-heterogeneous
adjacency matrix, as described in Baptista et al. (2022).

Reference:
    Baptista et al. (2022), "Universal multilayer network exploration by random
    walk with restart", Communications Physics, 5, 170.
    https://doi.org/10.1038/s42005-022-00937-9
"""

import numpy as np
import scipy.sparse as sp

from py3plex.algorithms.multilayer_algorithms.multixrank import (
    MultiXRank, multixrank_from_py3plex_networks)
from py3plex.core import multinet

print("=" * 70)
print("MultiXRank Example: Universal Multilayer Network Exploration")
print("=" * 70)

# ============================================================================
# Example 1: Building Networks with py3plex Data Structures
# ============================================================================
print("\n" + "=" * 70)
print("Example 1: Building Networks with py3plex Data Structures")
print("=" * 70)

# Create first multiplex using py3plex: Social network
# Build a 2-layer social network with 3 people (A, B, C)
print("\nCreating social multiplex network with py3plex...")
social_net = multinet.multi_layer_network(directed=False)

# Layer 1: Face-to-face interactions (A-B-C in a line)
social_net.add_edges(
    [["A", "face2face", "B", "face2face", 1], ["B", "face2face", "C", "face2face", 1]],
    input_type="list",
)

# Layer 2: Online interactions (A, B, and C form a triangle)
social_net.add_edges(
    [
        ["A", "online", "B", "online", 1],
        ["B", "online", "C", "online", 1],
        ["C", "online", "A", "online", 1],
    ],
    input_type="list",
)

print(f"Social network has {len(list(social_net.get_nodes()))} unique node-layer pairs")
print(
    f"Social network has {len(social_net.get_layers()[0])} layers: {social_net.get_layers()[0]}"
)

# Create second multiplex using py3plex: Collaboration network
print("\nCreating collaboration multiplex network with py3plex...")
collab_net = multinet.multi_layer_network(directed=False)

# Layer 1: Project collaborations (X, Y, Z all connected)
collab_net.add_edges(
    [
        ["X", "project", "Y", "project", 1],
        ["Y", "project", "Z", "project", 1],
        ["Z", "project", "X", "project", 1],
    ],
    input_type="list",
)

# Layer 2: Co-authorship (X-Y and Y-Z connections)
collab_net.add_edges(
    [["X", "coauthor", "Y", "coauthor", 1], ["Y", "coauthor", "Z", "coauthor", 1]],
    input_type="list",
)

print(
    f"Collaboration network has {len(list(collab_net.get_nodes()))} unique node-layer pairs"
)
print(
    f"Collaboration network has {len(collab_net.get_layers()[0])} layers: {collab_net.get_layers()[0]}"
)

# Get supra-adjacency matrices from py3plex networks
print("\nExtracting supra-adjacency matrices...")
social_supra = social_net.get_supra_adjacency_matrix(mtype="sparse")
collab_supra = collab_net.get_supra_adjacency_matrix(mtype="sparse")

print(f"Social supra-adjacency shape: {social_supra.shape}")
print(f"Collaboration supra-adjacency shape: {collab_supra.shape}")

# Initialize MultiXRank
mxr = MultiXRank(restart_prob=0.4, epsilon=1e-6, max_iter=100000, verbose=True)

# Add multiplexes to MultiXRank
# Use node_order from the py3plex networks for proper mapping
social_node_order = (
    social_net.node_order_in_matrix
    if hasattr(social_net, "node_order_in_matrix")
    else None
)
collab_node_order = (
    collab_net.node_order_in_matrix
    if hasattr(collab_net, "node_order_in_matrix")
    else None
)

mxr.add_multiplex("social", social_supra, node_order=social_node_order)
mxr.add_multiplex("collab", collab_supra, node_order=collab_node_order)

# Create bipartite connections between networks
# Map people in social network to their counterparts in collaboration network
# Assuming: A<->X, B<->Y, C<->Z (identity mapping at the node-layer replica level)
print("\nCreating bipartite inter-multiplex connections...")
bipartite_social_to_collab = sp.csr_matrix(
    np.eye(social_supra.shape[0], collab_supra.shape[0]), dtype=float
)

# Add bidirectional bipartite connections
mxr.add_bipartite_block("social", "collab", bipartite_social_to_collab)
mxr.add_bipartite_block("collab", "social", bipartite_social_to_collab.T)

# Build the supra-heterogeneous adjacency matrix
print("\nBuilding supra-heterogeneous adjacency matrix...")
supra_matrix = mxr.build_supra_heterogeneous_matrix()
print(f"Universal supra-matrix shape: {supra_matrix.shape}")
print(f"Total edges: {supra_matrix.nnz}")

# Column-normalize to create transition matrix
print("\nCreating column-stochastic transition matrix...")
transition_matrix = mxr.column_normalize()

# Run Random Walk with Restart from seed node
# Seed at node index 1 (corresponds to person B in social network)
print("\nRunning RWR with seed at index 1 in social network...")
scores = mxr.random_walk_with_restart({"social": [1]})

print(f"\nRaw scores (length={len(scores)}):")
print(f"Total probability mass: {np.sum(scores):.6f}")

# Aggregate scores by multiplex
print("\nAggregated scores by multiplex:")
aggregated = mxr.aggregate_scores(scores)
for multiplex_name, node_scores in aggregated.items():
    print(f"\n{multiplex_name} (top 5 node-replicas):")
    sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    for node_id, score in sorted_nodes:
        print(f"  Node-replica {node_id}: {score:.6f}")

# Get top-5 ranked nodes
print("\nTop-5 ranked node-replicas (excluding seed):")
top_k = mxr.get_top_ranked(scores, k=5, exclude_seeds=True, seed_nodes={"social": [1]})
for idx, (global_idx, score) in enumerate(top_k, 1):
    print(f"  {idx}. Global index {global_idx}: {score:.6f}")

# ============================================================================
# Example 2: Using py3plex multi_layer_network Objects
# ============================================================================
print("\n\n" + "=" * 70)
print("Example 2: Integration with py3plex multi_layer_network")
print("=" * 70)

# Create first network: Protein-protein interaction (PPI) network
print("\nCreating PPI multiplex network...")
ppi_net = multinet.multi_layer_network(directed=False)
ppi_net.add_edges(
    [
        ["P1", "physical", "P2", "physical", 1],
        ["P2", "physical", "P3", "physical", 1],
        ["P1", "genetic", "P3", "genetic", 1],
        ["P2", "genetic", "P3", "genetic", 1],
    ],
    input_type="list",
)

# Create second network: Gene regulatory network
print("Creating gene regulatory network...")
gene_net = multinet.multi_layer_network(directed=True)
gene_net.add_edges(
    [
        ["G1", "regulation", "G2", "regulation", 1],
        ["G2", "regulation", "G3", "regulation", 1],
    ],
    input_type="list",
)

# Get dimensions for bipartite block
ppi_dim = ppi_net.get_supra_adjacency_matrix().shape[0]
gene_dim = gene_net.get_supra_adjacency_matrix().shape[0]

print(f"PPI network dimension: {ppi_dim}")
print(f"Gene network dimension: {gene_dim}")

# Create bipartite connection: protein to gene mapping
# For demonstration, create a sparse connection matrix
bipartite_ppi_to_gene = sp.random(ppi_dim, gene_dim, density=0.3, format="csr")

# Use convenience function for py3plex networks
print("\nRunning MultiXRank on py3plex networks...")
networks = {"ppi": ppi_net, "gene": gene_net}
bipartite_connections = {("ppi", "gene"): bipartite_ppi_to_gene}

# Seed at first node of PPI network
seed_nodes = {"ppi": [0]}

mxr2, scores2 = multixrank_from_py3plex_networks(
    networks=networks,
    bipartite_connections=bipartite_connections,
    seed_nodes=seed_nodes,
    restart_prob=0.35,
    verbose=True,
)

print(f"\nScores shape: {scores2.shape}")
print(f"Total probability mass: {np.sum(scores2):.6f}")

# Aggregate scores
print("\nAggregated scores:")
aggregated2 = mxr2.aggregate_scores(scores2)
for net_name, node_scores in aggregated2.items():
    print(f"\n{net_name} (top 3 nodes):")
    sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for node_id, score in sorted_nodes:
        print(f"  {node_id}: {score:.6f}")

# ============================================================================
# Example 3: Emphasis on Supra-Adjacency Construction
# ============================================================================
print("\n\n" + "=" * 70)
print("Example 3: Detailed Supra-Adjacency Construction")
print("=" * 70)

# Create a 2-layer multiplex (multiplex 1)
print("\nCreating multiplex with 2 layers, 3 nodes each...")
# Layer 1: nodes 0, 1, 2
# Layer 2: nodes 0, 1, 2 (replicas)
# Total: 6 node-layer combinations

# Intra-layer edges for layer 1
layer1 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

# Intra-layer edges for layer 2
layer2 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)

# Inter-layer coupling (connects same physical node across layers)
coupling = sp.eye(3, format="csr", dtype=float)

# Build supra-adjacency for this multiplex
# Block structure:
#   [Layer1,  Coupling]
#   [Coupling, Layer2 ]
supra_multiplex1 = sp.bmat([[layer1, coupling], [coupling, layer2]], format="csr")

print(f"Multiplex 1 supra-adjacency shape: {supra_multiplex1.shape}")
print("Multiplex 1 supra-adjacency matrix:")
print(supra_multiplex1.toarray())

# Create a simple single-layer network (multiplex 2)
print("\nCreating single-layer network (multiplex 2)...")
single_layer = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)

# Initialize MultiXRank and add both multiplexes
mxr3 = MultiXRank(restart_prob=0.4, verbose=True)
mxr3.add_multiplex(
    "multiplex1",
    supra_multiplex1,
    node_order=["N0_L1", "N1_L1", "N2_L1", "N0_L2", "N1_L2", "N2_L2"],
)
mxr3.add_multiplex("multiplex2", single_layer, node_order=["M0", "M1"])

# Create bipartite connection between multiplexes
# Connect nodes from multiplex1 to multiplex2
bipartite_1_to_2 = sp.csr_matrix(
    [
        [1, 0],  # N0_L1 -> M0
        [0, 1],  # N1_L1 -> M1
        [0, 0],  # N2_L1 -> none
        [1, 0],  # N0_L2 -> M0
        [0, 1],  # N1_L2 -> M1
        [0, 0],  # N2_L2 -> none
    ],
    dtype=float,
)

mxr3.add_bipartite_block("multiplex1", "multiplex2", bipartite_1_to_2)

# Build universal supra-heterogeneous matrix
print("\nBuilding universal supra-heterogeneous matrix...")
universal_supra = mxr3.build_supra_heterogeneous_matrix()

print(f"Universal supra-matrix shape: {universal_supra.shape}")
print(f"Universal supra-matrix edges: {universal_supra.nnz}")

print("\nUniversal supra-heterogeneous adjacency matrix:")
print("(First 6x6 block is multiplex1, last 2x2 is multiplex2)")
print(universal_supra.toarray())

# Normalize and run RWR
mxr3.column_normalize()
print("\nRunning RWR from node N1_L1 (index 1) in multiplex1...")
scores3 = mxr3.random_walk_with_restart({"multiplex1": [1]})

print("\nFinal scores:")
aggregated3 = mxr3.aggregate_scores(scores3)
for mplex, nodes in aggregated3.items():
    print(f"\n{mplex}:")
    for node, score in nodes.items():
        print(f"  {node}: {score:.6f}")

print("\n" + "=" * 70)
print("Examples completed!")
print("=" * 70)
print("\nKey takeaways:")
print(
    "  1. MultiXRank builds a supra-heterogeneous adjacency from multiple multiplexes"
)
print("  2. Bipartite blocks connect different multiplexes")
print("  3. Column-stochastic normalization ensures valid transition matrix")
print("  4. RWR propagates probability from seed nodes across the universal network")
print("  5. Emphasis on correct supra-adjacency construction is critical")
