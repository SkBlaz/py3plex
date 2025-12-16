"""Run all Query Zoo examples and generate outputs.

Teaches how to orchestrate the DSL Query Zoo: loading datasets, running each
query, and saving CSVs/plots for inspection. Prerequisites: py3plex installed
with pandas, matplotlib (Agg backend), and seaborn available.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Callable, Optional
import traceback

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pandas as pd

    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as exc:  # pragma: no cover - surfaced to user
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

from examples.dsl_query_zoo.datasets import get_dataset
from examples.dsl_query_zoo.queries import (
    query_advanced_centrality_comparison,
    query_basic_exploration,
    query_community_structure,
    query_cross_layer_hubs,
    query_layer_similarity,
    query_multiplex_pagerank,
    query_robustness_analysis,
)

DEFAULT_SEED = 42


def _set_seeds(seed: int = DEFAULT_SEED) -> None:
    """Ensure deterministic behaviour for any random components."""
    random.seed(seed)
    np.random.seed(seed)


def setup_output_dir() -> Path:
    """Create output directory if it doesn't exist."""
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def save_dataframe(df: pd.DataFrame, filename: str, output_dir: Path) -> Path:
    """Save DataFrame to CSV."""
    filepath = output_dir / filename
    df.to_csv(filepath, index=False)
    print(f"  Saved: {filename}")
    return filepath


def plot_layer_stats(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create a bar plot of layer statistics."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # Plot 1: Number of nodes per layer
    axes[0].bar(df['layer'], df['n_nodes'], color='skyblue')
    axes[0].set_title('Nodes per Layer')
    axes[0].set_xlabel('Layer')
    axes[0].set_ylabel('Number of Nodes')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Plot 2: Number of edges per layer
    axes[1].bar(df['layer'], df['n_edges'], color='lightcoral')
    axes[1].set_title('Edges per Layer')
    axes[1].set_xlabel('Layer')
    axes[1].set_ylabel('Number of Edges')
    axes[1].tick_params(axis='x', rotation=45)
    
    # Plot 3: Average degree per layer
    axes[2].bar(df['layer'], df['avg_degree'], color='lightgreen')
    axes[2].set_title('Average Degree per Layer')
    axes[2].set_xlabel('Layer')
    axes[2].set_ylabel('Average Degree')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    filepath = output_dir / 'basic_exploration_plot.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: basic_exploration_plot.png")
    return filepath


def plot_layer_similarity(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create a heatmap of layer similarity."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, ax=ax, cbar_kws={'label': 'Correlation'})
    ax.set_title('Layer Similarity (Degree Distribution Correlation)')
    
    plt.tight_layout()
    filepath = output_dir / 'layer_similarity_heatmap.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: layer_similarity_heatmap.png")
    return filepath


def plot_robustness(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create a plot showing connectivity loss when layers are removed."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scenarios = df['scenario'].tolist()
    connectivity_loss = df['connectivity_loss'].tolist()
    
    colors = ['green' if loss == 0 else 'orange' if loss < 50 else 'red' 
              for loss in connectivity_loss]
    
    ax.barh(scenarios, connectivity_loss, color=colors, alpha=0.7)
    ax.set_xlabel('Connectivity Loss (%)')
    ax.set_title('Network Robustness: Impact of Layer Removal')
    ax.axvline(x=0, color='black', linewidth=0.5)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    filepath = output_dir / 'robustness_analysis_plot.png'
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: robustness_analysis_plot.png")
    return filepath


def _preview_dataframe(
    df: pd.DataFrame, rows: Optional[int] = 10, show_index: bool = False
) -> str:
    """Return a formatted preview string for console output."""
    if rows is None:
        return df.to_string(index=show_index)
    return df.head(rows).to_string(index=show_index)


def _execute_query(
    label: str,
    func: Callable[..., pd.DataFrame],
    args: tuple,
    output_name: str,
    output_dir: Path,
    *,
    plotter: Optional[Callable[[pd.DataFrame, Path], Path]] = None,
    preview_rows: Optional[int] = 10,
    show_index: bool = False,
) -> None:
    """Run one query function with consistent logging and error handling."""
    print(label)
    try:
        result = func(*args)
    except Exception as exc:  # pragma: no cover - surfaced to user
        print(f"  ERROR: {exc}")
        traceback.print_exc()
        print()
        return

    if not isinstance(result, pd.DataFrame):
        print(f"  Unexpected result type: {type(result)}\n")
        return

    save_dataframe(result, output_name, output_dir)

    if plotter:
        plotter(result, output_dir)

    preview = _preview_dataframe(result, rows=preview_rows, show_index=show_index)
    print(f"  Result preview:\n{preview}\n")


def _load_datasets(seed: int):
    """Load all toy networks with a shared seed."""
    print("Loading datasets...")
    social_work_net = get_dataset("social_work", seed=seed)
    communication_net = get_dataset("communication", seed=seed)
    transport_net = get_dataset("transport", seed=seed)
    print("  ✓ Datasets loaded\n")
    return social_work_net, communication_net, transport_net


def run_all_queries(seed: int = DEFAULT_SEED) -> None:
    """Execute all queries and save outputs."""
    if IMPORT_ERROR:
        print(f"Missing dependency: {IMPORT_ERROR}")
        print("Install py3plex with plotting extras to run the Query Zoo.")
        return

    _set_seeds(seed)

    print("=" * 80)
    print("DSL QUERY ZOO: Running All Examples")
    print("=" * 80)

    output_dir = setup_output_dir()
    print(f"\nOutput directory: {output_dir}\n")

    social_work_net, communication_net, transport_net = _load_datasets(seed)

    _execute_query(
        "[1/7] Running: Basic Multilayer Exploration",
        query_basic_exploration,
        (social_work_net,),
        "basic_exploration.csv",
        output_dir,
        plotter=plot_layer_stats,
        preview_rows=None,
    )

    _execute_query(
        "[2/7] Running: Cross-Layer Hubs",
        query_cross_layer_hubs,
        (social_work_net, 5),
        "cross_layer_hubs.csv",
        output_dir,
    )

    _execute_query(
        "[3/7] Running: Layer Similarity Analysis",
        query_layer_similarity,
        (social_work_net,),
        "layer_similarity.csv",
        output_dir,
        plotter=plot_layer_similarity,
        preview_rows=None,
        show_index=True,
    )

    _execute_query(
        "[4/7] Running: Community Structure Analysis",
        query_community_structure,
        (communication_net,),
        "community_structure.csv",
        output_dir,
    )

    _execute_query(
        "[5/7] Running: Multiplex PageRank",
        query_multiplex_pagerank,
        (transport_net,),
        "multiplex_pagerank.csv",
        output_dir,
    )

    _execute_query(
        "[6/7] Running: Robustness Analysis",
        query_robustness_analysis,
        (transport_net,),
        "robustness_analysis.csv",
        output_dir,
        plotter=plot_robustness,
        preview_rows=None,
    )

    _execute_query(
        "[7/7] Running: Advanced Centrality Comparison",
        query_advanced_centrality_comparison,
        (communication_net,),
        "centrality_comparison.csv",
        output_dir,
    )

    print("=" * 80)
    print("QUERY ZOO EXECUTION COMPLETE")
    print("=" * 80)
    print(f"\nAll outputs saved to: {output_dir}")
    print("\nGenerated files:")
    for file in sorted(output_dir.glob("*")):
        print(f"  - {file.name}")


def main() -> int:
    """CLI entrypoint when running as a script."""
    run_all_queries(seed=DEFAULT_SEED)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
