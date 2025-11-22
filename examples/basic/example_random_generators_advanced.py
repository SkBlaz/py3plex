"""
Example demonstrating advanced random multilayer graph generators.

This example shows how to generate synthetic multilayer networks using
various random graph models (Erdős-Rényi, Barabási-Albert, SBM).
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.advanced_random_generators import multilayer_erdos_renyi


def main():
    """Demonstrate random graph generators."""
    print("=== Random Graph Generators Demo ===\n")
    
    # Generate multilayer Erdős-Rényi network
    print("Generating multilayer Erdős-Rényi network...")
    G = multilayer_erdos_renyi(
        n=20,                    # 20 nodes per layer
        p=0.2,                   # 20% edge probability
        num_layers=3,            # 3 layers
        interlayer_prob=0.1,     # 10% inter-layer edge probability
        seed=42                  # For reproducibility
    )
    
    print(f"\nGenerated multilayer ER network:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    
    # Convert to py3plex network for analysis
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.load_network(G, input_type='nx')
    
    print(f"\nConverted to py3plex network:")
    print(f"  {net}")
    
    print("\nAvailable generators:")
    print("  - multilayer_erdos_renyi: Random edges")
    print("  - multilayer_barabasi_albert: Scale-free networks")
    print("  - multilayer_stochastic_block_model: Community structure")
    print("  - multilayer_sbm_with_dependencies: Layer-dependent communities\n")


if __name__ == "__main__":
    main()
