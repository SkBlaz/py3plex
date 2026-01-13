# Dynamics Examples

This directory contains examples demonstrating the OOP-style dynamics API in py3plex, as described in the *Practical Multilayer Network Analysis with Py3plex* book. Plots are written to an `outputs/` subdirectory next to each script; matplotlib uses the non-interactive Agg backend if available.

**Prerequisites:** py3plex installed with dynamics extras, plus networkx and numpy. Matplotlib is optional for saving figures; if missing, the examples still run but skip plotting.

## Overview

The py3plex dynamics module provides clean OOP abstractions for implementing and running dynamical processes on multilayer networks, including:

- **Epidemic models**: SIS, SIR, SEIR with compartmental dynamics
- **Diffusion processes**: Random walks on single and multilayer networks
- **Continuous-time models**: Gillespie algorithm implementations

## Quick Start

```python
from py3plex.dynamics import SIRDynamics
import networkx as nx

# Create a network
G = nx.karate_club_graph()

# Create SIR dynamics
sir = SIRDynamics(G, beta=0.3, gamma=0.1, initial_infected=0.1)

# Set seed for reproducibility
sir.set_seed(42)

# Run simulation
results = sir.run(steps=100)

# Extract measures
prevalence = results.get_measure("prevalence")
state_counts = results.get_measure("state_counts")
```

## Examples

### 1. `sir_epidemic.py`

Demonstrates the classic SIR (Susceptible-Infected-Recovered) epidemic model:

- Creating multilayer networks
- Running SIR dynamics with specified parameters
- Extracting and visualizing epidemic curves
- Comparing different parameter settings

**Run:**
```bash
python examples/dynamics/sir_epidemic.py
```

**Key Features:**
- Multilayer network support
- Peak prevalence and attack rate calculation
- Multiple parameter comparison
- Publication-quality plots

### 2. `sis_dynamics.py`

Shows SIS (Susceptible-Infected-Susceptible) dynamics where nodes can be reinfected:

- Endemic equilibrium behavior
- Comparison with SIR dynamics
- Epidemic threshold analysis (R₀)
- Small-world network structure

**Run:**
```bash
python examples/dynamics/sis_dynamics.py
```

**Key Features:**
- Endemic state detection
- SIS vs SIR comparison
- Threshold analysis with varying transmission rates
- Steady-state prevalence estimation

### 3. `random_walk.py`

Demonstrates random walk dynamics on multilayer networks:

- Single-walker random walks
- Multilayer exploration patterns
- Visit distribution analysis
- Lazy walk behavior
- Hitting time estimation

**Run:**
```bash
python examples/dynamics/random_walk.py
```

**Key Features:**
- Layer switching analysis
- Visit count distribution
- Lazy probability effects
- Hitting time statistics

## Common Patterns

### Setting Parameters

All dynamics classes accept parameters as keyword arguments:

```python
sir = SIRDynamics(
    network,
    beta=0.3,          # Infection rate
    gamma=0.1,         # Recovery rate
    initial_infected=0.05  # 5% initially infected
)
```

### Reproducible Simulations

Use `set_seed()` for reproducibility:

```python
dynamics.set_seed(42)
results = dynamics.run(steps=100)
```

### Extracting Measures

The `DynamicsResult` object provides measures through `get_measure()`:

```python
# Get prevalence time series
prevalence = results.get_measure("prevalence")

# Get state counts
state_counts = results.get_measure("state_counts")
# Returns: {'S': array(...), 'I': array(...), 'R': array(...)}

# Get raw trajectory
trajectory = results.get_measure("trajectory")
```

### Converting to DataFrame

For analysis in pandas:

```python
df = results.to_pandas()
# Returns DataFrame with columns: [t, node, state]
```

## Multilayer Networks

All examples support multilayer networks created with py3plex:

```python
from py3plex.core import multinet

network = multinet.multi_layer_network(directed=False)

# Add nodes to multiple layers
network.add_nodes([
    {'source': 0, 'type': 'physical'},
    {'source': 0, 'type': 'digital'},
    # ...
])

# Add edges within and between layers
network.add_edges([...])

# Run dynamics
sir = SIRDynamics(network, beta=0.3, gamma=0.1)
```

## Available Models

### Compartmental Models

- **SISDynamics**: Susceptible-Infected-Susceptible
- **SIRDynamics**: Susceptible-Infected-Recovered
- **SEIRDynamics**: Susceptible-Exposed-Infected-Recovered

### Random Walk Models

- **RandomWalkDynamics**: Single walker on network
- **MultiRandomWalkDynamics**: Multiple independent walkers
- **TemporalRandomWalk**: Walk on time-varying networks

### Continuous-Time Models

- **SISContinuousTime**: SIS with Gillespie algorithm

## Testing

The dynamics module includes comprehensive tests:

```bash
# Run all dynamics tests
pytest tests/test_dynamics*.py

# Run conservation law tests
pytest tests/test_dynamics_conservation.py

# Run core dynamics tests  
pytest tests/test_dynamics_core.py
```

## Documentation

For more details, see:

- `docfiles/sir_epidemic_simulator.rst`: SIR simulator documentation
- `DYNAMICS_IMPLEMENTATION.md`: Implementation details
- Book chapters 7 & 13: Dynamics on multilayer networks

## Citation

If you use these dynamics implementations in your research, please cite:

```bibtex
@software{py3plex,
  author = {Škrlj, Blaž},
  title = {Py3plex: A library for analysis and visualization of heterogeneous networks},
  url = {https://github.com/SkBlaz/py3plex},
  year = {2023}
}
```
