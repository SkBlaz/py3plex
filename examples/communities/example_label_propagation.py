"""
Community Detection Example: Label Propagation Algorithm

Teaches:
- Load a sparse network (`cora.mat`) and run semi-supervised label propagation
- Compare normalization schemes for node classification performance
- Summarize results and (optionally) render a headless plot

Prerequisites:
- Dataset: `cora.mat` reachable via `py3plex.utils.get_dataset_path`
- Optional: matplotlib + seaborn for plotting (Agg backend enabled)

SKIP_CI: external_deps - Requires specific dataset files
"""

from __future__ import annotations

import os
from typing import List

import numpy as np
import pandas as pd

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib = None
    plt = None

try:
    from py3plex.algorithms.network_classification import validate_label_propagation
    from py3plex.core import multinet
    from py3plex.utils import get_dataset_path
    from py3plex.visualization.benchmark_visualizations import plot_core_macro
except ImportError as exc:  # pragma: no cover - surfaced to user
    validate_label_propagation = None
    multinet = None
    get_dataset_path = None
    plot_core_macro = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

DEFAULT_SEED = 42
DEFAULT_PLOT_PATH = "/tmp/label_propagation_macro.png"


def run_label_propagation(normalization_schemes: List[str]) -> pd.DataFrame:
    """Evaluate label propagation across normalization schemes."""
    dataset_path = get_dataset_path("cora.mat")

    if not os.path.exists(dataset_path):
        print(f"Dataset file '{dataset_path}' not found. Skipping run.")
        return pd.DataFrame()

    print("\nStep 1: Loading network from sparse matrix")
    print("-" * 70)
    print(f"  Dataset: {dataset_path}")

    multilayer_network = multinet.multi_layer_network().load_network(
        dataset_path,
        directed=False,
        input_type="sparse",
    )
    print("  [OK] Network loaded successfully!")

    print(
        """
NOTE: Sparse matrices are optimized for memory efficiency.
Some operations like basic_stats() may not be available
for sparse representations. Use sparse_to_px() to convert
if full functionality is needed.
"""
    )

    print("Step 2: Configuring normalization schemes")
    print("-" * 70)
    for scheme in normalization_schemes:
        print(f"    - {scheme}")

    print("\nStep 3: Running label propagation experiments")
    print("-" * 70)
    print("  This will perform cross-validation for each scheme...")

    result_frames = []
    total_schemes = len(normalization_schemes)

    for idx, scheme in enumerate(normalization_schemes, 1):
        print(f"\n  [{idx}/{total_schemes}] Evaluating scheme: {scheme}")
        try:
            result = validate_label_propagation(
                multilayer_network.core_network,
                multilayer_network.labels,
                dataset_name="cora_classic",
                repetitions=5,
                normalization_scheme=scheme,
                random_seed=DEFAULT_SEED,
            )
            result_frames.append(result)
            print(f"    [OK] Completed validation for {scheme}")
        except Exception as exc:
            print(f"    [X] Error with scheme {scheme}: {exc}")
            continue

    validation_results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()

    if validation_results.empty:
        print("\n  [X] No successful validations. Cannot generate results.")
        return pd.DataFrame()

    return validation_results


def summarize_results(validation_results: pd.DataFrame) -> None:
    """Print aggregated metrics and optionally plot them."""
    print("\nStep 4: Aggregating results")
    print("-" * 70)
    validation_results = validation_results.reset_index(drop=True)
    print("  [OK] Results aggregated successfully!")
    print(f"\n  Total experiments: {len(validation_results)}")

    print("\nResults summary:")
    print("-" * 70)
    if "normalization_scheme" in validation_results.columns:
        summary = validation_results.groupby("normalization_scheme").agg(
            {"macro_F": ["mean", "std"], "micro_F": ["mean", "std"]}
        )
        print(summary)

    print("\nStep 5: Visualizing results")
    print("-" * 70)
    if plot_core_macro and matplotlib and plt:
        try:
            plot_core_macro(validation_results)
            plt.savefig(DEFAULT_PLOT_PATH, bbox_inches="tight")
            plt.close("all")
            print(f"  [OK] Plot saved to {DEFAULT_PLOT_PATH}")
        except Exception as exc:
            print(f"  [X] Visualization error: {exc}")
            print("  Continuing with text results...")
    else:
        print("  Plotting skipped (matplotlib or seaborn not available).")

    if "macro_F" in validation_results.columns:
        best_idx = validation_results["macro_F"].idxmax()
        best_result = validation_results.loc[best_idx]

        print("\nBest performing configuration:")
        if "normalization_scheme" in best_result:
            print(f"  Scheme: {best_result['normalization_scheme']}")
        if "macro_F" in best_result:
            print(f"  Macro-F1: {best_result['macro_F']:.4f}")
        if "micro_F" in best_result:
            print(f"  Micro-F1: {best_result['micro_F']:.4f}")

    print("\nKey insights:")
    print("  - Label propagation leverages network structure for classification")
    print("  - Different normalization schemes suit different network types")
    print("  - Performance depends on label correlation with topology")
    print("  - Works well with limited labeled data")

    print("\nNext steps:")
    print("  - Try different propagation iterations")
    print("  - Experiment with various train/test splits")
    print("  - Compare with supervised learning methods")
    print("  - Apply to your own labeled networks")


def main() -> int:
    """Run the label propagation comparison."""
    if IMPORT_ERROR:
        print(f"Error importing dependencies: {IMPORT_ERROR}")
        print("Install py3plex (and matplotlib/seaborn for plotting) to run this example.")
        return 1

    np.random.seed(DEFAULT_SEED)

    print("=" * 70)
    print("LABEL PROPAGATION FOR NODE CLASSIFICATION")
    print("=" * 70)

    normalization_schemes = ["freq", "basic", "freq_amplify", "exp"]
    results = run_label_propagation(normalization_schemes)
    if results.empty:
        return 1

    summarize_results(results)
    print("\n" + "=" * 70)
    print("LABEL PROPAGATION COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
