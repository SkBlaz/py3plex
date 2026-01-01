# Multilayer Stochastic Block Model (SBM) for py3plex

This module provides implementations of Stochastic Block Models for multiplex and multilayer networks.

## Features

- **Models**: Vanilla SBM and Degree-Corrected SBM (DC-SBM)
- **Inference**: Mean-field variational inference with multiple initialization strategies
- **Layer Coupling**: Independent layers, shared blocks, or shared affinity matrices
- **Model Selection**: Automatic K selection using ELBO, BIC, or ICL
- **Link Prediction**: Built-in edge probability prediction
- **Uncertainty**: Node-level uncertainty quantification
- **Performance**: Sparse-first implementation, no densification

## Quick Start

```python
from py3plex.core import multinet
from py3plex.algorithms.sbm import fit_multilayer_sbm

# Create or load network
net = multinet.multi_layer_network(directed=False)
net.add_edges([...])  # Add your edges

# Fit DC-SBM with 3 blocks
model = fit_multilayer_sbm(
    net,
    n_blocks=3,
    model="dc_sbm",
    layer_mode="shared_blocks",
    n_init=5,
    seed=42
)

# Get community assignments
partition = model.to_partition_vector()

# Link prediction
prob = model.predict_proba(node_u, node_v, layer='L1')
```

## Model Selection

```python
# Try multiple values of K
model, info = fit_multilayer_sbm(
    net,
    n_blocks=[2, 3, 4, 5],
    model="dc_sbm",
    n_init=3,
    seed=42
)

print(f"Best K: {info['best_K']}")
print(info['comparison_table'])
```

## API Reference

### Main Functions

- **`fit_multilayer_sbm(network, n_blocks, ...)`**: Fit SBM to a network
- **`select_multilayer_sbm_model(network, K_list, ...)`**: Model selection wrapper

### Models

- **`model="sbm"`**: Vanilla Stochastic Block Model
  - Bernoulli or Poisson likelihood
  - Simple block structure

- **`model="dc_sbm"`**: Degree-Corrected SBM
  - Accounts for node degree heterogeneity
  - Better for real-world networks

### Layer Coupling Modes

- **`layer_mode="independent"`**: Separate blocks and affinities per layer
- **`layer_mode="shared_blocks"`**: Shared memberships, separate affinities
- **`layer_mode="shared_affinity"`**: Shared memberships and affinities (strong regularization)

### Parameters

- `n_blocks`: Number of blocks (int) or list for model selection
- `init`: Initialization ("spectral", "kmeans", "random")
- `n_init`: Number of random restarts (default: 5)
- `max_iter`: Maximum VI iterations (default: 500)
- `tol`: Convergence tolerance (default: 1e-5)
- `seed`: Random seed for reproducibility

### SBMFittedModel Attributes

- `memberships_`: Soft membership matrix (n_nodes × K)
- `hard_membership_`: Hard block assignments (n_nodes,)
- `block_affinity_`: Block affinity matrices per layer
- `degree_params_`: Node propensities (DC-SBM only)
- `elbo_history_`: ELBO values over iterations
- `converged_`: Whether inference converged
- `uncertainty_`: Node-level uncertainty metrics

### SBMFittedModel Methods

- `predict_proba(u, v, layer)`: Predict edge probability
- `score_edges(edges)`: Batch edge scoring
- `to_partition_vector()`: Get community labels dict
- `get_summary()`: Model summary statistics

## Requirements

- Node-aligned multiplex networks (all layers must have the same nodes)
- Sparse adjacency representation (CSR/CSC/COO)
- Python 3.8+

## Examples

See `examples/sbm_tutorial.py` for comprehensive examples including:
1. Basic SBM fitting
2. Model selection across K
3. Link prediction
4. Uncertainty quantification
5. Layer coupling mode comparison

## References

- Abbe, E. (2017). Community detection and stochastic block models: recent developments. JMLR.
- Karrer, B., & Newman, M. E. (2011). Stochastic blockmodels and community structure in networks. Physical Review E.
- Peixoto, T. P. (2014). Hierarchical block structures and high-resolution model selection in large networks. Physical Review X.

## Testing

Run tests with:
```bash
pytest tests/algorithms/sbm/
```

All 17 tests should pass.
