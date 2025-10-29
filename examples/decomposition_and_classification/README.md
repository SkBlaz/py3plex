# Decomposition and Classification Examples

This directory contains examples for network decomposition, machine learning, and node classification.

## Examples

### Network Decomposition

- **`example_decomposition_and_classification.py`** - End-to-end workflow: decompose → classify
- **`example_network_decomposition.py`** - Basic network decomposition methods
- **`example_network_decomposition_different_meta_paths.py`** - Using different meta-paths for decomposition
- **`example_decomposition_ground_truth.py`** - Decomposition with ground truth labels

### Classification Algorithms

- **`example_PPR.py`** - Personalized PageRank (PPR) for node classification
- **`example_multixrank.py`** - MultiXrank algorithm for multilayer networks

### Specialized Methods

- **`example_CBSSD.py`** - Community-Based Semantic Subgroup Discovery (uses UniProt identifiers)
- **`example_semantic_enrichment.py`** - Semantic enrichment and annotation

## Key Concepts

### Network Decomposition
Breaking down networks into subgraphs for analysis:
- **Meta-paths**: Specific path patterns in heterogeneous networks
- **Subgraph extraction**: Extract meaningful substructures
- **Motif-based**: Decompose by network motifs

### Node Classification
Predicting labels for nodes based on network structure:
1. **Feature extraction**: Decompose network into features
2. **Train classifier**: SVM, Random Forest, Neural Networks
3. **Predict**: Classify unlabeled nodes

### Personalized PageRank (PPR)
Random walk-based algorithm that:
- Computes node relevance relative to seed nodes
- Creates feature vectors for classification
- Works well with labeled seed nodes

### MultiXrank
Extends PageRank to multilayer networks:
- Leverages information across layers
- Computes layer-specific rankings
- Useful for heterogeneous networks

## Usage

```bash
# Full classification pipeline
python example_decomposition_and_classification.py

# Personalized PageRank
python example_PPR.py

# MultiXrank algorithm
python example_multixrank.py

# Semantic enrichment
python example_semantic_enrichment.py
```

## Typical Workflow

1. **Load network** with node labels
2. **Decompose** into subgraphs or features
3. **Extract features** from decomposition
4. **Split data** (train/test)
5. **Train classifier** (SVM, etc.)
6. **Evaluate** (F1, accuracy)

## Classification Settings

Examples support:
- **Multiclass**: Each node has one label
- **Multilabel**: Nodes can have multiple labels
- **Semi-supervised**: Learn from partially labeled data
- **Cross-validation**: Stratified splits for evaluation

## Applications

- **Biological networks**: Protein function prediction
- **Social networks**: User interest classification
- **Citation networks**: Paper topic prediction
- **Knowledge graphs**: Entity type prediction

## Related Directories

- See [../embeddings/](../embeddings/) for embedding-based classification
- See [../community_detection/](../community_detection/) for unsupervised grouping
- See [../centrality_and_statistics/](../centrality_and_statistics/) for feature extraction
- See [../dynamics/](../dynamics/) for random walk-based methods
