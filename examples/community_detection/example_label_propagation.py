"""
Community Detection Example: Label Propagation Algorithm

This example demonstrates how to:
1. Load a network from a sparse matrix format
2. Apply label propagation for semi-supervised node classification
3. Compare different normalization schemes
4. Visualize and evaluate classification performance

Label propagation is a semi-supervised learning algorithm that:
- Uses labeled nodes to infer labels of unlabeled nodes
- Propagates information through network connections
- Works well when labels correlate with network structure

Use cases:
- Node classification with limited labeled data
- Community detection using seed nodes
- Information diffusion simulation

SKIP_CI: external_deps - Requires specific dataset files
"""

import os
import pandas as pd
from py3plex.core import multinet
from py3plex.algorithms.network_classification import validate_label_propagation
from py3plex.visualization.benchmark_visualizations import plot_core_macro
from py3plex.utils import get_dataset_path

print("=" * 70)
print("LABEL PROPAGATION FOR NODE CLASSIFICATION")
print("=" * 70)

# Define dataset path
dataset_path = get_dataset_path("cora.mat")

# Check if file exists
if not os.path.exists(dataset_path):
    print(f"Error: Dataset file '{dataset_path}' not found.")
    print("This example requires the Cora citation network dataset.")
    exit(1)

print("\nStep 1: Loading network from sparse matrix")
print("-" * 70)
print(f"  Dataset: {dataset_path}")

# Load network from sparse matrix format
# The .mat file should contain:
# - network: sparse adjacency matrix
# - labels: node class labels
multilayer_network = multinet.multi_layer_network().load_network(
    dataset_path,
    directed=False,
    input_type="sparse"
)

print("  ✓ Network loaded successfully!")

# Note about sparse matrices
print("""
NOTE: Sparse matrices are optimized for memory efficiency.
Some operations like basic_stats() may not be available
for sparse representations. Use sparse_to_px() to convert
if full functionality is needed.
""")

print("Step 2: Configuring normalization schemes")
print("-" * 70)

# Different schemes for weighting label propagation
# Each emphasizes different aspects of network structure
normalization_schemes = ["freq", "basic", "freq_amplify", "exp"]

print("  Normalization schemes to evaluate:")
print("    - freq: Frequency-based normalization")
print("    - basic: Simple neighbor averaging")
print("    - freq_amplify: Amplified frequency weighting")
print("    - exp: Exponential decay weighting")

print("\nStep 3: Running label propagation experiments")
print("-" * 70)
print("  This will perform cross-validation for each scheme...")
print("  (This may take a few minutes)")

result_frames = []
total_schemes = len(normalization_schemes)

# Validate each normalization scheme
for idx, scheme in enumerate(normalization_schemes, 1):
    print(f"\n  [{idx}/{total_schemes}] Evaluating scheme: {scheme}")
    
    try:
        # Perform k-fold cross-validation
        # Tests label propagation with different train/test splits
        result = validate_label_propagation(
            multilayer_network.core_network,
            multilayer_network.labels,
            dataset_name="cora_classic",
            repetitions=5,              # Number of repetitions for robustness
            normalization_scheme=scheme
        )
        
        result_frames.append(result)
        print(f"    ✓ Completed validation for {scheme}")
        
    except Exception as e:
        print(f"    ✗ Error with scheme {scheme}: {e}")
        continue

if not result_frames:
    print("\n  ✗ No successful validations. Cannot generate results.")
    exit(1)

print("\nStep 4: Aggregating results")
print("-" * 70)

# Combine all results into a single DataFrame
validation_results = pd.DataFrame()

for result_frame in result_frames:
    validation_results = pd.concat(
        [validation_results, result_frame],
        ignore_index=True
    )

# Reset index for clean output
validation_results.reset_index(drop=True, inplace=True)

print("  ✓ Results aggregated successfully!")
print(f"\n  Total experiments: {len(validation_results)}")

# Display results summary
print("\nResults summary:")
print("-" * 70)
if 'normalization_scheme' in validation_results.columns:
    summary = validation_results.groupby('normalization_scheme').agg({
        'macro_F': ['mean', 'std'],
        'micro_F': ['mean', 'std']
    })
    print(summary)

print("\nStep 5: Visualizing results")
print("-" * 70)

try:
    # Generate visualization comparing normalization schemes
    # Shows macro-F1 scores across different schemes
    print("  Generating performance comparison plot...")
    print("  (Close the window to exit)")
    
    plot_core_macro(validation_results)
    
    print("  ✓ Visualization complete!")
    
except Exception as e:
    print(f"  ✗ Visualization error: {e}")
    print("  Continuing with text results...")

print("\n" + "=" * 70)
print("LABEL PROPAGATION COMPLETE")
print("=" * 70)

# Find best performing scheme
if 'macro_F' in validation_results.columns:
    best_idx = validation_results['macro_F'].idxmax()
    best_result = validation_results.loc[best_idx]
    
    print("\nBest performing configuration:")
    if 'normalization_scheme' in best_result:
        print(f"  Scheme: {best_result['normalization_scheme']}")
    if 'macro_F' in best_result:
        print(f"  Macro-F1: {best_result['macro_F']:.4f}")
    if 'micro_F' in best_result:
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
