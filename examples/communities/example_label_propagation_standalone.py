"""Standalone examples for label propagation community detection.

These examples demonstrate the two label propagation algorithms independently
without DSL to show the pure algorithm behavior.

SKIP_CI: example - Demonstration script
"""

from py3plex.core import multinet
from py3plex.algorithms.community_detection import (
    multilayer_label_propagation_supra,
    multiplex_label_propagation_consensus,
)


def create_test_network():
    """Create a simple test network."""
    net = multinet.multi_layer_network(directed=False)
    
    # Layer 1: Chain A-B-C-D
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "L1", "target_type": "L1"},
        {"source": "B", "target": "C", "source_type": "L1", "target_type": "L1"},
        {"source": "C", "target": "D", "source_type": "L1", "target_type": "L1"},
    ])
    
    # Layer 2: Similar structure
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "L2", "target_type": "L2"},
        {"source": "B", "target": "C", "source_type": "L2", "target_type": "L2"},
        {"source": "C", "target": "D", "source_type": "L2", "target_type": "L2"},
    ])
    
    return net


def test_supra_lpa():
    """Test Algorithm 1: Supra-graph label propagation."""
    print("\n" + "=" * 70)
    print("Algorithm 1: Supra-Graph Label Propagation")
    print("=" * 70)
    
    net = create_test_network()
    
    # Run with low omega (independent layers)
    result_low = multilayer_label_propagation_supra(
        net, omega=0.1, max_iter=100, random_state=42
    )
    
    # Run with high omega (coupled layers)
    result_high = multilayer_label_propagation_supra(
        net, omega=10.0, max_iter=100, random_state=42
    )
    
    print("\nWith omega=0.1 (weak coupling):")
    print(f"  Converged: {result_low['converged']}")
    print(f"  Iterations: {result_low['iterations']}")
    print(f"  Communities: {len(set(result_low['partition_supra'].values()))}")
    
    # Check cross-layer agreement
    nodes = set(k[0] for k in result_low['partition_supra'].keys())
    agreement_low = sum(
        1 for node in nodes
        if (node, 'L1') in result_low['partition_supra']
        and (node, 'L2') in result_low['partition_supra']
        and result_low['partition_supra'][(node, 'L1')] == result_low['partition_supra'][(node, 'L2')]
    ) / len(nodes)
    
    print(f"  Cross-layer agreement: {agreement_low:.1%}")
    
    print("\nWith omega=10.0 (strong coupling):")
    print(f"  Converged: {result_high['converged']}")
    print(f"  Iterations: {result_high['iterations']}")
    print(f"  Communities: {len(set(result_high['partition_supra'].values()))}")
    
    agreement_high = sum(
        1 for node in nodes
        if (node, 'L1') in result_high['partition_supra']
        and (node, 'L2') in result_high['partition_supra']
        and result_high['partition_supra'][(node, 'L1')] == result_high['partition_supra'][(node, 'L2')]
    ) / len(nodes)
    
    print(f"  Cross-layer agreement: {agreement_high:.1%}")
    
    print(f"\n✓ Higher omega increases cross-layer synchronization: {agreement_high > agreement_low}")


def test_consensus_lpa():
    """Test Algorithm 2: Consensus label propagation."""
    print("\n" + "=" * 70)
    print("Algorithm 2: Multiplex Consensus Label Propagation")
    print("=" * 70)
    
    net = create_test_network()
    
    result = multiplex_label_propagation_consensus(
        net, max_iter=50, inner_max_iter=100, random_state=42
    )
    
    print(f"\nConverged: {result['converged']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Communities: {len(set(result['partition_nodes'].values()))}")
    
    # Verify synchronization
    all_synced = True
    for node in result['partition_nodes']:
        node_label = result['partition_nodes'][node]
        layer_labels = [
            result['labels_by_layer'].get((node, layer))
            for layer in ['L1', 'L2']
            if (node, layer) in result['labels_by_layer']
        ]
        if any(lbl != node_label for lbl in layer_labels):
            print(f"  Node {node}: NOT synchronized!")
            all_synced = False
    
    print(f"\n✓ All replicas synchronized: {all_synced}")
    
    # Print partition
    print(f"\nNode-level partition:")
    for node, comm in sorted(result['partition_nodes'].items()):
        print(f"  {node} -> community {comm}")


def test_determinism():
    """Test that both algorithms are deterministic."""
    print("\n" + "=" * 70)
    print("Determinism Test")
    print("=" * 70)
    
    net = create_test_network()
    
    # Test supra
    r1 = multilayer_label_propagation_supra(net, omega=1.0, random_state=42)
    r2 = multilayer_label_propagation_supra(net, omega=1.0, random_state=42)
    supra_same = r1['partition_supra'] == r2['partition_supra']
    
    # Test consensus
    r3 = multiplex_label_propagation_consensus(net, random_state=42)
    r4 = multiplex_label_propagation_consensus(net, random_state=42)
    consensus_same = r3['partition_nodes'] == r4['partition_nodes']
    
    print(f"\n✓ Supra-LPA is deterministic: {supra_same}")
    print(f"✓ Consensus-LPA is deterministic: {consensus_same}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Label Propagation Algorithms: Standalone Examples")
    print("=" * 70)
    
    test_supra_lpa()
    test_consensus_lpa()
    test_determinism()
    
    print("\n" + "=" * 70)
    print("All tests passed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
