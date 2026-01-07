"""Example: Minimal 1-line contract usage.

This demonstrates the simplest possible contract usage with all defaults.
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.contracts import Robustness


def main():
    # Create a small network
    net = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': f'N{i}', 'type': 'L0'}
        for i in range(15)
    ]
    net.add_nodes(nodes)
    
    # Create a connected graph with some structure
    edges = []
    # Ring structure
    for i in range(15):
        edges.append({
            'source': f'N{i}',
            'target': f'N{(i+1) % 15}',
            'source_type': 'L0',
            'target_type': 'L0'
        })
    # Add some cross connections for hubs
    for i in [0, 5, 10]:
        for j in range(15):
            if abs(i - j) % 15 > 1:
                edges.append({
                    'source': f'N{i}',
                    'target': f'N{j}',
                    'source_type': 'L0',
                    'target_type': 'L0'
                })
    
    net.add_edges(edges)
    
    print(f"Network: {len(list(net.get_nodes()))} nodes, {len(list(net.get_edges()))} edges")
    
    # 1-LINE CONTRACT USAGE (with explicit small params for testing)
    print("\nRunning contract with top-k query...")
    result = (Q.nodes()
              .compute("degree")
              .order_by("degree", desc=True)
              .limit(5)
              .contract(Robustness(n_samples=3, grid=[0.0, 0.05]))
              .execute(net))
    
    # Check result
    print(f"\nContract OK: {result.contract_ok}")
    
    if result.contract_ok:
        print("✓ Top-5 by degree is stable!")
        df = result.to_pandas()
        print("\nTop-5 nodes:")
        print(df[['node', 'degree']].to_string(index=False))
    else:
        print(f"✗ Contract failed: {result.failure_mode.value if result.failure_mode else 'unknown'}")
        print(f"Message: {result.message}")
        
        if result.repair.stable_core:
            print(f"\nStable core ({len(result.repair.stable_core)} nodes):")
            print(result.repair.stable_core)
    
    # Show provenance
    print("\nProvenance:")
    prov = result.provenance
    if "contract" in prov:
        contract_spec = prov["contract"]
        print(f"  Perturbation: {contract_spec.get('perturb')}")
        print(f"  Grid: {contract_spec.get('grid')}")
        print(f"  Samples: {contract_spec.get('n_samples')}")
        print(f"  Seed: {contract_spec.get('seed')}")
        if contract_spec.get('predicates'):
            pred = contract_spec['predicates'][0]
            print(f"  Predicate: {pred.get('type')} (k={pred.get('k')}, threshold={pred.get('threshold')})")


if __name__ == "__main__":
    main()
