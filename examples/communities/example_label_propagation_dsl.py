"""Example demonstrating label propagation community detection using DSL v2.

This example shows how to use both supra-graph label propagation and
consensus label propagation algorithms via the DSL v2 API.

SKIP_CI: example - Demonstration script
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L


def create_example_network():
    """Create a simple multilayer network for demonstration."""
    net = multinet.multi_layer_network(directed=False)

    # Add edges in social layer
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "social", "target_type": "social"},
        {"source": "B", "target": "C", "source_type": "social", "target_type": "social"},
        {"source": "C", "target": "D", "source_type": "social", "target_type": "social"},
        {"source": "D", "target": "A", "source_type": "social", "target_type": "social"},
    ])

    # Add edges in work layer
    net.add_edges([
        {"source": "A", "target": "B", "source_type": "work", "target_type": "work"},
        {"source": "B", "target": "C", "source_type": "work", "target_type": "work"},
        {"source": "C", "target": "D", "source_type": "work", "target_type": "work"},
        {"source": "D", "target": "E", "source_type": "work", "target_type": "work"},
    ])

    return net


def example_a_supra_lpa():
    """Example A: Run Algorithm 1 (supra) and inspect layer-wise communities."""
    print("\n" + "="*70)
    print("Example A: Supra-Graph Label Propagation")
    print("="*70)

    net = create_example_network()

    # Community detection (supra-LPA)
    res = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="label_propagation_supra",
             omega=0.7,
             projection="none",
             max_iter=50,
             random_state=42,
         )
         .compute("community")  # Add community attribute to output
         .execute(net)
    )

    df = res.to_pandas()
    # id column is the node, layer is the layer
    df = df.rename(columns={"id": "node"})
    print(f"\nDetected communities (replica-level):")
    print(df[["node", "layer", "community"]].to_string(index=False))

    # Show statistics
    n_communities = df["community"].nunique()
    print(f"\nTotal communities: {n_communities}")
    print(f"Total node-layer pairs: {len(df)}")


def example_b_supra_with_projection():
    """Example B: Algorithm 1 with node-level majority projection."""
    print("\n" + "="*70)
    print("Example B: Supra-Graph LPA with Majority Projection")
    print("="*70)

    net = create_example_network()

    res = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="label_propagation_supra",
             omega=1.0,
             projection="majority",
             max_iter=50,
             random_state=42,
         )
         .compute("community")  # Add community attribute to output
         .execute(net)
    )

    df = res.to_pandas()
    df = df.rename(columns={"id": "node"})
    print(f"\nDetected communities (with node-level projection):")
    print(df[["node", "layer", "community"]].to_string(index=False))

    # Show statistics
    print(f"\nCommunity statistics:")
    print(f"  Total communities: {df['community'].nunique()}")
    print(f"  Node-layer pairs: {len(df)}")


def example_c_consensus_lpa():
    """Example C: Run Algorithm 2 (consensus) and get node-level communities."""
    print("\n" + "="*70)
    print("Example C: Multiplex Consensus Label Propagation")
    print("="*70)

    # Create fresh network to avoid partition conflicts
    net = create_example_network()

    res = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="label_propagation_consensus",
             max_iter=25,
             inner_max_iter=50,
             random_state=42,
             partition_name="consensus",  # Use unique name
         )
         .compute("community")  # Add community attribute to output
         .execute(net)
    )

    df = res.to_pandas()
    df = df.rename(columns={"id": "node"})
    print(f"\nDetected communities (node-level consensus):")
    print(df[["node", "layer", "community"]].to_string(index=False))

    # Verify synchronization
    print(f"\nVerifying consensus synchronization:")
    for node in df["node"].unique():
        node_df = df[df["node"] == node]
        communities = node_df["community"].unique()
        status = " synchronized" if len(communities) == 1 else " not synchronized"
        print(f"  Node {node}: {status} (communities: {communities})")


def example_d_post_query_hubs():
    """Example D: Post-query - find top hubs per community."""
    print("\n" + "="*70)
    print("Example D: Find Top Hubs per Community")
    print("="*70)

    # Create fresh network
    net = create_example_network()

    # Run consensus LPA and compute degree
    res = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="label_propagation_consensus",
             max_iter=25,
             inner_max_iter=50,
             random_state=42,
             partition_name="consensus_d",  # Use unique name
         )
         .compute("community", "degree")
         .execute(net)
    )

    df = res.to_pandas()
    df = df.rename(columns={"id": "node"})
    print(f"\nNodes with degree and community:")
    print(df[["node", "layer", "community", "degree"]].to_string(index=False))

    # Find top hubs per community
    print(f"\nTop hub per community:")
    top_hubs = df.loc[df.groupby("community")["degree"].idxmax()]
    print(top_hubs[["community", "node", "degree"]].to_string(index=False))


def compare_algorithms():
    """Compare the two algorithms on the same network."""
    print("\n" + "="*70)
    print("Comparison: Supra vs Consensus LPA")
    print("="*70)

    net = create_example_network()

    # Run both algorithms
    res_supra = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="label_propagation_supra",
             omega=0.5,
             projection="none",
             max_iter=50,
             random_state=42,
         )
         .compute("community")
         .execute(net)
    )

    res_consensus = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="label_propagation_consensus",
             max_iter=25,
             inner_max_iter=50,
             random_state=42,
         )
         .compute("community")
         .execute(net)
    )

    df_supra = res_supra.to_pandas()
    df_consensus = res_consensus.to_pandas()
    df_supra = df_supra.rename(columns={"id": "node"})
    df_consensus = df_consensus.rename(columns={"id": "node"})

    print(f"\nSupra-graph LPA:")
    print(f"  Communities: {df_supra['community'].nunique()}")
    print(f"  Replica assignments: {len(df_supra)}")

    print(f"\nConsensus LPA:")
    print(f"  Communities: {df_consensus['community'].nunique()}")
    print(f"  Replica assignments: {len(df_consensus)}")

    # Check synchronization in consensus
    consensus_synced = all(
        df_consensus[df_consensus["node"] == node]["community"].nunique() == 1
        for node in df_consensus["node"].unique()
    )
    print(f"\nConsensus replicas synchronized: {consensus_synced}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Label Propagation Community Detection Examples (DSL v2)")
    print("="*70)

    example_a_supra_lpa()
    example_b_supra_with_projection()
    example_c_consensus_lpa()
    example_d_post_query_hubs()
    compare_algorithms()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70)


if __name__ == "__main__":
    main()
