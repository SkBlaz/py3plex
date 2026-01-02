"""
Tutorial: Multilayer Stochastic Block Model in py3plex

This example demonstrates how to use the multilayer SBM implementation
for community detection and link prediction in multiplex networks.
"""

import numpy as np
from py3plex.core import multinet
from py3plex.algorithms.sbm import fit_multilayer_sbm, select_multilayer_sbm_model


def generate_aligned_network(n_nodes, n_layers, p_within=0.4, p_between=0.05, n_communities=3, seed=42):
    """Generate node-aligned multiplex network with block structure."""
    np.random.seed(seed)
    net = multinet.multi_layer_network(directed=False)
    
    # True community assignments
    block_sizes = [n_nodes // n_communities] * n_communities
    block_sizes[-1] += n_nodes - sum(block_sizes)
    true_labels = np.repeat(range(n_communities), block_sizes)
    np.random.shuffle(true_labels)
    
    # Ensure all nodes exist in all layers
    layer_names = [f'L{i}' for i in range(n_layers)]
    for i in range(n_nodes):
        for layer in layer_names:
            net.add_edges([{
                'source': i, 'target': (i + 1) % n_nodes,
                'source_type': layer, 'target_type': layer
            }])
    
    # Add edges based on block structure
    for layer in layer_names:
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                same_comm = (true_labels[i] == true_labels[j])
                p = p_within if same_comm else p_between
                if np.random.rand() < p:
                    net.add_edges([{
                        'source': i, 'target': j,
                        'source_type': layer, 'target_type': layer
                    }])
    
    return net, true_labels


def example_1_basic_fitting():
    """Example 1: Basic SBM fitting."""
    print("=" * 60)
    print("Example 1: Basic SBM Fitting")
    print("=" * 60)
    
    # Generate network with 3 communities
    net, true_labels = generate_aligned_network(
        n_nodes=12, n_layers=2, n_communities=3, p_within=0.6, p_between=0.1
    )
    
    print(f"Network: 12 nodes, 2 layers, 3 true communities")
    
    # Fit Degree-Corrected SBM with 3 blocks
    print("\nFitting DC-SBM with K=3 blocks...")
    model = fit_multilayer_sbm(
        net,
        n_blocks=3,
        model="dc_sbm",
        layer_mode="shared_blocks",
        n_init=2,
        max_iter=50,
        verbose=False,
        seed=42
    )
    
    # Get summary
    summary = model.get_summary()
    print(f"Converged: {summary['converged']}")
    print(f"Iterations: {summary['n_iter']}")
    print(f"Final ELBO: {summary['final_elbo']:.4f}")
    print(f"Blocks used: {summary['n_blocks_used']}")
    print(f"Block sizes: {summary['block_sizes']}")
    
    # Get partition
    partition = model.to_partition_vector()
    print(f"\nCommunity assignments:")
    for node_id, community_id in sorted(partition.items())[:12]:
        print(f"  Node {node_id}: Community {community_id} (true: {true_labels[node_id]})")
    
    print()


def example_2_model_selection():
    """Example 2: Model selection across K."""
    print("=" * 60)
    print("Example 2: Model Selection")
    print("=" * 60)
    
    # Generate network with 3 communities
    net, _ = generate_aligned_network(
        n_nodes=24, n_layers=2, n_communities=3, p_within=0.5, p_between=0.05
    )
    
    print("Network with 3 true communities")
    
    # Model selection: try K in [2, 3, 4, 5]
    print("\nRunning model selection for K=[2,3,4,5]...")
    best_model, selection_info = fit_multilayer_sbm(
        net,
        n_blocks=[2, 3, 4, 5],
        model="sbm",
        layer_mode="independent",
        n_init=2,
        max_iter=40,
        verbose=False,
        seed=42
    )
    
    print(f"\nBest K selected: {selection_info['best_K']}")
    print("\nComparison table:")
    print(selection_info['comparison_table'])
    
    print()


def example_3_link_prediction():
    """Example 3: Link prediction."""
    print("=" * 60)
    print("Example 3: Link Prediction")
    print("=" * 60)
    
    # Generate small network
    net, _ = generate_aligned_network(
        n_nodes=6, n_layers=2, n_communities=2, p_within=0.7, p_between=0.1, seed=43
    )
    
    # Fit model
    model = fit_multilayer_sbm(
        net, n_blocks=2, n_init=2, max_iter=30, verbose=False, seed=42
    )
    
    print("Fitted SBM model for link prediction")
    
    # Predict probabilities for potential edges
    print("\nLink prediction scores:")
    potential_edges = [
        (0, 3, 'L0'),
        (1, 4, 'L0'),
        (2, 5, 'L1'),
    ]
    
    scores = model.score_edges(potential_edges)
    
    for (u, v, layer), score in zip(potential_edges, scores):
        print(f"  Edge ({u}, {v}) in {layer}: {score:.4f}")
    
    print()


def example_4_uncertainty():
    """Example 4: Uncertainty quantification."""
    print("=" * 60)
    print("Example 4: Uncertainty Quantification")
    print("=" * 60)
    
    # Generate network with 2 communities
    net, true_labels = generate_aligned_network(
        n_nodes=8, n_layers=2, n_communities=2, p_within=0.6, p_between=0.2, seed=44
    )
    
    # Fit model
    model = fit_multilayer_sbm(
        net, n_blocks=2, n_init=2, max_iter=50, verbose=False, seed=42
    )
    
    print("Node assignment uncertainties:")
    print(f"{'Node':<6} {'Community':<12} {'True':<6} {'Confidence':<12} {'Entropy':<12}")
    print("-" * 54)
    
    for node_id in range(8):
        community = model.hard_membership_[node_id]
        true_comm = true_labels[node_id]
        confidence = model.uncertainty_['confidence'][node_id]
        entropy = model.uncertainty_['entropy'][node_id]
        print(f"{node_id:<6} {community:<12} {true_comm:<6} {confidence:<12.3f} {entropy:<12.3f}")
    
    print()


def example_5_layer_coupling():
    """Example 5: Different layer coupling modes."""
    print("=" * 60)
    print("Example 5: Layer Coupling Modes")
    print("=" * 60)
    
    # Generate network
    net, _ = generate_aligned_network(
        n_nodes=16, n_layers=2, n_communities=4, p_within=0.5, p_between=0.1
    )
    
    # Try different coupling modes
    modes = ['independent', 'shared_blocks', 'shared_affinity']
    
    for mode in modes:
        model = fit_multilayer_sbm(
            net, n_blocks=4, layer_mode=mode,
            n_init=2, max_iter=30, verbose=False, seed=42
        )
        
        summary = model.get_summary()
        print(f"\nMode: {mode}")
        print(f"  ELBO: {summary['final_elbo']:.2f}")
        print(f"  Blocks used: {summary['n_blocks_used']}")
        print(f"  Converged: {summary['converged']}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Multilayer SBM Tutorial")
    print("=" * 60 + "\n")
    
    # Run examples
    example_1_basic_fitting()
    example_2_model_selection()
    example_3_link_prediction()
    example_4_uncertainty()
    example_5_layer_coupling()
    
    print("=" * 60)
    print("Tutorial Complete!")
    print("=" * 60)
