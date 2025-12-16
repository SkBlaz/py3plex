"""
Load multilayer networks from assorted file formats and re-save them.

Shows how to load monoplex and multilayer networks (GML, gpickle, edgelist,
MATLAB sparse matrix, multiedgelist, multiplex_edges) and then persist the last
successful load to gpickle. Prerequisites: bundled datasets (see
`py3plex/utils/get_dataset_path`) must be present locally.

SKIP_CI: external_deps - Requires optional datasets.
"""

from __future__ import annotations

from pathlib import Path

from py3plex.core import multinet
from py3plex.utils import get_dataset_path, get_data_path


def load_multiedgelist_example() -> None:
    """Load and analyze a multilayer network from multiedgelist format."""
    print("=" * 70)
    print("LOADING MULTILAYER NETWORK FROM MULTIEDGELIST FORMAT")
    print("=" * 70)

    # Check if file exists
    multiedgelist_path = Path(get_dataset_path("multiedgelist2.txt"))
    if not multiedgelist_path.exists():
        print(f"Warning: File '{multiedgelist_path}' not found.")
        print("Skipping this example. Please ensure the file exists.\n")
        return

    # Load a multilayer network from multiedgelist format
    # Format: node1 layer1 node2 layer2 weight (one edge per line)
    multilayer_network = multinet.multi_layer_network().load_network(
        str(multiedgelist_path),
        directed=False,
        input_type="multiedgelist",
    )

    print(f"Network loaded from: {multiedgelist_path}")
    print("\nBasic network statistics:")
    multilayer_network.basic_stats()

    # Analyze node-layer structure
    print("\nAnalyzing node-layer structure...")
    node_layer_tuples = set()
    unique_nodes = set()

    for node in multilayer_network.get_nodes():
        node_layer_tuples.add(node)
        unique_nodes.add(node[0])  # Extract just the node ID

    print(f"  Total node-layer tuples: {len(node_layer_tuples)}")
    print(f"  Unique nodes: {len(unique_nodes)}")
    print(f"  Average layers per node: {len(node_layer_tuples) / len(unique_nodes):.2f}")


def load_monoplex_examples() -> multinet.multi_layer_network:
    """Load simple networks from various monoplex formats."""
    print("\n" + "=" * 70)
    print("LOADING SIMPLE NETWORKS (MONOPLEX FORMATS)")
    print("=" * 70)

    last_network = None

    # Example 1: Loading from GML format
    print("\n1. GML format (Graph Modeling Language):")
    gml_path = Path(get_dataset_path("ecommerce_0.gml"))
    if gml_path.exists():
        last_network = multinet.multi_layer_network().load_network(
            str(gml_path),
            directed=True,
            input_type="gml",
        )
        print(f"   [OK] Loaded: {gml_path}")
    else:
        print(f"   [X] Not found: {gml_path}")

    # Example 2: Loading from gpickle_biomine format
    print("\n2. gpickle_biomine format (specialized biological networks):")
    gpickle_path = Path(get_dataset_path("epigenetics.gpickle"))
    if gpickle_path.exists():
        last_network = multinet.multi_layer_network().load_network(
            str(gpickle_path),
            directed=True,
            input_type="gpickle_biomine",
        )
        print(f"   [OK] Loaded: {gpickle_path}")
    else:
        print(f"   [X] Not found: {gpickle_path}")

    # Example 3: Loading from sparse matrix format (.mat)
    print("\n3. Sparse matrix format (.mat - MATLAB format):")
    mat_path = Path(get_dataset_path("ions.mat"))
    if mat_path.exists():
        last_network = multinet.multi_layer_network().load_network(
            str(mat_path),
            directed=False,
            input_type="sparse",
        )
        print(f"   [OK] Loaded: {mat_path}")
    else:
        print(f"   [X] Not found: {mat_path}")

    # Example 4: Loading from simple edgelist
    print("\n4. Simple edgelist format (node1 node2 per line):")
    edgelist_path = Path(get_dataset_path("test.edgelist"))
    if edgelist_path.exists():
        last_network = multinet.multi_layer_network().load_network(
            str(edgelist_path),
            directed=False,
            input_type="edgelist",
        )
        print(f"   [OK] Loaded: {edgelist_path}")
    else:
        print(f"   [X] Not found: {edgelist_path}")

    return last_network


def load_multilayer_examples() -> multinet.multi_layer_network:
    """Load networks from multilayer/multiplex-specific formats."""
    print("\n" + "=" * 70)
    print("MULTILAYER/MULTIPLEX-SPECIFIC FORMATS")
    print("=" * 70)

    last_network = None

    # Example 5: Multiedgelist format (N L N L w)
    print("\n5. Multiedgelist format (node1 layer1 node2 layer2 weight):")
    multiedge_path = Path(get_dataset_path("multiedgelist.txt"))
    if multiedge_path.exists():
        last_network = multinet.multi_layer_network().load_network(
            str(multiedge_path),
            directed=False,
            input_type="multiedgelist",
        )
        print(f"   [OK] Loaded: {multiedge_path}")
    else:
        print(f"   [X] Not found: {multiedge_path}")

    # Example 6: Multiplex edges format (L N N w)
    # Note: Using network_type="multiplex" here because:
    # - All layers share the same set of nodes (same people/entities)
    # - Different layers represent different relationship types
    # - Automatic coupling edges are added between node copies across layers
    # Use network_type="multilayer" when layers have different node sets
    print("\n6. Multiplex edges format (layer node1 node2 weight):")
    multiplex_path = Path(get_dataset_path("test13.edges"))
    if multiplex_path.exists():
        last_network = multinet.multi_layer_network(
            network_type="multiplex"
        ).load_network(
            str(multiplex_path),
            directed=False,
            input_type="multiplex_edges",
        )
        print(f"   [OK] Loaded: {multiplex_path}")
    else:
        print(f"   [X] Not found: {multiplex_path}")

    return last_network


def save_network_example(network: multinet.multi_layer_network) -> None:
    """Save the network in gpickle format."""
    print("\n" + "=" * 70)
    print("SAVING NETWORK IN GPICKLE FORMAT")
    print("=" * 70)

    if network is None:
        print("No network was successfully loaded, skipping save.")
        return

    datasets_dir = Path(get_data_path("datasets"))
    output_path = datasets_dir / "stored_network.gpickle"

    network.save_network(output_file=str(output_path), output_type="gpickle")
    print(f"[OK] Network saved to: {output_path}")
    print("\nNote: gpickle format is fastest for loading/saving complex networks")


def main() -> int:
    """Run all network loading examples."""
    load_multiedgelist_example()

    # Load monoplex examples and keep last successful network
    last_monoplex = load_monoplex_examples()

    # Load multilayer examples and keep last successful network
    last_multilayer = load_multilayer_examples()

    # Save the last successfully loaded network
    network_to_save = last_multilayer or last_monoplex
    if network_to_save:
        save_network_example(network_to_save)

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
