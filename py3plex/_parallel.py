"""Private parallel execution utilities for py3plex.

This module provides internal parallelization utilities for null models
and uncertainty quantification. These functions are NOT part of the public API.

Key features:
- Deterministic parallel execution with seed spawning
- Serial fallback when n_jobs=1
- Optional backends: multiprocessing (default), joblib (if available)
- Optional progress reporting with tqdm

**INTERNAL USE ONLY - NOT A PUBLIC API**
"""

from typing import Any, Callable, Iterable, List, Optional, Union
import warnings

import numpy as np


def spawn_seeds(base_seed: Optional[int], n: int) -> List[Optional[int]]:
    """Spawn deterministic child seeds from a base seed.
    
    Uses numpy's SeedSequence to generate independent, reproducible child seeds.
    Each child seed is guaranteed to be different and deterministically derived
    from the base seed, ensuring reproducibility across parallel runs.
    
    Parameters
    ----------
    base_seed : int or None
        Base seed for spawning children. If None, returns [None] * n.
    n : int
        Number of child seeds to generate.
    
    Returns
    -------
    list of int or None
        List of n child seeds. If base_seed is None, returns [None] * n.
    
    Examples
    --------
    >>> seeds = spawn_seeds(42, 3)
    >>> len(seeds)
    3
    >>> seeds[0] != seeds[1] != seeds[2]
    True
    >>> # Same base seed always produces same children
    >>> spawn_seeds(42, 3) == spawn_seeds(42, 3)
    True
    
    Notes
    -----
    - Uses numpy.random.SeedSequence for cryptographically sound seed spawning
    - Each child seed is independent and suitable for parallel execution
    - Deterministic: same base_seed + n always produces same children
    - If base_seed is None, returns [None] * n (no seeding)
    """
    if base_seed is None:
        return [None] * n
    
    # Use SeedSequence for deterministic, independent child seeds
    ss = np.random.SeedSequence(base_seed)
    child_sequences = ss.spawn(n)
    
    # Extract entropy as seed values (generates deterministic 64-bit integers)
    child_seeds = [int(cs.generate_state(1)[0]) for cs in child_sequences]
    
    return child_seeds


def parallel_map(
    func: Callable[[Any], Any],
    items: Iterable[Any],
    *,
    n_jobs: int = 1,
    backend: str = "multiprocessing",
    chunksize: Optional[int] = None,
    progress: bool = False,
    desc: Optional[str] = None,
) -> List[Any]:
    """Apply a function to items in parallel with optional progress reporting.
    
    This is an internal utility for parallelizing independent computations
    (e.g., generating null model samples, bootstrap replicates).
    
    **INTERNAL USE ONLY - NOT A PUBLIC API**
    
    Parameters
    ----------
    func : callable
        Function to apply to each item. Must be picklable for multiprocessing.
        Signature: func(item) -> result
    items : iterable
        Items to process. Will be converted to list internally.
    n_jobs : int, default=1
        Number of parallel jobs. If 1, runs serially (no multiprocessing overhead).
        If -1, uses all available CPU cores.
    backend : str, default="multiprocessing"
        Backend for parallelization:
        - "multiprocessing": Use Python's multiprocessing (always available)
        - "joblib": Use joblib if available (falls back to multiprocessing)
    chunksize : int, optional
        Chunk size for parallel processing. If None, uses reasonable default.
    progress : bool, default=False
        If True and tqdm is available, shows progress bar.
    desc : str, optional
        Description for progress bar (only used if progress=True).
    
    Returns
    -------
    list
        Results in the same order as input items.
    
    Examples
    --------
    >>> def square(x):
    ...     return x * x
    >>> results = parallel_map(square, [1, 2, 3], n_jobs=2)
    >>> results
    [1, 4, 9]
    
    Notes
    -----
    - n_jobs=1 runs serially (no multiprocessing overhead)
    - Uses spawn context for Windows compatibility
    - Progress bars require tqdm to be installed
    - joblib backend requires joblib to be installed
    """
    # Convert to list for length and multiple iterations
    items_list = list(items)
    n_items = len(items_list)
    
    if n_items == 0:
        return []
    
    # Serial execution for n_jobs=1
    if n_jobs == 1:
        if progress:
            try:
                from tqdm import tqdm
                items_iter = tqdm(items_list, desc=desc or "Processing")
            except ImportError:
                items_iter = items_list
        else:
            items_iter = items_list
        
        return [func(item) for item in items_iter]
    
    # Parallel execution
    if n_jobs == -1:
        import multiprocessing as mp
        n_jobs = mp.cpu_count()
    
    # Ensure n_jobs is reasonable
    n_jobs = max(1, min(n_jobs, n_items))
    
    # Choose backend
    if backend == "joblib":
        try:
            from joblib import Parallel, delayed
            
            # Use joblib with spawn context for safety
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                results = Parallel(
                    n_jobs=n_jobs,
                    backend="multiprocessing",
                    verbose=10 if progress else 0,
                )(delayed(func)(item) for item in items_list)
            
            return results
        except ImportError:
            # Fall back to multiprocessing
            warnings.warn(
                "joblib not available, falling back to multiprocessing backend",
                RuntimeWarning
            )
            backend = "multiprocessing"
    
    if backend == "multiprocessing":
        import multiprocessing as mp
        
        # Use spawn context for Windows compatibility
        ctx = mp.get_context("spawn")
        
        # Determine chunksize
        if chunksize is None:
            # Heuristic: distribute work evenly with some overhead
            chunksize = max(1, n_items // (n_jobs * 4))
        
        # Process in parallel
        with ctx.Pool(processes=n_jobs) as pool:
            if progress:
                try:
                    from tqdm import tqdm
                    # Use imap with progress bar
                    results = list(tqdm(
                        pool.imap(func, items_list, chunksize=chunksize),
                        total=n_items,
                        desc=desc or "Processing"
                    ))
                except ImportError:
                    # No progress bar, just run
                    results = pool.map(func, items_list, chunksize=chunksize)
            else:
                results = pool.map(func, items_list, chunksize=chunksize)
        
        return results
    
    raise ValueError(
        f"Unknown backend '{backend}'. "
        "Must be 'multiprocessing' or 'joblib'"
    )


def _compute_random_value(seed):
    """Generate a deterministic random value from seed.
    
    This is a module-level function so it can be pickled for multiprocessing.
    """
    if seed is None:
        return np.random.rand()
    rng = np.random.default_rng(seed)
    return rng.random()


def _test_parallel_determinism():
    """Internal test to verify parallel execution is deterministic.
    
    This is used for internal validation and testing.
    """
    # Test 1: Same base seed should produce same results
    base_seed = 42
    n_tasks = 10
    
    # Serial execution
    seeds_serial = spawn_seeds(base_seed, n_tasks)
    results_serial = parallel_map(_compute_random_value, seeds_serial, n_jobs=1)
    
    # Parallel execution
    seeds_parallel = spawn_seeds(base_seed, n_tasks)
    results_parallel = parallel_map(_compute_random_value, seeds_parallel, n_jobs=2)
    
    # Results should be identical
    assert len(results_serial) == len(results_parallel)
    for i, (r_s, r_p) in enumerate(zip(results_serial, results_parallel)):
        assert abs(r_s - r_p) < 1e-10, f"Mismatch at index {i}: {r_s} != {r_p}"
    
    print("[OK] Determinism test passed: serial and parallel results are identical")
    
    # Test 2: Different base seeds should produce different results
    seeds_different = spawn_seeds(123, n_tasks)
    results_different = parallel_map(_compute_random_value, seeds_different, n_jobs=2)
    
    # At least one result should be different
    assert any(abs(r1 - r2) > 1e-6 for r1, r2 in zip(results_serial, results_different))
    print("[OK] Independence test passed: different base seeds produce different results")
    
    # Test 3: None seed should work
    seeds_none = spawn_seeds(None, n_tasks)
    results_none = parallel_map(_compute_random_value, seeds_none, n_jobs=1)
    assert len(results_none) == n_tasks
    print("[OK] None seed test passed")
    
    return True


if __name__ == "__main__":
    # Run internal tests
    print("Running internal parallel execution tests...")
    _test_parallel_determinism()
    print("All tests passed!")
