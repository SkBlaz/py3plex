#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Multilayer Leiden Community Detection with Uncertainty Quantification

This example demonstrates the production-quality multilayer Leiden algorithm
with first-class uncertainty quantification (UQ) support.

Features demonstrated:
1. Basic multilayer Leiden community detection
2. Parameter sweeps (gamma, omega)
3. Uncertainty quantification via ensemble runs
4. Stability metrics and confidence intervals
5. DSL integration (Q.nodes().community(method="leiden"))

Author: py3plex community
"""

import numpy as np
from py3plex.core import multinet
from py3plex.algorithms.community_detection import (
    multilayer_leiden,
    multilayer_leiden_uq,
)

print("=" * 80)
print("MULTILAYER LEIDEN COMMUNITY DETECTION WITH UQ")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════
# 1. Create a multilayer network
# ═══════════════════════════════════════════════════════════════════════════

print("\n[1] Creating a 2-layer, 6-node multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Layer 1: Two densely connected communities
network.add_edges([
    # Community 1
    ['A', 'L1', 'B', 'L1', 1.0],
    ['A', 'L1', 'C', 'L1', 1.0],
    ['B', 'L1', 'C', 'L1', 1.0],
    # Community 2
    ['D', 'L1', 'E', 'L1', 1.0],
    ['D', 'L1', 'F', 'L1', 1.0],
    ['E', 'L1', 'F', 'L1', 1.0],
    # Weak inter-community edge
    ['C', 'L1', 'D', 'L1', 0.5],
], input_type='list')

# Layer 2: Different structure
network.add_edges([
    ['A', 'L2', 'B', 'L2', 1.0],
    ['B', 'L2', 'C', 'L2', 1.0],
    ['D', 'L2', 'E', 'L2', 1.0],
    ['E', 'L2', 'F', 'L2', 1.0],
], input_type='list')

n_nodes = len(list(network.get_nodes()))
n_edges = len(list(network.get_edges()))
print(f"Network created: {n_nodes} node-layer pairs, {n_edges} edges")

# ═══════════════════════════════════════════════════════════════════════════
# 2. Basic Leiden community detection
# ═══════════════════════════════════════════════════════════════════════════

print("\n[2] Running basic multilayer Leiden...")
print("-" * 80)

partition, modularity = multilayer_leiden(
    network,
    gamma=1.0,
    omega=1.0,
    random_state=42
)

n_communities = len(set(partition.values()))
print(f"Modularity Q = {modularity:.4f}")
print(f"Number of communities: {n_communities}")
print("\nPartition:")
for (node, layer), comm_id in sorted(partition.items()):
    print(f"  ({node}, {layer}) → Community {comm_id}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. Leiden with diagnostics
# ═══════════════════════════════════════════════════════════════════════════

print("\n[3] Running Leiden with diagnostics...")
print("-" * 80)

partition, modularity, diagnostics = multilayer_leiden(
    network,
    gamma=1.0,
    omega=1.0,
    random_state=42,
    return_diagnostics=True
)

print(f"Runtime: {diagnostics['timing']:.4f} seconds")
print(f"Iterations: {diagnostics['convergence_info']['iterations']}")
print(f"Converged: {diagnostics['convergence_info']['converged']}")
print(f"Backend: {diagnostics['backend_used']}")

# ═══════════════════════════════════════════════════════════════════════════
# 4. Parameter sweep: gamma (resolution)
# ═══════════════════════════════════════════════════════════════════════════

print("\n[4] Parameter sweep: gamma (resolution)...")
print("-" * 80)

gamma_values = [0.5, 1.0, 1.5, 2.0]
print(f"{'Gamma':<10} {'Modularity':<15} {'#Communities':<15}")
print("-" * 40)

for gamma in gamma_values:
    partition, Q = multilayer_leiden(
        network,
        gamma=gamma,
        omega=1.0,
        random_state=42
    )
    n_comm = len(set(partition.values()))
    print(f"{gamma:<10.1f} {Q:<15.4f} {n_comm:<15}")

print("\nObservation: Higher gamma typically leads to more communities.")

# ═══════════════════════════════════════════════════════════════════════════
# 5. Parameter sweep: omega (interlayer coupling)
# ═══════════════════════════════════════════════════════════════════════════

print("\n[5] Parameter sweep: omega (interlayer coupling)...")
print("-" * 80)

omega_values = [0.0, 0.5, 1.0, 2.0]
print(f"{'Omega':<10} {'Modularity':<15} {'#Communities':<15}")
print("-" * 40)

for omega in omega_values:
    partition, Q = multilayer_leiden(
        network,
        gamma=1.0,
        omega=omega,
        random_state=42
    )
    n_comm = len(set(partition.values()))
    print(f"{omega:<10.1f} {Q:<15.4f} {n_comm:<15}")

print("\nObservation: Higher omega couples layers more strongly.")

# ═══════════════════════════════════════════════════════════════════════════
# 6. Uncertainty Quantification (UQ) via ensemble
# ═══════════════════════════════════════════════════════════════════════════

print("\n[6] Multilayer Leiden with Uncertainty Quantification...")
print("-" * 80)

result = multilayer_leiden_uq(
    network,
    gamma=1.0,
    omega=1.0,
    n_runs=20,
    method="seed",  # Monte Carlo via different seeds
    random_state=42
)

print(f"\nUQ Results (n_runs=20):")
print(f"  Score (modularity) mean: {result.summary['score_mean']:.4f}")
print(f"  Score std: {result.summary['score_std']:.4f}")
print(f"  Score 95% CI: [{result.ci['score'][0]:.4f}, {result.ci['score'][1]:.4f}]")
print(f"  #Communities mean: {result.summary['n_communities_mean']:.2f}")
print(f"  #Communities std: {result.summary['n_communities_std']:.2f}")
print(f"  #Communities 95% CI: [{result.ci['n_communities'][0]:.0f}, {result.ci['n_communities'][1]:.0f}]")

print(f"\nStability Metrics:")
print(f"  Variation of Information (VI) mean: {result.stability_metrics['vi_mean']:.4f}")
print(f"  NMI mean: {result.stability_metrics['nmi_mean']:.4f}")
print(f"  Pairwise agreement: {result.stability_metrics['pairwise_agreement']:.4f}")

print(f"\nNode-level uncertainty (entropy):")
nodes = sorted(result.consensus_partition.keys())
for i, node in enumerate(nodes[:6]):  # Show first 6
    entropy = result.stability_metrics['node_entropy'][i]
    print(f"  {node}: entropy = {entropy:.4f}")

print(f"\nConsensus partition:")
for (node, layer), comm_id in sorted(result.consensus_partition.items())[:6]:
    print(f"  ({node}, {layer}) → Community {comm_id}")

# ═══════════════════════════════════════════════════════════════════════════
# 7. UQ with perturbation (structural uncertainty)
# ═══════════════════════════════════════════════════════════════════════════

print("\n[7] UQ with edge perturbation (structural uncertainty)...")
print("-" * 80)

result_perturb = multilayer_leiden_uq(
    network,
    gamma=1.0,
    omega=1.0,
    n_runs=20,
    method="perturbation",
    perturbation_rate=0.1,  # Drop 10% of edges
    random_state=42
)

print(f"\nUQ Results with perturbation:")
print(f"  Successful runs: {result_perturb.summary['n_runs_success']}/{20}")
print(f"  Score mean: {result_perturb.summary['score_mean']:.4f}")
print(f"  Score std: {result_perturb.summary['score_std']:.4f}")
print(f"  NMI mean: {result_perturb.stability_metrics['nmi_mean']:.4f}")

# ═══════════════════════════════════════════════════════════════════════════
# 8. Determinism check
# ═══════════════════════════════════════════════════════════════════════════

print("\n[8] Determinism check (same seed → same result)...")
print("-" * 80)

partition1, score1 = multilayer_leiden(network, random_state=42)
partition2, score2 = multilayer_leiden(network, random_state=42)

identical = (partition1 == partition2) and (abs(score1 - score2) < 1e-10)
print(f"Partitions identical: {partition1 == partition2}")
print(f"Scores identical: {abs(score1 - score2) < 1e-10}")
print(f"Deterministic: {identical}")

# ═══════════════════════════════════════════════════════════════════════════
# 9. DSL Integration (if DSL is available)
# ═══════════════════════════════════════════════════════════════════════════

print("\n[9] DSL Integration (Q.nodes().community())...")
print("-" * 80)

try:
    from py3plex.dsl import Q

    # Basic community detection via DSL
    result = (
        Q.nodes()
         .community(method="leiden", gamma=1.2, omega=0.8, random_state=42)
         .execute(network)
    )

    print("DSL query executed successfully!")
    print(f"Query result type: {type(result)}")
    print("Note: Community metadata is attached to network and result")

except ImportError:
    print("DSL not available in this environment")

# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
Key takeaways:
1. multilayer_leiden() provides production-quality community detection
2. Deterministic by default (random_state=None → seed=0)
3. Parameters: gamma (resolution), omega (coupling), n_iterations
4. multilayer_leiden_uq() provides uncertainty quantification
5. UQ methods: 'seed' (Monte Carlo), 'perturbation', 'bootstrap'
6. Stability metrics: VI, NMI, node entropy, pairwise agreement
7. Consensus partition: medoid (default) or co-assignment clustering
8. DSL integration: Q.nodes().community(method="leiden")

For more information, see:
- AGENTS.md: Complete API reference and conventions
- docfiles/how-to/run_community_detection.rst: Tutorial
- tests/test_multilayer_leiden_uq.py: Comprehensive test suite
""")
