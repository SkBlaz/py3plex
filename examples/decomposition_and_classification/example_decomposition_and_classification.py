"""
Decomposition and Classification Example: Network Decomposition for Node Classification

This example demonstrates a complete workflow:
1. Load a multilayer/heterogeneous network
2. Decompose it using different heuristics
3. Generate node representations using Personalized PageRank (PPR)
4. Train classifiers to predict node labels
5. Compare performance across decomposition heuristics

This approach is useful for:
- Node classification in heterogeneous networks
- Feature extraction from network structure
- Comparing different network decomposition strategies
- Semi-supervised learning on graphs

The decomposition process extracts meaningful subgraphs (meta-paths)
that capture different aspects of the network structure.
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.svm import SVC
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedShuffleSplit

from py3plex.core import multinet
from py3plex.algorithms.network_classification import PPR

print("=" * 70)
print("NETWORK DECOMPOSITION AND CLASSIFICATION")
print("=" * 70)

# Dataset configuration
dataset = "../datasets/imdb.gpickle"

# Check if dataset exists
if not os.path.exists(dataset):
    print(f"Error: Dataset file '{dataset}' not found.")
    print("This example requires the IMDB network dataset.")
    print("Target nodes must have 'labels' property for classification.")
    exit(1)

print(f"\nStep 1: Loading network")
print("-" * 70)
print(f"  Dataset: {dataset}")

# Load the multilayer network
multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset,
    directed=True,
    input_type=dataset.split(".")[-1]  # Detect format from extension
)

print("  ✓ Network loaded successfully!")
print("\n  Network statistics:")
multilayer_network.basic_stats()

print(f"\nStep 2: Extracting decomposition cycles (meta-paths)")
print("-" * 70)

# Get unique decomposition cycles (meta-paths)
# Meta-paths are sequences of node/edge types that form meaningful patterns
# Example: Author->Paper->Author, Movie->Actor->Movie, etc.
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))

print(f"  Found {len(triplet_set)} unique meta-path patterns:")
for i, triplet in enumerate(triplet_set[:5], 1):  # Show first 5
    print(f"    {i}. {triplet}")
if len(triplet_set) > 5:
    print(f"    ... and {len(triplet_set) - 5} more")

print(f"\nStep 3: Setting up decomposition heuristics")
print("-" * 70)

# Different heuristics for weighting meta-path importance
# Each heuristic emphasizes different structural properties
heuristics = ["idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi"]

print("  Heuristics to evaluate:")
print("    - idf: Inverse Document Frequency (rare paths weighted higher)")
print("    - tf: Term Frequency (common paths weighted higher)")
print("    - chi: Chi-squared test (statistical significance)")
print("    - ig: Information Gain (classification informativeness)")
print("    - gr: Gain Ratio (normalized information gain)")
print("    - delta: Delta measure (distributional difference)")
print("    - rf: Relevance Frequency (relevant occurrence weighting)")
print("    - okapi: Okapi BM25 (information retrieval weighting)")

print(f"\nStep 4: Decomposing network and training classifiers")
print("-" * 70)
print("  This may take several minutes...")

# Initialize results storage
df = pd.DataFrame()
total_combinations = len(heuristics)
current = 0

# Iterate through different decomposition heuristics
for decomposition in multilayer_network.get_decomposition(
    heuristic=heuristics,
    cycle=triplet_set
):
    current += 1
    
    # Unpack decomposition results
    decomposed_network = decomposition[0]  # Decomposed network
    labels = decomposition[1][:, 1]         # Node labels for classification
    heuristic = decomposition[2]            # Current heuristic name
    
    print(f"\n  [{current}/{total_combinations}] Processing heuristic: {heuristic}")
    
    # Construct Personalized PageRank (PPR) matrix
    # PPR provides node representations based on random walk probabilities
    print(f"    - Constructing PPR feature matrix...")
    vectors = PPR.construct_PPR_matrix(decomposed_network)
    
    print(f"    - Feature matrix shape: {vectors.shape}")
    print(f"    - Number of labeled nodes: {len(labels)}")
    
    # Storage for this heuristic's results
    micros = []
    macros = []
    times = []
    
    # Evaluate across different train/test splits
    print(f"    - Evaluating across multiple train/test splits...")
    
    for test_size in np.arange(0.1, 1, 0.1):
        train_size = 1 - test_size
        
        # Stratified split ensures balanced class distribution
        rs = StratifiedShuffleSplit(
            n_splits=10,
            test_size=test_size,
            random_state=612312
        )
        
        # Run multiple splits for robust evaluation
        for train_idx, test_idx in rs.split(vectors, labels):
            start = time.time()
            
            # Split data
            train_x = vectors[train_idx]
            test_x = vectors[test_idx]
            train_labels = labels[train_idx]
            test_labels = labels[test_idx]
            
            # Train SVM classifier
            clf = SVC()
            clf.fit(train_x, train_labels)
            
            # Predict on test set
            preds = clf.predict(test_x)
            
            # Calculate F1 scores
            # Micro-F1: global average (good for imbalanced classes)
            # Macro-F1: average per class (all classes weighted equally)
            mi = f1_score(test_labels, preds, average='micro')
            ma = f1_score(test_labels, preds, average='macro')
            
            end = time.time()
            elapsed = end - start
            
            micros.append(mi)
            macros.append(ma)
            times.append(elapsed)
        
        # Store averaged results for this train/test ratio
        outarray = {
            "percent_train": np.round(train_size, 1),
            "micro_F": np.mean(micros),
            "macro_F": np.mean(macros),
            "setting": "PPR",
            "time": np.mean(times),
            "heuristic": heuristic
        }
        df = pd.concat([df, pd.DataFrame([outarray])], ignore_index=True)

print("\n" + "=" * 70)
print("CLASSIFICATION RESULTS")
print("=" * 70)

# Display results summary
print("\nResults DataFrame:")
print(df.to_string(index=False))

# Find best performing heuristic
best_heuristic = df.loc[df['micro_F'].idxmax()]
print(f"\nBest Performing Configuration:")
print(f"  Heuristic: {best_heuristic['heuristic']}")
print(f"  Training %: {best_heuristic['percent_train'] * 100:.0f}%")
print(f"  Micro-F1: {best_heuristic['micro_F']:.4f}")
print(f"  Macro-F1: {best_heuristic['macro_F']:.4f}")
print(f"  Avg Time: {best_heuristic['time']:.4f}s")

print(f"\nStep 5: Visualizing results")
print("-" * 70)

# Create visualization
plt.figure(figsize=(12, 6))
sns.lineplot(
    data=df,
    x='percent_train',
    y='micro_F',
    hue='heuristic',
    marker='o',
    linewidth=2
)

plt.xlabel('Training Data Percentage', fontsize=12)
plt.ylabel('Micro-F1 Score', fontsize=12)
plt.title('Classification Performance vs Training Data Size', fontsize=14)
plt.legend(title='Heuristic', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()

print("  Generating visualization...")
print("  (Close the window to exit)")

plt.show()

print("\n" + "=" * 70)
print("DECOMPOSITION AND CLASSIFICATION COMPLETE")
print("=" * 70)

print("\nKey Insights:")
print("  - Different heuristics capture different network properties")
print("  - Performance typically improves with more training data")
print("  - PPR-based features are effective for heterogeneous networks")
print("  - Meta-path decomposition preserves semantic relationships")

print("\nNext Steps:")
print("  - Try different classifiers (Random Forest, Neural Networks)")
print("  - Experiment with different meta-path patterns")
print("  - Combine multiple heuristics for ensemble methods")
print("  - Apply to other heterogeneous network datasets")
