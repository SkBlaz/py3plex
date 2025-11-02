"""
Comprehensive tests for RNG seeding and determinism.

This test suite guarantees that algorithms with randomness are reproducible
when the same seed is used, and that results vary (within reason) across
different seeds. Also verifies determinism across processes/threads when
a seed is fixed.

The tests cover multiple randomized entry points from py3plex:
- Random walks (basic_random_walk, node2vec_walk, generate_walks)
- Random network generators (random_multilayer_ER, random_multiplex_ER, random_multiplex_generator)
"""

import hashlib
import multiprocessing as mp
import os
import random
from contextlib import contextmanager
from typing import Any

import networkx as nx
import numpy as np
import pytest

# Import py3plex randomized functions
from py3plex.algorithms.general.walkers import (
    basic_random_walk,
    generate_walks,
    node2vec_walk,
)
from py3plex.core.random_generators import (
    random_multilayer_ER,
    random_multiplex_ER,
    random_multiplex_generator,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
SEEDS = [0, 1, 42, 1337]
FLOAT_TOL = 1e-12


# ─────────────────────────────────────────────────────────────────────────────
# Context Manager for Fixed Seed
# ─────────────────────────────────────────────────────────────────────────────
@contextmanager
def fixed_seed(seed: int):
    """
    Freeze Python and NumPy RNGs; restore afterward.
    
    This ensures that randomized code produces deterministic results
    within this context without permanently affecting global state.
    """
    py_state = random.getstate()
    np_state = np.random.get_state()
    try:
        random.seed(seed)
        np.random.seed(seed)
        yield
    finally:
        random.setstate(py_state)
        np.random.set_state(np_state)


# ─────────────────────────────────────────────────────────────────────────────
# Signature Function for Output Canonicalization
# ─────────────────────────────────────────────────────────────────────────────
def _sha256_bytes(b: bytes) -> str:
    """Helper to compute SHA256 hash of bytes."""
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def signature(obj: Any) -> tuple:
    """
    Produce a stable signature for equality checks across runs and processes.
    
    This handles various data types:
    - numpy arrays: (shape, dtype, hash of bytes)
    - pandas DataFrames: (columns, index, hash of values)
    - NetworkX/py3plex graphs: (sorted nodes with attrs, sorted edges with attrs)
    - lists/tuples: recursive signatures
    - dicts: sorted (key, signature) pairs
    - fallback: repr()
    """
    # NumPy arrays
    if isinstance(obj, np.ndarray):
        return ("ndarray", obj.shape, obj.dtype.str, _sha256_bytes(obj.tobytes()))

    # pandas DataFrame (optional)
    try:
        import pandas as pd
        if isinstance(obj, pd.DataFrame):
            values = obj.to_numpy(copy=False)
            return (
                "dataframe",
                tuple(obj.columns),
                tuple(obj.index),
                _sha256_bytes(values.tobytes()),
            )
    except Exception:
        pass

    # py3plex multi_layer_network objects - extract core_network first
    if hasattr(obj, "core_network"):
        obj = obj.core_network
    
    # NetworkX graphs
    try:
        if hasattr(obj, "nodes") and hasattr(obj, "edges"):
            nodes = tuple(
                sorted(
                    (n, tuple(sorted((k, repr(v)) for k, v in d.items())))
                    for n, d in obj.nodes(data=True)
                )
            )
            edges = tuple(
                sorted(
                    (u, v, tuple(sorted((k, repr(v)) for k, v in d.items())))
                    for u, v, d in obj.edges(data=True)
                )
            )
            return ("graph", nodes, edges)
    except Exception:
        pass

    # Containers
    if isinstance(obj, (list, tuple)):
        return (type(obj).__name__, tuple(signature(x) for x in obj))
    if isinstance(obj, dict):
        return ("dict", tuple(sorted((k, signature(v)) for k, v in obj.items())))

    # Fallback
    return ("repr", repr(obj))


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions for Randomized Calls
# ─────────────────────────────────────────────────────────────────────────────
def _get_test_graph():
    """Create a small test graph for walks."""
    G = nx.karate_club_graph()
    return G


def get_randomized_output_basic_walk(seed: int) -> list:
    """Call basic_random_walk with seed."""
    G = _get_test_graph()
    return basic_random_walk(G, 0, walk_length=20, seed=seed)


def get_randomized_output_node2vec_walk(seed: int) -> list:
    """Call node2vec_walk with seed."""
    G = _get_test_graph()
    return node2vec_walk(G, 0, walk_length=20, p=0.5, q=2.0, seed=seed)


def get_randomized_output_generate_walks(seed: int) -> list:
    """Call generate_walks with seed."""
    G = _get_test_graph()
    # Use a subset of nodes to keep it fast
    return generate_walks(
        G, num_walks=3, walk_length=10, start_nodes=[0, 1, 2], seed=seed
    )


def get_randomized_output_multilayer_er(seed: int):
    """Call random_multilayer_ER with controlled seed."""
    # Use fixed_seed since this function doesn't accept seed parameter
    with fixed_seed(seed):
        return random_multilayer_ER(n=5, l=2, p=0.5, directed=False)


def get_randomized_output_multiplex_er(seed: int):
    """Call random_multiplex_ER with controlled seed."""
    with fixed_seed(seed):
        return random_multiplex_ER(n=5, l=2, p=0.5, directed=False)


def get_randomized_output_multiplex_generator(seed: int):
    """Call random_multiplex_generator with controlled seed."""
    with fixed_seed(seed):
        return random_multiplex_generator(n=5, m=2, d=0.5)


# ─────────────────────────────────────────────────────────────────────────────
# Test: Same Seed is Reproducible (Same Process)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("seed", SEEDS)
def test_basic_walk_same_seed_is_reproducible(seed):
    """Same seed → identical signature in the same process."""
    out1 = get_randomized_output_basic_walk(seed)
    out2 = get_randomized_output_basic_walk(seed)
    assert signature(out1) == signature(out2)


@pytest.mark.parametrize("seed", SEEDS)
def test_node2vec_walk_same_seed_is_reproducible(seed):
    """Same seed → identical signature in the same process."""
    out1 = get_randomized_output_node2vec_walk(seed)
    out2 = get_randomized_output_node2vec_walk(seed)
    assert signature(out1) == signature(out2)


@pytest.mark.parametrize("seed", SEEDS)
def test_generate_walks_same_seed_is_reproducible(seed):
    """Same seed → identical signature in the same process."""
    out1 = get_randomized_output_generate_walks(seed)
    out2 = get_randomized_output_generate_walks(seed)
    assert signature(out1) == signature(out2)


@pytest.mark.parametrize("seed", SEEDS)
def test_multilayer_er_same_seed_is_reproducible(seed):
    """Same seed → identical signature in the same process."""
    out1 = get_randomized_output_multilayer_er(seed)
    out2 = get_randomized_output_multilayer_er(seed)
    assert signature(out1) == signature(out2)


@pytest.mark.parametrize("seed", SEEDS)
def test_multiplex_er_same_seed_is_reproducible(seed):
    """Same seed → identical signature in the same process."""
    out1 = get_randomized_output_multiplex_er(seed)
    out2 = get_randomized_output_multiplex_er(seed)
    assert signature(out1) == signature(out2)


@pytest.mark.parametrize("seed", SEEDS)
def test_multiplex_generator_same_seed_is_reproducible(seed):
    """Same seed → identical signature in the same process."""
    out1 = get_randomized_output_multiplex_generator(seed)
    out2 = get_randomized_output_multiplex_generator(seed)
    assert signature(out1) == signature(out2)


# ─────────────────────────────────────────────────────────────────────────────
# Test: Same Seed is Reproducible (Cross-Process)
# ─────────────────────────────────────────────────────────────────────────────
def _worker_basic_walk(seed: int):
    """Subprocess target for basic_random_walk."""
    return signature(get_randomized_output_basic_walk(seed))


def _worker_node2vec_walk(seed: int):
    """Subprocess target for node2vec_walk."""
    return signature(get_randomized_output_node2vec_walk(seed))


def _worker_generate_walks(seed: int):
    """Subprocess target for generate_walks."""
    return signature(get_randomized_output_generate_walks(seed))


def _worker_multilayer_er(seed: int):
    """Subprocess target for random_multilayer_ER."""
    return signature(get_randomized_output_multilayer_er(seed))


def _worker_multiplex_er(seed: int):
    """Subprocess target for random_multiplex_ER."""
    return signature(get_randomized_output_multiplex_er(seed))


def _worker_multiplex_generator(seed: int):
    """Subprocess target for random_multiplex_generator."""
    return signature(get_randomized_output_multiplex_generator(seed))


@pytest.mark.parametrize("seed", SEEDS)
def test_basic_walk_same_seed_across_processes(seed):
    """Same seed → identical signature across processes."""
    with mp.get_context("spawn").Pool(processes=2) as pool:
        sigs = pool.map(_worker_basic_walk, [seed, seed])
    assert sigs[0] == sigs[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_node2vec_walk_same_seed_across_processes(seed):
    """Same seed → identical signature across processes."""
    with mp.get_context("spawn").Pool(processes=2) as pool:
        sigs = pool.map(_worker_node2vec_walk, [seed, seed])
    assert sigs[0] == sigs[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_generate_walks_same_seed_across_processes(seed):
    """Same seed → identical signature across processes."""
    with mp.get_context("spawn").Pool(processes=2) as pool:
        sigs = pool.map(_worker_generate_walks, [seed, seed])
    assert sigs[0] == sigs[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_multilayer_er_same_seed_across_processes(seed):
    """Same seed → identical signature across processes."""
    with mp.get_context("spawn").Pool(processes=2) as pool:
        sigs = pool.map(_worker_multilayer_er, [seed, seed])
    assert sigs[0] == sigs[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_multiplex_er_same_seed_across_processes(seed):
    """Same seed → identical signature across processes."""
    with mp.get_context("spawn").Pool(processes=2) as pool:
        sigs = pool.map(_worker_multiplex_er, [seed, seed])
    assert sigs[0] == sigs[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_multiplex_generator_same_seed_across_processes(seed):
    """Same seed → identical signature across processes."""
    with mp.get_context("spawn").Pool(processes=2) as pool:
        sigs = pool.map(_worker_multiplex_generator, [seed, seed])
    assert sigs[0] == sigs[1]


# ─────────────────────────────────────────────────────────────────────────────
# Test: Different Seeds Vary
# ─────────────────────────────────────────────────────────────────────────────
def test_basic_walk_different_seeds_vary():
    """Across seeds, at least one signature differs."""
    sigs = [signature(get_randomized_output_basic_walk(s)) for s in SEEDS]
    assert len(set(sigs)) > 1, (
        "All outputs identical across seeds—unexpected; "
        "check seeding or algorithm randomness."
    )


def test_node2vec_walk_different_seeds_vary():
    """Across seeds, at least one signature differs."""
    sigs = [signature(get_randomized_output_node2vec_walk(s)) for s in SEEDS]
    assert len(set(sigs)) > 1, (
        "All outputs identical across seeds—unexpected; "
        "check seeding or algorithm randomness."
    )


def test_generate_walks_different_seeds_vary():
    """Across seeds, at least one signature differs."""
    sigs = [signature(get_randomized_output_generate_walks(s)) for s in SEEDS]
    assert len(set(sigs)) > 1, (
        "All outputs identical across seeds—unexpected; "
        "check seeding or algorithm randomness."
    )


def test_multilayer_er_different_seeds_vary():
    """Across seeds, at least one signature differs."""
    sigs = [signature(get_randomized_output_multilayer_er(s)) for s in SEEDS]
    assert len(set(sigs)) > 1, (
        "All outputs identical across seeds—unexpected; "
        "check seeding or algorithm randomness."
    )


def test_multiplex_er_different_seeds_vary():
    """Across seeds, at least one signature differs."""
    sigs = [signature(get_randomized_output_multiplex_er(s)) for s in SEEDS]
    assert len(set(sigs)) > 1, (
        "All outputs identical across seeds—unexpected; "
        "check seeding or algorithm randomness."
    )


def test_multiplex_generator_different_seeds_vary():
    """Across seeds, at least one signature differs."""
    sigs = [signature(get_randomized_output_multiplex_generator(s)) for s in SEEDS]
    assert len(set(sigs)) > 1, (
        "All outputs identical across seeds—unexpected; "
        "check seeding or algorithm randomness."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test: RNG State Restoration
# ─────────────────────────────────────────────────────────────────────────────
def test_fixed_seed_does_not_mutate_global_rng_state():
    """Verify fixed_seed context manager restores RNG state."""
    # Capture initial states
    py_state_before = random.getstate()
    np_state_before = np.random.get_state()
    
    # Generate some randomness before
    random.random()
    np.random.random()
    
    # Capture states after some randomness
    py_state_mid = random.getstate()
    np_state_mid = np.random.get_state()
    
    # Use fixed_seed context
    with fixed_seed(42):
        random.random()
        np.random.random()
    
    # States should be restored to what they were before entering context
    py_state_after = random.getstate()
    np_state_after = np.random.get_state()
    
    assert py_state_after == py_state_mid
    assert np.array_equal(np_state_after[1], np_state_mid[1])


def test_fixed_seed_produces_deterministic_results():
    """Verify fixed_seed actually fixes the seed."""
    results1 = []
    results2 = []
    
    # First run
    with fixed_seed(42):
        results1.append(random.random())
        results1.append(np.random.random())
    
    # Second run with same seed
    with fixed_seed(42):
        results2.append(random.random())
        results2.append(np.random.random())
    
    assert results1 == results2


# ─────────────────────────────────────────────────────────────────────────────
# Test: Signature Function
# ─────────────────────────────────────────────────────────────────────────────
def test_signature_numpy_arrays():
    """Signature handles numpy arrays correctly."""
    arr1 = np.array([1, 2, 3, 4, 5])
    arr2 = np.array([1, 2, 3, 4, 5])
    arr3 = np.array([1, 2, 3, 4, 6])
    
    sig1 = signature(arr1)
    sig2 = signature(arr2)
    sig3 = signature(arr3)
    
    assert sig1 == sig2
    assert sig1 != sig3


def test_signature_lists():
    """Signature handles lists correctly."""
    list1 = [1, 2, 3, [4, 5]]
    list2 = [1, 2, 3, [4, 5]]
    list3 = [1, 2, 3, [4, 6]]
    
    sig1 = signature(list1)
    sig2 = signature(list2)
    sig3 = signature(list3)
    
    assert sig1 == sig2
    assert sig1 != sig3


def test_signature_dicts():
    """Signature handles dicts correctly."""
    dict1 = {"a": 1, "b": 2, "c": [3, 4]}
    dict2 = {"a": 1, "b": 2, "c": [3, 4]}
    dict3 = {"a": 1, "b": 2, "c": [3, 5]}
    
    sig1 = signature(dict1)
    sig2 = signature(dict2)
    sig3 = signature(dict3)
    
    assert sig1 == sig2
    assert sig1 != sig3


def test_signature_graphs():
    """Signature handles NetworkX graphs correctly."""
    G1 = nx.Graph()
    G1.add_edge(0, 1, weight=1.0)
    G1.add_edge(1, 2, weight=2.0)
    
    G2 = nx.Graph()
    G2.add_edge(0, 1, weight=1.0)
    G2.add_edge(1, 2, weight=2.0)
    
    G3 = nx.Graph()
    G3.add_edge(0, 1, weight=1.0)
    G3.add_edge(1, 2, weight=3.0)  # Different weight
    
    sig1 = signature(G1)
    sig2 = signature(G2)
    sig3 = signature(G3)
    
    assert sig1 == sig2
    assert sig1 != sig3


# ─────────────────────────────────────────────────────────────────────────────
# Optional Tests (Marked for Future Extension)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.skip(reason="Workers parameter not yet implemented in py3plex walks")
def test_workers_one_is_deterministic():
    """If the algorithm supports parallelism, workers=1 should be deterministic."""
    # This test is skipped because the current walk implementations
    # don't expose a workers/n_jobs parameter. If/when they do, this test
    # can be enabled to ensure single-worker determinism.
    pass
