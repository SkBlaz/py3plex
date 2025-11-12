#!/usr/bin/env python3
"""
Example script demonstrating multilayer network statistics.

This script showcases all 17 multilayer network statistics implemented
in py3plex.algorithms.statistics.multilayer_statistics.

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

# This is a demonstration script - requires dependencies to run
# Usage: python examples/example_multilayer_statistics.py

try:
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls

    print("=" * 70)
    print("Multilayer Network Statistics Examples")
    print("=" * 70)

    # Create a sample multilayer network
    print("\n1. Creating a 3-layer social network...")
    network = multinet.multi_layer_network(directed=False)

    # Facebook layer
    network.add_edges([
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Alice', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'David', 'facebook', 1],
        ['Carol', 'facebook', 'David', 'facebook', 1],
    ], input_type='list')

    # Twitter layer
    network.add_edges([
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Bob', 'twitter', 'David', 'twitter', 1],
        ['Carol', 'twitter', 'David', 'twitter', 1],
    ], input_type='list')

    # LinkedIn layer
    network.add_edges([
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Carol', 'linkedin', 'David', 'linkedin', 1],
    ], input_type='list')

    # Inter-layer connections
    network.add_edges([
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
        ['Alice', 'twitter', 'Alice', 'linkedin', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
        ['Bob', 'twitter', 'Bob', 'linkedin', 1],
        ['Carol', 'facebook', 'Carol', 'twitter', 1],
        ['David', 'twitter', 'David', 'linkedin', 1],
    ], input_type='list')

    print("[OK] Network created: 4 nodes, 3 layers")

    # 1. Layer Density
    print("\n2. Layer Density (ρᵢ)")
    print("   Fraction of possible edges in each layer:")
    for layer in ['facebook', 'twitter', 'linkedin']:
        density = mls.layer_density(network, layer)
        print(f"   - {layer}: {density:.3f}")

    # 2. Inter-layer Coupling Strength
    print("\n3. Inter-layer Coupling Strength (Cᵢⱼ)")
    print("   Average inter-layer connection weight:")
    coupling_fb_tw = mls.inter_layer_coupling_strength(network, 'facebook', 'twitter')
    print(f"   - facebook ↔ twitter: {coupling_fb_tw:.3f}")

    # 3. Node Activity
    print("\n4. Node Activity (aᵢ)")
    print("   Fraction of layers where each node is active:")
    for node in ['Alice', 'Bob', 'Carol', 'David']:
        activity = mls.node_activity(network, node)
        print(f"   - {node}: {activity:.3f}")

    # 4. Degree Vector
    print("\n5. Degree Vector (kᵢ)")
    print("   Node degrees in each layer:")
    degrees_alice = mls.degree_vector(network, 'Alice')
    print(f"   - Alice: {degrees_alice}")

    # 5. Inter-layer Degree Correlation
    print("\n6. Inter-layer Degree Correlation (rᵢⱼ)")
    corr = mls.inter_layer_degree_correlation(network, 'facebook', 'twitter')
    print(f"   - facebook vs twitter: {corr:.3f}")

    # 6. Edge Overlap
    print("\n7. Edge Overlap (ωᵢⱼ)")
    print("   Jaccard similarity of edge sets:")
    overlap = mls.edge_overlap(network, 'facebook', 'twitter')
    print(f"   - facebook ∩ twitter: {overlap:.3f}")

    # 7. Layer Similarity
    print("\n8. Layer Similarity (Sᵢⱼ)")
    similarity = mls.layer_similarity(network, 'facebook', 'twitter', method='cosine')
    print(f"   - Cosine similarity: {similarity:.3f}")

    # 8. Multilayer Clustering Coefficient
    print("\n9. Multilayer Clustering Coefficient (Cᴹ)")
    clustering = mls.multilayer_clustering_coefficient(network)
    print("   - Per node:", {k: f"{v:.3f}" for k, v in clustering.items()})

    # 9. Versatility Centrality
    print("\n10. Versatility Centrality (Vᵢ)")
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    print("    Combined centrality across layers:")
    for node, v in sorted(versatility.items(), key=lambda x: x[1], reverse=True):
        print(f"    - {node}: {v:.3f}")

    # 10. Interdependence
    print("\n11. Interdependence (λ)")
    print("    Shortest path dependency on inter-layer edges:")
    interdep = mls.interdependence(network, sample_size=10)
    print(f"    - λ = {interdep:.3f}")

    # 11. Supra-Laplacian Spectrum
    print("\n12. Supra-Laplacian Spectrum (Λ)")
    spectrum = mls.supra_laplacian_spectrum(network, k=5)
    print(f"    - First 5 eigenvalues: {[f'{x:.3f}' for x in spectrum]}")

    # 12. Algebraic Connectivity
    print("\n13. Algebraic Connectivity (λ₂)")
    alg_conn = mls.algebraic_connectivity(network)
    print(f"    - Fiedler value: {alg_conn:.3f}")

    # 13. Inter-layer Assortativity
    print("\n14. Inter-layer Assortativity (rᴵ)")
    assort = mls.inter_layer_assortativity(network, 'facebook', 'twitter')
    print(f"    - Degree mixing: {assort:.3f}")

    # 14. Entropy of Multiplexity
    print("\n15. Entropy of Multiplexity (Hₘ)")
    entropy = mls.entropy_of_multiplexity(network)
    print(f"    - Layer diversity: {entropy:.3f} bits")

    # 15. Multilayer Motif Frequency
    print("\n16. Multilayer Motif Frequency (fₘ)")
    motifs = mls.multilayer_motif_frequency(network, motif_size=3)
    print("    - Triangle frequencies:")
    for motif_type, freq in motifs.items():
        print(f"      - {motif_type}: {freq:.3f}")

    # 16. Resilience
    print("\n17. Resilience (R)")
    print("    Network robustness to perturbations:")
    r_layer = mls.resilience(network, 'layer_removal', perturbation_param='twitter')
    print(f"    - After removing twitter layer: {r_layer:.3f}")
    r_coupling = mls.resilience(network, 'coupling_removal', perturbation_param=0.5)
    print(f"    - After removing 50% couplings: {r_coupling:.3f}")

    # 17. Multilayer Modularity (using community detection)
    print("\n18. Multilayer Modularity (Qᴹᴸ)")
    print("    Community quality across layers:")
    # Simple community assignment
    communities = {
        ('Alice', 'facebook'): 0, ('Bob', 'facebook'): 0,
        ('Carol', 'facebook'): 1, ('David', 'facebook'): 1,
        ('Alice', 'twitter'): 0, ('Carol', 'twitter'): 1,
        ('Bob', 'twitter'): 0, ('David', 'twitter'): 1,
        ('Alice', 'linkedin'): 0, ('Bob', 'linkedin'): 0,
        ('Carol', 'linkedin'): 1, ('David', 'linkedin'): 1,
    }
    Q = mls.multilayer_modularity(network, communities)
    print(f"    - Q = {Q:.3f}")

    print("\n" + "=" * 70)
    print("All 17 multilayer statistics computed successfully!")
    print("=" * 70)

except ImportError as e:
    print("ERROR: This example requires py3plex dependencies:")
    print(f"   {e}")
    print("\nInstall with: pip install numpy scipy networkx")
