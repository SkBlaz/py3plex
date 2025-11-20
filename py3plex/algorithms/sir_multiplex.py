"""
SIR Epidemic Simulator on Multiplex Graphs

This module implements efficient, reproducible SIR (Susceptible-Infected-Recovered)
epidemic simulators on multiplex graphs with the same node set but multiple edge layers.

Supports:
- Discrete-time and continuous-time (Gillespie) dynamics
- Per-layer transmission rates
- Optional exogenous importations
- Rich outputs: incidence curves, event logs, per-layer attributions
- Sparse linear algebra for scalability

Model:
- Nodes have a single health state shared across layers: S=0, I=1, R=2
- Intra-layer transmission: along layer-specific edges with rate/probability β[α]
- Recovery: infected nodes recover at rate γ
- Hazard aggregation: exposures from all layers combine additively (continuous-time)
  or via independent-trial complement (discrete-time)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any
import warnings

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None
    warnings.warn("numpy not available, SIR epidemic simulator will not work", stacklevel=2)

try:
    import scipy.sparse
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    scipy = None
    warnings.warn("scipy not available, SIR epidemic simulator will not work", stacklevel=2)


@dataclass
class EpidemicResult:
    """
    Result of an epidemic simulation.

    Attributes:
        times: Array of shape (T,) with step times (discrete) or event times (Gillespie)
        S: Array of shape (T,) with susceptible counts over time
        I: Array of shape (T,) with infected counts over time
        R: Array of shape (T,) with recovered counts over time
        states: Optional array of shape (T, N) for discrete simulations; None for Gillespie
        incidence_by_layer: Optional array of shape (T, L) if requested, showing infections per layer
        events: Optional list of tuples (t, event_type, node_id, layer_or_None) if requested
        meta: Dictionary with simulation metadata (parameters, N, L, dt/t_max, rng_seed)
    """
    times: Any  # np.ndarray when available
    S: Any  # np.ndarray when available
    I: Any  # np.ndarray when available
    R: Any  # np.ndarray when available
    states: Optional[Any] = None  # np.ndarray when available
    incidence_by_layer: Optional[Any] = None  # np.ndarray when available
    events: Optional[list] = None
    meta: dict = None


def simulate_sir_multiplex_discrete(
    A_layers: list,  # scipy.sparse.csr_matrix when available
    beta,  # np.ndarray | float when available
    gamma,  # np.ndarray | float when available
    *,
    layer_weights: Optional = None,  # np.ndarray when available
    dt: float = 1.0,
    steps: int = 100,
    initial_state: Optional = None,  # np.ndarray when available
    initial_infected: Optional = None,  # np.ndarray when available
    import_rate = 0.0,  # float | Callable[[int], float]
    rng_seed: int = 0,
    return_event_log: bool = False,
    return_layer_incidence: bool = False
) -> EpidemicResult:
    """
    Discrete-time SIR epidemic simulation on multiplex graphs.

    Update rule per step t → t+dt:
    - For each susceptible i, compute per-layer exposure:
      λ_{i,α}(t) = β_α(t) * w_α * Σ_j A^{(α)}_{j i} * 1{X_j(t)=I}
    - Infection probability: p_i(t) = 1 - Π_α exp(-λ_{i,α}(t) * dt)
    - Recovery probability per infected i: 1 - exp(-γ_i(t) * dt)
    - Apply synchronous updates

    Parameters:
        A_layers: List of L sparse adjacency matrices (N×N), representing different layers
        beta: Transmission rate(s). Scalar or array of length L for per-layer rates
        gamma: Recovery rate(s). Scalar or array of length N for per-node rates
        layer_weights: Optional array of length L for layer weights (default: ones)
        dt: Time step size
        steps: Number of simulation steps
        initial_state: Optional array of length N with values {0,1,2} for S/I/R states
        initial_infected: Optional boolean mask of length N for initially infected nodes
        import_rate: Exogenous infection rate. Scalar or callable f(step) -> rate
        rng_seed: Random seed for reproducibility
        return_event_log: If True, return list of infection/recovery events
        return_layer_incidence: If True, return per-layer infection counts over time

    Returns:
        EpidemicResult with simulation trajectories and optional detailed outputs

    Raises:
        ValueError: If input dimensions are inconsistent or values are invalid
        ImportError: If numpy or scipy are not available
    """
    # Check dependencies
    if not NUMPY_AVAILABLE or not SCIPY_AVAILABLE:
        raise ImportError(
            "SIR epidemic simulator requires numpy and scipy. "
            "Please install them: pip install numpy scipy"
        )

    # Validate inputs
    if not A_layers:
        raise ValueError("A_layers must contain at least one adjacency matrix")

    N = A_layers[0].shape[0]
    L = len(A_layers)

    # Check all layers have same shape
    for i, A in enumerate(A_layers):
        if A.shape != (N, N):
            raise ValueError(f"Layer {i} has shape {A.shape}, expected ({N}, {N})")
        if not scipy.sparse.issparse(A):
            raise ValueError(f"Layer {i} is not a sparse matrix")

    # Initialize random number generator
    rng = np.random.default_rng(rng_seed)

    # Initialize states
    X = _init_states(N, initial_state, initial_infected, rng)

    # Process layer weights
    if layer_weights is None:
        w = np.ones(L, dtype=float)
    else:
        w = np.asarray(layer_weights, dtype=float)
        if w.shape != (L,):
            raise ValueError(f"layer_weights must have length {L}, got {w.shape}")
        if np.any(w < 0):
            raise ValueError("layer_weights must be non-negative")

    # Process beta
    if np.isscalar(beta):
        beta_arr = np.full(L, float(beta), dtype=float)
    else:
        beta_arr = np.asarray(beta, dtype=float)
        if beta_arr.shape != (L,):
            raise ValueError(f"beta must be scalar or have length {L}, got {beta_arr.shape}")
    if np.any(beta_arr < 0):
        raise ValueError("beta must be non-negative")

    # Process gamma
    if np.isscalar(gamma):
        gamma_arr = np.full(N, float(gamma), dtype=float)
    else:
        gamma_arr = np.asarray(gamma, dtype=float)
        if gamma_arr.shape != (N,):
            raise ValueError(f"gamma must be scalar or have length {N}, got {gamma_arr.shape}")
    if np.any(gamma_arr < 0):
        raise ValueError("gamma must be non-negative")

    # Storage
    times = np.arange(0, (steps + 1) * dt, dt)
    S_hist = []
    I_hist = []
    R_hist = []
    layer_inc = [] if return_layer_incidence else None
    events = [] if return_event_log else None

    # Record initial state
    S_hist.append(np.sum(X == 0))
    I_hist.append(np.sum(X == 1))
    R_hist.append(np.sum(X == 2))

    # Simulation loop
    for k in range(steps):
        # Current infected nodes as float array for matrix multiplication
        infected = (X == 1).astype(float)

        # Compute per-layer force of infection
        # λ_{i,α} = β_α * w_α * Σ_j A^{(α)}_{j i} * I_j
        # Note: A.T @ infected gives incoming edges (j->i transmission)
        lambdas = []
        for alpha in range(L):
            lam_alpha = beta_arr[alpha] * w[alpha] * (A_layers[alpha].T @ infected)
            lambdas.append(lam_alpha)

        # Stack lambdas for easier manipulation
        lambdas_arr = np.vstack(lambdas)  # shape (L, N)

        # Total force of infection per node (sum across layers)
        Lambda = np.sum(lambdas_arr, axis=0)  # shape (N,)

        # Infection probability: 1 - exp(-Λ * dt)
        # Use -expm1(-x) = 1 - exp(-x) for numerical stability
        p_inf = -np.expm1(-Lambda * dt)
        p_inf = np.clip(p_inf, 0.0, 1.0)

        # Block infections to susceptibles only
        p_draw = p_inf * (X == 0)
        new_inf = rng.random(N) < p_draw

        # Optional importations
        if import_rate != 0:
            rate = import_rate(k) if callable(import_rate) else float(import_rate)
            if rate > 0:
                imp_prob = -np.expm1(-rate * dt)
                imp_prob = np.clip(imp_prob, 0.0, 1.0)
                import_mask = (rng.random(N) < imp_prob) & (X == 0)
                new_inf |= import_mask

        # Recoveries
        # p_rec = 1 - exp(-γ * dt) for infected nodes
        p_rec = -np.expm1(-gamma_arr * dt)
        p_rec = np.clip(p_rec, 0.0, 1.0)
        p_rec_masked = p_rec * (X == 1)
        new_rec = rng.random(N) < p_rec_masked

        # Synchronous update: first mark new infections, then recoveries
        X_new = X.copy()
        X_new[new_inf] = 1
        X_new[new_rec] = 2
        X = X_new

        # Bookkeeping
        S_hist.append(np.sum(X == 0))
        I_hist.append(np.sum(X == 1))
        R_hist.append(np.sum(X == 2))

        # Per-layer incidence attribution
        if layer_inc is not None:
            # Attribute new infections to layers via fractional hazards
            eps = 1e-12
            # contrib[alpha, i] = λ_{i,α} / (Λ_i + eps)
            contrib = lambdas_arr / (Lambda + eps)
            # Sum contributions weighted by new infections
            layer_contributions = (contrib * new_inf).sum(axis=1)
            layer_inc.append(layer_contributions)

        # Event log
        if events is not None:
            t_next = times[k + 1]
            for i in np.where(new_inf)[0]:
                events.append((t_next, "infection", int(i), None))
            for i in np.where(new_rec)[0]:
                events.append((t_next, "recovery", int(i), None))

    # Prepare results
    meta = {
        "N": N,
        "L": L,
        "dt": dt,
        "steps": steps,
        "rng_seed": rng_seed,
        "beta": beta_arr.tolist() if L > 1 else float(beta_arr[0]),
        "gamma": gamma_arr.tolist() if np.any(gamma_arr != gamma_arr[0]) else float(gamma_arr[0]),
        "layer_weights": w.tolist() if L > 1 else None,
        "import_rate": import_rate if callable(import_rate) else float(import_rate)
    }

    result = EpidemicResult(
        times=times,
        S=np.array(S_hist),
        I=np.array(I_hist),
        R=np.array(R_hist),
        states=None,  # Could store full state history if needed
        incidence_by_layer=np.vstack(layer_inc) if layer_inc is not None else None,
        events=events,
        meta=meta
    )

    return result


def simulate_sir_multiplex_gillespie(
    A_layers: list,  # scipy.sparse.csr_matrix when available
    beta,  # np.ndarray | float when available
    gamma,  # np.ndarray | float when available
    *,
    layer_weights: Optional = None,  # np.ndarray when available
    t_max: float = 100.0,
    initial_state: Optional = None,  # np.ndarray when available
    initial_infected: Optional = None,  # np.ndarray when available
    import_rate = 0.0,  # float | Callable[[float], float]
    rng_seed: int = 0,
    return_event_log: bool = True,
    return_layer_incidence: bool = False
) -> EpidemicResult:
    """
    Continuous-time SIR epidemic simulation using Gillespie algorithm on multiplex graphs.

    The Gillespie algorithm simulates exact continuous-time dynamics:
    1. Compute total event rate Λ = Σ_i∈S Σ_α λ_{i,α} + Σ_i∈I γ_i + η|S|
    2. Sample time to next event: Δt ~ Exp(Λ)
    3. Select event type proportionally to rates
    4. Update state and affected rates incrementally
    5. Repeat until t > t_max or no infected nodes remain

    Parameters:
        A_layers: List of L sparse adjacency matrices (N×N)
        beta: Transmission rate(s). Scalar or array of length L
        gamma: Recovery rate(s). Scalar or array of length N
        layer_weights: Optional array of length L for layer weights
        t_max: Maximum simulation time
        initial_state: Optional array of length N with S/I/R states
        initial_infected: Optional boolean mask for initially infected nodes
        import_rate: Exogenous infection rate. Scalar or callable f(t) -> rate
        rng_seed: Random seed for reproducibility
        return_event_log: If True, return detailed event log
        return_layer_incidence: If True, track infections per layer

    Returns:
        EpidemicResult with event-driven trajectories

    Raises:
        ImportError: If numpy or scipy are not available
    """
    # Check dependencies
    if not NUMPY_AVAILABLE or not SCIPY_AVAILABLE:
        raise ImportError(
            "SIR epidemic simulator requires numpy and scipy. "
            "Please install them: pip install numpy scipy"
        )

    # Validate inputs
    if not A_layers:
        raise ValueError("A_layers must contain at least one adjacency matrix")

    N = A_layers[0].shape[0]
    L = len(A_layers)

    # Check all layers have same shape
    for i, A in enumerate(A_layers):
        if A.shape != (N, N):
            raise ValueError(f"Layer {i} has shape {A.shape}, expected ({N}, {N})")
        if not scipy.sparse.issparse(A):
            raise ValueError(f"Layer {i} is not a sparse matrix")

    # Initialize random number generator
    rng = np.random.default_rng(rng_seed)

    # Initialize states
    X = _init_states(N, initial_state, initial_infected, rng)

    # Process layer weights
    if layer_weights is None:
        w = np.ones(L, dtype=float)
    else:
        w = np.asarray(layer_weights, dtype=float)
        if w.shape != (L,):
            raise ValueError(f"layer_weights must have length {L}, got {w.shape}")
        if np.any(w < 0):
            raise ValueError("layer_weights must be non-negative")

    # Process beta
    if np.isscalar(beta):
        beta_arr = np.full(L, float(beta), dtype=float)
    else:
        beta_arr = np.asarray(beta, dtype=float)
        if beta_arr.shape != (L,):
            raise ValueError(f"beta must be scalar or have length {L}, got {beta_arr.shape}")
    if np.any(beta_arr < 0):
        raise ValueError("beta must be non-negative")

    # Process gamma
    if np.isscalar(gamma):
        gamma_arr = np.full(N, float(gamma), dtype=float)
    else:
        gamma_arr = np.asarray(gamma, dtype=float)
        if gamma_arr.shape != (N,):
            raise ValueError(f"gamma must be scalar or have length {N}, got {gamma_arr.shape}")
    if np.any(gamma_arr < 0):
        raise ValueError("gamma must be non-negative")

    # Precompute neighbor lists for efficient incremental updates
    # neighbors[alpha][i] = list of nodes j with edge j->i in layer alpha
    neighbors = []
    for alpha in range(L):
        A_csc = A_layers[alpha].tocsc()  # Column-sparse for efficient column access
        layer_neighbors = []
        for i in range(N):
            # Get indices of non-zero entries in column i (incoming edges)
            col_indices = A_csc.indices[A_csc.indptr[i]:A_csc.indptr[i+1]]
            col_data = A_csc.data[A_csc.indptr[i]:A_csc.indptr[i+1]]
            layer_neighbors.append(list(zip(col_indices, col_data)))
        neighbors.append(layer_neighbors)

    # Storage
    times = [0.0]
    S_hist = [np.sum(X == 0)]
    I_hist = [np.sum(X == 1)]
    R_hist = [np.sum(X == 2)]
    events = [] if return_event_log else None
    layer_inc = dict.fromkeys(range(L), 0) if return_layer_incidence else None
    layer_inc_hist = [] if return_layer_incidence else None

    # Initialize infection rates per node
    # λ_i = Σ_α β_α w_α Σ_{j∈I} A^{(α)}_{j i}
    lambda_i = np.zeros(N, dtype=float)
    for i in range(N):
        if X[i] == 0:  # Susceptible
            for alpha in range(L):
                for j, weight in neighbors[alpha][i]:
                    if X[j] == 1:  # Infected neighbor
                        lambda_i[i] += beta_arr[alpha] * w[alpha] * weight

    t = 0.0

    # Check if import rate is active (for loop continuation)
    has_import = callable(import_rate) or float(import_rate) > 0

    # Main Gillespie loop
    # Continue while time permits and either infections exist or imports are possible
    while t < t_max:
        # Compute total rates
        susceptible = (X == 0)
        infected = (X == 1)

        # Infection rate: sum of λ_i over susceptibles
        infection_rate_total = np.sum(lambda_i[susceptible])

        # Recovery rate: sum of γ_i over infected
        recovery_rate_total = np.sum(gamma_arr[infected])

        # Import rate
        n_susceptible = np.sum(susceptible)
        import_rate_val = import_rate(t) if callable(import_rate) else float(import_rate)
        import_rate_total = import_rate_val * n_susceptible

        # Total rate
        total_rate = infection_rate_total + recovery_rate_total + import_rate_total

        # Stop if no events are possible
        if total_rate <= 0:
            # No infected and no imports possible
            if I_hist[-1] == 0 and not has_import:
                break
            # Or nothing can happen anymore
            if n_susceptible == 0 and I_hist[-1] == 0:
                break
            break

        # Sample time to next event
        dt = rng.exponential(1.0 / total_rate)
        t += dt

        if t > t_max:
            break

        # Select event type
        r = rng.random() * total_rate

        if r < infection_rate_total:
            # Infection event
            # Select susceptible node i proportional to λ_i
            susceptible_nodes = np.where(susceptible)[0]
            lambda_susceptible = lambda_i[susceptible_nodes]

            if lambda_susceptible.sum() == 0:
                continue

            probs = lambda_susceptible / lambda_susceptible.sum()
            i = rng.choice(susceptible_nodes, p=probs)

            # Determine which layer caused the infection (for attribution)
            layer_probs = np.zeros(L)
            for alpha in range(L):
                for j, weight in neighbors[alpha][i]:
                    if X[j] == 1:
                        layer_probs[alpha] += beta_arr[alpha] * w[alpha] * weight

            if layer_probs.sum() > 0:
                layer_probs /= layer_probs.sum()
                source_layer = rng.choice(L, p=layer_probs)
            else:
                source_layer = None

            # Update state
            X[i] = 1

            # Update infection rates for neighbors of i
            for alpha in range(L):
                # i is now infected, so it can infect its outgoing neighbors
                # Find all j where i->j exists
                A_csr = A_layers[alpha].tocsr()
                out_indices = A_csr.indices[A_csr.indptr[i]:A_csr.indptr[i+1]]
                out_data = A_csr.data[A_csr.indptr[i]:A_csr.indptr[i+1]]

                for j, weight in zip(out_indices, out_data):
                    if X[j] == 0:  # j is susceptible
                        lambda_i[j] += beta_arr[alpha] * w[alpha] * weight

            # i is no longer susceptible, so clear its rate
            lambda_i[i] = 0

            # Record event
            if events is not None:
                events.append((t, "infection", int(i), source_layer))
            if layer_inc is not None and source_layer is not None:
                layer_inc[source_layer] += 1

        elif r < infection_rate_total + recovery_rate_total:
            # Recovery event
            # Select infected node i proportional to γ_i
            infected_nodes = np.where(infected)[0]
            gamma_infected = gamma_arr[infected_nodes]

            if gamma_infected.sum() == 0:
                continue

            probs = gamma_infected / gamma_infected.sum()
            i = rng.choice(infected_nodes, p=probs)

            # Update state
            X[i] = 2

            # Update infection rates for neighbors of i
            for alpha in range(L):
                # i is no longer infected, so reduce rates of its outgoing neighbors
                A_csr = A_layers[alpha].tocsr()
                out_indices = A_csr.indices[A_csr.indptr[i]:A_csr.indptr[i+1]]
                out_data = A_csr.data[A_csr.indptr[i]:A_csr.indptr[i+1]]

                for j, weight in zip(out_indices, out_data):
                    if X[j] == 0:  # j is susceptible
                        lambda_i[j] -= beta_arr[alpha] * w[alpha] * weight
                        lambda_i[j] = max(0, lambda_i[j])  # Numerical safety

            # Record event
            if events is not None:
                events.append((t, "recovery", int(i), None))

        else:
            # Import event
            # Select random susceptible node
            susceptible_nodes = np.where(susceptible)[0]
            if len(susceptible_nodes) == 0:
                continue

            i = rng.choice(susceptible_nodes)

            # Update state
            X[i] = 1

            # Update infection rates for neighbors of i
            for alpha in range(L):
                A_csr = A_layers[alpha].tocsr()
                out_indices = A_csr.indices[A_csr.indptr[i]:A_csr.indptr[i+1]]
                out_data = A_csr.data[A_csr.indptr[i]:A_csr.indptr[i+1]]

                for j, weight in zip(out_indices, out_data):
                    if X[j] == 0:
                        lambda_i[j] += beta_arr[alpha] * w[alpha] * weight

            lambda_i[i] = 0

            # Record event
            if events is not None:
                events.append((t, "import", int(i), None))
            if layer_inc is not None:
                # Imports not attributed to any layer
                pass

        # Record state
        times.append(t)
        S_hist.append(np.sum(X == 0))
        I_hist.append(np.sum(X == 1))
        R_hist.append(np.sum(X == 2))
        if layer_inc_hist is not None:
            layer_inc_hist.append([layer_inc[alpha] for alpha in range(L)])

    # Prepare results
    meta = {
        "N": N,
        "L": L,
        "t_max": t_max,
        "final_time": times[-1],
        "rng_seed": rng_seed,
        "beta": beta_arr.tolist() if L > 1 else float(beta_arr[0]),
        "gamma": gamma_arr.tolist() if np.any(gamma_arr != gamma_arr[0]) else float(gamma_arr[0]),
        "layer_weights": w.tolist() if L > 1 else None,
        "import_rate": import_rate if callable(import_rate) else float(import_rate)
    }

    result = EpidemicResult(
        times=np.array(times),
        S=np.array(S_hist),
        I=np.array(I_hist),
        R=np.array(R_hist),
        states=None,
        incidence_by_layer=np.array(layer_inc_hist) if layer_inc_hist is not None else None,
        events=events,
        meta=meta
    )

    return result


def basic_reproduction_number(
    A_layers: list,  # scipy.sparse.csr_matrix when available
    beta,  # np.ndarray | float when available
    gamma: float,
    layer_weights: Optional = None  # np.ndarray when available
) -> float:
    """
    Compute basic reproduction number R0 as a proxy using spectral radius.

    For uniform recovery rate γ, R0 ≈ ρ(Σ_α (β_α w_α / γ) A^{(α)})
    where ρ is the spectral radius (largest eigenvalue magnitude).

    This is a simplified approximation that works well for homogeneous networks.

    Parameters:
        A_layers: List of sparse adjacency matrices
        beta: Transmission rate(s). Scalar or array of length L
        gamma: Recovery rate (scalar)
        layer_weights: Optional layer weights

    Returns:
        Approximate R0 value

    Raises:
        ImportError: If numpy or scipy are not available
    """
    # Check dependencies
    if not NUMPY_AVAILABLE or not SCIPY_AVAILABLE:
        raise ImportError(
            "SIR epidemic simulator requires numpy and scipy. "
            "Please install them: pip install numpy scipy"
        )

    L = len(A_layers)
    N = A_layers[0].shape[0]

    # Process inputs
    if np.isscalar(beta):
        beta_arr = np.full(L, float(beta))
    else:
        beta_arr = np.asarray(beta, dtype=float)

    if layer_weights is None:
        w = np.ones(L)
    else:
        w = np.asarray(layer_weights, dtype=float)

    # Compute weighted sum of adjacency matrices
    # M = Σ_α (β_α w_α / γ) A^{(α)}
    M = scipy.sparse.csr_matrix((N, N), dtype=float)
    for alpha in range(L):
        M = M + (beta_arr[alpha] * w[alpha] / gamma) * A_layers[alpha]

    # Compute spectral radius using power iteration (faster for sparse matrices)
    try:
        from scipy.sparse.linalg import eigs
        # Compute largest eigenvalue by magnitude
        eigenvalues = eigs(M, k=1, which='LM', return_eigenvectors=False)
        R0 = np.abs(eigenvalues[0])
    except Exception:
        # Fallback to dense computation for small matrices
        if N <= 1000:
            M_dense = M.toarray()
            eigenvalues = np.linalg.eigvals(M_dense)
            R0 = np.max(np.abs(eigenvalues))
        else:
            # If both fail, return NaN
            R0 = np.nan

    return float(R0)


def summarize(result: EpidemicResult) -> dict:
    """
    Compute summary statistics from an epidemic simulation result.

    Parameters:
        result: EpidemicResult from a simulation

    Returns:
        Dictionary with summary statistics including:
        - peak_prevalence: Maximum number of infected individuals
        - peak_time: Time at which peak occurred
        - attack_rate: Final proportion of recovered individuals
        - time_to_extinction: Time when infections reached zero
        - total_infections: Total number of infections
        - layer_contributions: If available, proportion of infections per layer
    """
    summary = {}

    # Peak prevalence
    peak_idx = np.argmax(result.I)
    summary["peak_prevalence"] = int(result.I[peak_idx])
    summary["peak_time"] = float(result.times[peak_idx])

    # Attack rate
    N = result.meta["N"]
    summary["attack_rate"] = float(result.R[-1]) / N

    # Time to extinction
    if np.any(result.I == 0):
        extinction_idx = np.where(result.I == 0)[0][0]
        summary["time_to_extinction"] = float(result.times[extinction_idx])
    else:
        summary["time_to_extinction"] = None

    # Total infections
    summary["total_infections"] = int(result.R[-1])

    # Layer contributions (if available)
    if result.incidence_by_layer is not None:
        total_by_layer = result.incidence_by_layer.sum(axis=0)
        total = total_by_layer.sum()
        if total > 0:
            summary["layer_contributions"] = (total_by_layer / total).tolist()
        else:
            summary["layer_contributions"] = [0.0] * len(total_by_layer)

    # Duration
    summary["duration"] = float(result.times[-1] - result.times[0])

    return summary


def _init_states(
    N: int,
    initial_state: Optional[np.ndarray],
    initial_infected: Optional[np.ndarray],
    rng: np.random.Generator
) -> np.ndarray:
    """
    Initialize node states for simulation.

    Priority:
    1. If initial_state provided, use it
    2. If initial_infected provided, use it (rest are susceptible)
    3. Otherwise, randomly select one infected node

    Parameters:
        N: Number of nodes
        initial_state: Optional state array
        initial_infected: Optional infected mask
        rng: Random number generator

    Returns:
        State array of length N with values {0, 1, 2}
    """
    if initial_state is not None:
        X = np.asarray(initial_state, dtype=int)
        if X.shape != (N,):
            raise ValueError(f"initial_state must have length {N}, got {X.shape}")
        if not np.all(np.isin(X, [0, 1, 2])):
            raise ValueError("initial_state must contain only values {0, 1, 2}")
        return X

    if initial_infected is not None:
        initial_infected = np.asarray(initial_infected, dtype=bool)
        if initial_infected.shape != (N,):
            raise ValueError(f"initial_infected must have length {N}, got {initial_infected.shape}")
        X = np.zeros(N, dtype=int)
        X[initial_infected] = 1
        if not np.any(X == 1):
            raise ValueError("initial_infected must have at least one True value")
        return X

    # Default: random single infected node
    X = np.zeros(N, dtype=int)
    infected_idx = rng.integers(0, N)
    X[infected_idx] = 1
    return X
