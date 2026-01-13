"""Example: Contract Failure Modes and Troubleshooting.

This example demonstrates different contract failure modes and how to
interpret and handle them.
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.contracts import Robustness, FailureMode


def make_network(size="small"):
    """Create test networks of different sizes."""
    net = multinet.multi_layer_network(directed=False)

    if size == "tiny":
        # Very small network - will trigger special handling
        nodes = [{'source': f'N{i}', 'type': 'L0'} for i in range(3)]
        edges = [
            {'source': 'N0', 'target': 'N1', 'source_type': 'L0', 'target_type': 'L0'},
            {'source': 'N1', 'target': 'N2', 'source_type': 'L0', 'target_type': 'L0'},
        ]
    elif size == "small":
        # Small network
        nodes = [{'source': f'N{i}', 'type': 'L0'} for i in range(10)]
        edges = []
        for i in range(9):
            edges.append({
                'source': f'N{i}',
                'target': f'N{i+1}',
                'source_type': 'L0',
                'target_type': 'L0'
            })
        # Add some extra connections
        edges.extend([
            {'source': 'N0', 'target': 'N5', 'source_type': 'L0', 'target_type': 'L0'},
            {'source': 'N2', 'target': 'N7', 'source_type': 'L0', 'target_type': 'L0'},
        ])
    else:  # "medium"
        # Medium network
        nodes = [{'source': f'N{i}', 'type': 'L0'} for i in range(50)]
        import random
        random.seed(42)
        edges = []
        # Create a connected graph
        for i in range(49):
            edges.append({
                'source': f'N{i}',
                'target': f'N{i+1}',
                'source_type': 'L0',
                'target_type': 'L0'
            })
        # Add random edges
        for _ in range(100):
            i, j = random.randint(0, 49), random.randint(0, 49)
            if i != j:
                edges.append({
                    'source': f'N{i}',
                    'target': f'N{j}',
                    'source_type': 'L0',
                    'target_type': 'L0'
                })

    net.add_nodes(nodes)
    net.add_edges(edges)
    return net


def example_insufficient_baseline():
    """Example: INSUFFICIENT_BASELINE failure mode."""
    print("="*70)
    print("Example 1: INSUFFICIENT_BASELINE")
    print("="*70)
    print("Requesting top-20 from a network with only 10 nodes...")

    net = make_network("small")
    print(f"Network: {len(list(net.get_nodes()))} nodes")

    # This will fail: asking for top-20 but network only has 10 nodes
    result = (Q.nodes()
              .compute("degree")
              .order_by("degree", desc=True)
              .limit(20)
              .contract(Robustness())
              .execute(net))

    print(f"\nContract OK: {result.contract_ok}")
    print(f"Failure mode: {result.failure_mode.value}")
    print(f"Message: {result.message}")
    print(f"Details: {result.details}")

    print("\nTroubleshooting:")
    print("- Reduce top_k to match available nodes")
    print("- Or expand query to include more nodes")
    print()


def example_nondeterminism_leak():
    """Example: NONDETERMINISM_LEAK failure mode."""
    print("="*70)
    print("Example 2: NONDETERMINISM_LEAK")
    print("="*70)
    print("Attempting to use seed=None without explicit permission...")

    try:
        # This will fail at contract construction
        contract = Robustness(seed=None, allow_nondeterminism=False)
    except ValueError as e:
        print(f"\n ValueError: {e}")
        print("\nTroubleshooting:")
        print("- Set seed=0 (or any integer) for deterministic evaluation")
        print("- Or set allow_nondeterminism=True if you don't need reproducibility")

    print("\n Fixed version:")
    contract = Robustness(seed=0)
    print(f"  seed={contract.seed}, allow_nondeterminism={contract.allow_nondeterminism}")
    print()


def example_contract_violation_with_repair():
    """Example: CONTRACT_VIOLATION with successful repair."""
    print("="*70)
    print("Example 3: CONTRACT_VIOLATION with Repair")
    print("="*70)

    net = make_network("small")
    print(f"Network: {len(list(net.get_nodes()))} nodes, {len(list(net.get_edges()))} edges")

    # Query that may violate contract but can be repaired
    print("\nQuerying top-7 by degree with small perturbations...")
    result = (Q.nodes()
              .compute("degree")
              .order_by("degree", desc=True)
              .limit(7)
              .contract(Robustness(n_samples=5, grid=[0.0, 0.05, 0.10]))
              .execute(net))

    print(f"\nContract OK: {result.contract_ok}")

    if not result.contract_ok:
        print(f"Failure mode: {result.failure_mode.value}")
        print(f"Message: {result.message}")

        # Check repair
        if result.repair.repaired_ok and result.repair.stable_core:
            print(f"\n Repair successful!")
            print(f"  Stable core: {len(result.repair.stable_core)} out of {7} nodes")
            print(f"  Stable nodes: {result.repair.stable_core}")

            # Get DataFrame with repair columns
            df = result.to_pandas(expand_contract=True)
            if df is not None and len(df) > 0:
                stable_df = df[df['is_in_stable_core']] if 'is_in_stable_core' in df.columns else df
                print(f"\n  Stable core details:")
                # Print available columns
                cols_to_show = [c for c in df.columns if c not in ['is_in_stable_core', 'contract_ok', 'failure_mode']]
                if len(cols_to_show) > 0:
                    print(stable_df[cols_to_show[:3]].to_string(index=False))  # Show first 3 columns
                else:
                    print("  (No data columns available)")
            else:
                print("  (DataFrame is empty)")
        else:
            print(f"\n Repair failed: {result.repair.metadata.get('reason')}")
    else:
        print("All nodes in top-7 are stable!")

    print()


def example_tiny_graph_adaptation():
    """Example: Automatic adaptation for tiny graphs."""
    print("="*70)
    print("Example 4: Tiny Graph Adaptation")
    print("="*70)

    net = make_network("tiny")
    n_nodes = len(list(net.get_nodes()))
    n_edges = len(list(net.get_edges()))
    print(f"Network: {n_nodes} nodes, {n_edges} edges (tiny graph: E < 20)")

    # Contract will automatically adapt parameters
    result = (Q.nodes()
              .compute("degree")
              .order_by("degree", desc=True)
              .limit(2)
              .contract(Robustness())
              .execute(net))

    # Check provenance to see adapted parameters
    prov = result.provenance
    if "contract" in prov:
        contract_spec = prov["contract"]
        print(f"\nAuto-adapted parameters:")
        print(f"  p_max: {contract_spec.get('p_max')} (capped at 0.05 for tiny graphs)")
        print(f"  grid: {contract_spec.get('grid')} (reduced to avoid degeneracy)")
        print(f"  n_samples: {contract_spec.get('n_samples')} (bumped for small graph)")

    print(f"\nContract OK: {result.contract_ok}")
    print()


def example_provenance_and_replay():
    """Example: Provenance recording and deterministic replay."""
    print("="*70)
    print("Example 5: Provenance and Deterministic Replay")
    print("="*70)

    net = make_network("small")

    print("Running contract with seed=0 (default)...")
    result1 = (Q.nodes()
               .compute("degree")
               .order_by("degree", desc=True)
               .limit(5)
               .contract(Robustness(n_samples=3))
               .execute(net))

    print(f"First run - Contract OK: {result1.contract_ok}")

    # Run again with same seed
    print("\nRe-running with same seed (deterministic replay)...")
    result2 = (Q.nodes()
               .compute("degree")
               .order_by("degree", desc=True)
               .limit(5)
               .contract(Robustness(n_samples=3))
               .execute(net))

    print(f"Second run - Contract OK: {result2.contract_ok}")

    # Check determinism
    if result1.contract_ok == result2.contract_ok:
        print("\n Results are deterministic (both runs match)")
    else:
        print("\n Results differ (unexpected!)")

    # Show provenance
    print("\nProvenance (full contract spec recorded):")
    if "contract" in result1.provenance:
        contract_spec = result1.provenance["contract"]
        for key in ["perturb", "grid", "n_samples", "seed"]:
            print(f"  {key}: {contract_spec.get(key)}")

    print()


def main():
    """Run all examples."""
    print("\nROBUSTNESS CONTRACTS: FAILURE MODES AND TROUBLESHOOTING")
    print("="*70)
    print()

    example_insufficient_baseline()
    example_nondeterminism_leak()
    example_contract_violation_with_repair()
    example_tiny_graph_adaptation()
    example_provenance_and_replay()

    print("="*70)
    print("For more information:")
    print("  - See AGENTS.md section 'Robustness Contracts'")
    print("  - Check failure mode details: help(FailureMode)")
    print("="*70)


if __name__ == "__main__":
    main()
