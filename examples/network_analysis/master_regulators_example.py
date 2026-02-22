"""Master regulator discovery on a multilayer network (deterministic).

What this shows:
- Loading a built-in multilayer human interactome
- Multilayer community detection (Louvain)
- DSL queries to rank candidate master regulators per layer
- Pandas-friendly outputs saved locally

Prerequisites: py3plex (with bundled datasets), pandas. No network or GUI needed.
SKIP_CI: slow - can take ~30s due to community detection on a 500-node multiplex.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from py3plex.algorithms.community_detection import multilayer_louvain
from py3plex.core import datasets
from py3plex.dsl import Q

# Keep randomness deterministic for reproducibility
SEED = 42
OUTPUT_DIR = Path(__file__).parent / "outputs"


def load_network() -> Optional[object]:
    """Load the built-in multilayer human interactome, with graceful fallback."""
    try:
        return datasets.fetch_multilayer("human_ppi_gene_disease_drug")
    except Exception as exc:  # pragma: no cover - defensive guard for missing data
        print(f"Failed to load built-in dataset: {exc}")
        return None


def summarize_network(network) -> Tuple[int, int, int]:
    """Return (node_count, layer_count, edge_count) and print a summary."""
    node_count = len(list(network.get_nodes()))
    layers_data = network.get_layers()
    layer_count = len(layers_data[0]) if isinstance(layers_data, tuple) and layers_data else 0
    edge_count = len(list(network.get_edges()))
    print(f"Loaded multilayer network: {node_count} nodes, {layer_count} layers, {edge_count} edges")
    return node_count, layer_count, edge_count


def run_community_detection(network) -> None:
    """Assign multilayer Louvain communities to the network."""
    partition_vector, modularity = multilayer_louvain(network, gamma=1.2, random_state=SEED)
    network.assign_partition(partition_vector)
    print(
        f"Multilayer Louvain -> {len(set(partition_vector.values()))} communities, "
        f"modularity = {modularity:.3f}"
    )


def query_master_regulators(network):
    """Run DSL queries to identify candidate master regulators."""
    # Note: layers in this synthetic dataset are numbered 0-3
    master_regulators = (
        Q.nodes()
        .node_type("gene")
        .where(degree__gt=3)
        .per_layer()
        .compute("degree_centrality", "betweenness_centrality")
        .top_k(20, "betweenness_centrality")
        .end_grouping()
        .sort(by="betweenness_centrality", descending=True)
        .limit(20)
        .execute(network)
    )
    df = master_regulators.to_pandas()
    print("\nMaster Regulator Candidates (Top 10 shown):")
    print(df.head(10))
    return df


def query_aggregated_stats(network):
    """Optionally aggregate per-layer statistics for inspection."""

    def _extract_mean(value) -> float:
        """Handle DSL stats objects that store mean/std dictionaries."""
        if isinstance(value, dict) and "mean" in value:
            return float(value["mean"])
        return float(value)

    per_layer_results = (
        Q.nodes()
        .node_type("gene")
        .where(degree__gt=5)
        .per_layer()
        .compute("degree_centrality", "betweenness_centrality")
        .top_k(10, "betweenness_centrality")
        .end_grouping()
        .execute(network)
    )
    per_layer_df = per_layer_results.to_pandas()
    per_layer_df = per_layer_df.assign(
        betweenness_mean=per_layer_df["betweenness_centrality"].apply(_extract_mean),
        degree_mean=per_layer_df["degree_centrality"].apply(_extract_mean),
    )
    summary = (
        per_layer_df.groupby("layer")
        .agg(
            avg_betweenness=("betweenness_mean", "mean"),
            max_betweenness=("betweenness_mean", "max"),
            avg_degree=("degree_mean", "mean"),
            max_degree=("degree_mean", "max"),
            n_candidates=("id", "count"),
        )
        .reset_index()
    )
    print("\nAggregated per-layer statistics:")
    print(summary)
    return per_layer_df, summary


def save_results(df: pd.DataFrame, output_path: Path) -> None:
    """Save candidate regulators to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")
    print(f"Total master regulator candidates identified: {len(df)}")


def maybe_visualize(network, output_path: Path) -> None:
    """Optional: generate a hairball plot if matplotlib is available."""
    try:
        import matplotlib.pyplot as plt  # local import to avoid GUI unless requested
        from py3plex.visualization.multilayer import hairball_plot
    except Exception as exc:  # pragma: no cover - visualization is optional
        print(f"Visualization skipped (dependency/GUI not available): {exc}")
        return

    try:
        hairball_plot(network, layout_parameters={"iterations": 50})
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Visualization saved to {output_path}")
    except Exception as exc:  # pragma: no cover - visualization is optional
        print(f"Visualization skipped: {exc}")


def main() -> int:
    """Execute the master regulator analysis pipeline."""
    np.random.seed(SEED)
    print("=" * 70)
    print("Master Regulators Example")
    print("=" * 70)

    network = load_network()
    if network is None:
        print("Example cannot continue without the dataset.")
        return 1

    summarize_network(network)
    run_community_detection(network)

    candidates = query_master_regulators(network)
    _, summary = query_aggregated_stats(network)

    save_results(candidates, OUTPUT_DIR / "master_regulators.csv")

    # Visualization is optional; uncomment to enable in GUI-capable environments.
    # maybe_visualize(network, OUTPUT_DIR / "network_visualization.png")

    print("\n" + "=" * 70)
    print("MASTER REGULATORS ANALYSIS COMPLETE")
    print("=" * 70)
    print("This example demonstrated: datasets.fetch_multilayer, multilayer_louvain,")
    print("DSL per-layer queries with aggregation, and pandas-friendly outputs.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
