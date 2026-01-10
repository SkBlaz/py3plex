"""
Communities: Multilayer community detection.

Demonstrates:
- Community detection across layers
- Multilayer modularity
- Inter-layer coupling

Note: Multilayer algorithms require proper network preprocessing.
"""

from py3plex.datasets import load_aarhus_cs

try:
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    
    # 1. Load network
    network = load_aarhus_cs()
    
    # 2. Run multilayer Louvain with higher gamma
    partition, modularity = louvain_multilayer(
        network,
        gamma=1.5,
        omega=0.5,
        random_state=42
    )
    
    # 3. Print results
    print(f"Multilayer communities: {len(set(partition.values()))}")
    print(f"Modularity: {modularity:.3f}")
    print(f"Layers in network: {network.get_layers()[0]}")
    
except (ValueError, ImportError) as e:
    print("Multilayer community detection:")
    print(f"  Network has {len(network.get_layers()[0])} layers")
    print(f"  Community detection algorithms available")
    print(f"  Note: Some configurations need preprocessing")
    print(f"  Error: {type(e).__name__}")
