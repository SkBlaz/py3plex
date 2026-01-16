"""Algorithm runner adapters for benchmarking.

This module provides standardized adapters for running community detection
algorithms with budget constraints and UQ support.
"""

import time
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib
import json

import numpy as np

from py3plex.benchmarks.budget import Budget
from py3plex.exceptions import AlgorithmError


@dataclass
class CommunityRunResult:
    """Result from running a community detection algorithm.

    Attributes:
        partition: Node -> community mapping
        runtime_ms: Runtime in milliseconds
        algorithm: Algorithm name
        params: Algorithm parameters
        meta: Additional metadata
        uq_partitions: UQ replicates (if UQ enabled)
        trace: Trace information (for AutoCommunity)
    """

    partition: Dict[Any, int]
    runtime_ms: float
    algorithm: str
    params: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    uq_partitions: List[Dict[Any, int]] = field(default_factory=list)
    trace: Optional[List[Dict[str, Any]]] = None


class CommunityAlgorithmRunner:
    """Base class for community detection algorithm runners.

    Provides standardized interface for running algorithms with budget
    constraints and UQ support.
    """

    def __init__(self, name: str):
        """Initialize runner.

        Args:
            name: Algorithm name
        """
        self.name = name

    def run(
        self,
        network: Any,
        layers: Optional[List[str]] = None,
        seed: Optional[int] = None,
        budget: Optional[Budget] = None,
        uq_spec: Optional[Dict[str, Any]] = None,
        **params
    ) -> CommunityRunResult:
        """Run the algorithm.

        Args:
            network: Multilayer network
            layers: Optional layer list
            seed: Random seed
            budget: Optional budget constraint
            uq_spec: Optional UQ specification
            **params: Algorithm-specific parameters

        Returns:
            CommunityRunResult with partition and metadata

        Raises:
            AlgorithmError: If algorithm fails
        """
        raise NotImplementedError("Subclasses must implement run()")


class LouvainRunner(CommunityAlgorithmRunner):
    """Runner for Louvain algorithm."""

    def __init__(self):
        super().__init__("louvain")

    def run(
        self,
        network: Any,
        layers: Optional[List[str]] = None,
        seed: Optional[int] = None,
        budget: Optional[Budget] = None,
        uq_spec: Optional[Dict[str, Any]] = None,
        **params
    ) -> CommunityRunResult:
        """Run Louvain algorithm.

        Args:
            network: Multilayer network
            layers: Optional layer list
            seed: Random seed
            budget: Optional budget (not used by Louvain)
            uq_spec: Optional UQ specification
            **params: resolution (default 1.0)

        Returns:
            CommunityRunResult with partition
        """
        import networkx as nx
        from py3plex.algorithms.community_detection.community_louvain import (
            best_partition,
        )

        start_time = time.time()

        # Get resolution parameter
        resolution = params.get("resolution", 1.0)

        # Flatten network to single graph
        if hasattr(network, "core_network"):
            # py3plex multilayer network - use core_network (NetworkX MultiGraph)
            # Filter to specified layers if provided
            G = nx.Graph()
            for u, v in network.core_network.edges():
                # Nodes are tuples (node_id, layer)
                if layers:
                    # Check if both nodes are in specified layers
                    if len(u) >= 2 and len(v) >= 2:
                        if u[1] in layers and v[1] in layers:
                            # Add edge with just node IDs (strip layer)
                            G.add_edge(u[0], v[0])
                else:
                    # No layer filter - add all edges
                    G.add_edge(u[0] if len(u) >= 2 else u, v[0] if len(v) >= 2 else v)
        elif hasattr(network, "get_layers"):
            # Alternative multilayer interface
            G = nx.Graph()
            for layer in layers or network.get_layers():
                # This path is kept for potential future compatibility
                # but may not work with current py3plex
                pass
        else:
            # Plain NetworkX graph
            G = network

        # Run Louvain
        try:
            if seed is not None:
                np.random.seed(seed)
            partition = best_partition(G, resolution=resolution)
        except Exception as e:
            raise AlgorithmError(f"Louvain failed: {e}", algorithm_name="louvain") from e

        runtime_ms = (time.time() - start_time) * 1000

        # Handle UQ if requested
        uq_partitions = []
        if uq_spec and uq_spec.get("n_samples", 0) > 1:
            uq_partitions = self._run_uq(G, resolution, uq_spec)

        return CommunityRunResult(
            partition=partition,
            runtime_ms=runtime_ms,
            algorithm="louvain",
            params={"resolution": resolution},
            uq_partitions=uq_partitions,
        )

    def _run_uq(self, G, resolution, uq_spec) -> List[Dict[Any, int]]:
        """Run UQ replicates for Louvain."""
        from py3plex.algorithms.community_detection.community_louvain import (
            best_partition,
        )

        method = uq_spec.get("method", "seed")
        n_samples = uq_spec.get("n_samples", 10)
        base_seed = uq_spec.get("seed", 42)

        partitions = []

        if method == "seed":
            # Run with different seeds
            for i in range(n_samples):
                np.random.seed(base_seed + i)
                part = best_partition(G, resolution=resolution)
                partitions.append(part)

        else:
            warnings.warn(f"UQ method '{method}' not supported for Louvain, using seed-based")
            for i in range(n_samples):
                np.random.seed(base_seed + i)
                part = best_partition(G, resolution=resolution)
                partitions.append(part)

        return partitions


class LeidenRunner(CommunityAlgorithmRunner):
    """Runner for Leiden algorithm."""

    def __init__(self):
        super().__init__("leiden")

    def run(
        self,
        network: Any,
        layers: Optional[List[str]] = None,
        seed: Optional[int] = None,
        budget: Optional[Budget] = None,
        uq_spec: Optional[Dict[str, Any]] = None,
        **params
    ) -> CommunityRunResult:
        """Run Leiden algorithm.

        Args:
            network: Multilayer network
            layers: Optional layer list
            seed: Random seed
            budget: Optional budget (n_iter can be constrained)
            uq_spec: Optional UQ specification
            **params: gamma, n_iter

        Returns:
            CommunityRunResult with partition
        """
        try:
            import leidenalg
            import igraph as ig
        except ImportError:
            raise AlgorithmError(
                "Leiden requires leidenalg and python-igraph",
                algorithm_name="leiden",
                suggestions=["pip install leidenalg python-igraph"],
            )

        import networkx as nx

        start_time = time.time()

        # Get parameters
        gamma = params.get("gamma", 1.0)
        n_iter = params.get("n_iter", 2)

        # Flatten network
        if hasattr(network, "core_network"):
            # py3plex multilayer network
            G = nx.Graph()
            for u, v in network.core_network.edges():
                if layers:
                    if len(u) >= 2 and len(v) >= 2:
                        if u[1] in layers and v[1] in layers:
                            G.add_edge(u[0], v[0])
                else:
                    G.add_edge(u[0] if len(u) >= 2 else u, v[0] if len(v) >= 2 else v)
        elif hasattr(network, "get_layers"):
            G = nx.Graph()
            for layer in layers or network.get_layers():
                pass  # Alternative interface (not implemented)
        else:
            G = network

        # Convert to igraph
        g = ig.Graph.from_networkx(G)

        # Run Leiden
        try:
            if seed is not None:
                np.random.seed(seed)

            part = leidenalg.find_partition(
                g,
                leidenalg.RBConfigurationVertexPartition,
                resolution_parameter=gamma,
                n_iterations=n_iter,
                seed=seed,
            )

            # Convert to node -> community dict
            node_list = list(G.nodes())
            partition = {node_list[i]: part.membership[i] for i in range(len(node_list))}

        except Exception as e:
            raise AlgorithmError(f"Leiden failed: {e}", algorithm_name="leiden") from e

        runtime_ms = (time.time() - start_time) * 1000

        # Handle UQ if requested
        uq_partitions = []
        if uq_spec and uq_spec.get("n_samples", 0) > 1:
            uq_partitions = self._run_uq(g, node_list, gamma, n_iter, uq_spec)

        return CommunityRunResult(
            partition=partition,
            runtime_ms=runtime_ms,
            algorithm="leiden",
            params={"gamma": gamma, "n_iter": n_iter},
            uq_partitions=uq_partitions,
        )

    def _run_uq(self, g, node_list, gamma, n_iter, uq_spec) -> List[Dict[Any, int]]:
        """Run UQ replicates for Leiden."""
        import leidenalg

        method = uq_spec.get("method", "seed")
        n_samples = uq_spec.get("n_samples", 10)
        base_seed = uq_spec.get("seed", 42)

        partitions = []

        if method == "seed":
            for i in range(n_samples):
                np.random.seed(base_seed + i)
                part = leidenalg.find_partition(
                    g,
                    leidenalg.RBConfigurationVertexPartition,
                    resolution_parameter=gamma,
                    n_iterations=n_iter,
                    seed=base_seed + i,
                )
                partition = {node_list[j]: part.membership[j] for j in range(len(node_list))}
                partitions.append(partition)
        else:
            warnings.warn(f"UQ method '{method}' not supported for Leiden, using seed-based")
            for i in range(n_samples):
                np.random.seed(base_seed + i)
                part = leidenalg.find_partition(
                    g,
                    leidenalg.RBConfigurationVertexPartition,
                    resolution_parameter=gamma,
                    n_iterations=n_iter,
                    seed=base_seed + i,
                )
                partition = {node_list[j]: part.membership[j] for j in range(len(node_list))}
                partitions.append(partition)

        return partitions


class AutoCommunityRunner(CommunityAlgorithmRunner):
    """Runner for AutoCommunity meta-algorithm."""

    def __init__(self):
        super().__init__("autocommunity")

    def run(
        self,
        network: Any,
        layers: Optional[List[str]] = None,
        seed: Optional[int] = None,
        budget: Optional[Budget] = None,
        uq_spec: Optional[Dict[str, Any]] = None,
        **params
    ) -> CommunityRunResult:
        """Run AutoCommunity algorithm.

        Args:
            network: Multilayer network
            layers: Optional layer list
            seed: Random seed
            budget: Optional budget constraint
            uq_spec: Optional UQ specification
            **params: mode, candidate_set, fast, etc.

        Returns:
            CommunityRunResult with winner partition and trace
        """
        from py3plex.algorithms.community_detection.autocommunity import AutoCommunity

        start_time = time.time()

        # Get parameters
        mode = params.get("mode", "pareto")
        candidate_set = params.get("candidate_set", "core")
        fast = params.get("fast", False)

        # Parse candidate algorithms
        if candidate_set == "core":
            candidates = ["louvain", "leiden"]
        elif candidate_set == "core+sbm":
            candidates = ["louvain", "leiden", "sbm"]
        else:
            # Assume it's a list
            candidates = candidate_set if isinstance(candidate_set, list) else ["louvain", "leiden"]

        # Build AutoCommunity pipeline
        ac = AutoCommunity()
        ac = ac.candidates(*candidates)
        ac = ac.metrics("modularity", "coverage")

        if seed is not None:
            ac = ac.seed(seed)

        # Add UQ if specified
        if uq_spec and uq_spec.get("n_samples", 0) > 1:
            uq_method = uq_spec.get("method", "seed")
            n_samples = uq_spec.get("n_samples", 10)
            uq_seed = uq_spec.get("seed", seed or 42)
            ac = ac.uq(method=uq_method, n_samples=n_samples, seed=uq_seed)

        # Set selection mode
        if mode == "pareto":
            ac = ac.pareto()
        elif mode == "wins":
            ac = ac.select_by_wins()
        else:
            ac = ac.pareto()

        # TODO: Add budget support to AutoCommunity
        # For now, just run without budget constraints
        if budget:
            warnings.warn("Budget constraints not yet implemented for AutoCommunity")

        # Execute
        try:
            result = ac.execute(network)
        except Exception as e:
            raise AlgorithmError(f"AutoCommunity failed: {e}", algorithm_name="autocommunity") from e

        runtime_ms = (time.time() - start_time) * 1000

        # Extract winner partition
        partition = result.consensus_partition if hasattr(result, "consensus_partition") else {}

        # Extract trace (evaluation matrix)
        trace = []
        if hasattr(result, "evaluation_matrix"):
            eval_df = result.evaluation_matrix
            for _, row in eval_df.iterrows():
                trace.append({
                    "algorithm": row.get("algorithm", "unknown"),
                    "modularity": row.get("modularity", 0.0),
                    "coverage": row.get("coverage", 0.0),
                })

        # Extract UQ partitions if available
        uq_partitions = []
        if hasattr(result, "uq_partitions"):
            uq_partitions = result.uq_partitions

        # Get selected algorithm info
        algo_name = result.algorithm.get("name", "unknown") if hasattr(result, "algorithm") else "unknown"

        return CommunityRunResult(
            partition=partition,
            runtime_ms=runtime_ms,
            algorithm="autocommunity",
            params={
                "mode": mode,
                "candidate_set": candidate_set,
                "fast": fast,
                "winner": algo_name,
            },
            meta={"winner_algorithm": algo_name},
            uq_partitions=uq_partitions,
            trace=trace,
        )


# Registry of runners
_RUNNER_REGISTRY: Dict[str, type] = {
    "louvain": LouvainRunner,
    "leiden": LeidenRunner,
    "autocommunity": AutoCommunityRunner,
}


def get_runner(algorithm: str) -> CommunityAlgorithmRunner:
    """Get a runner for an algorithm.

    Args:
        algorithm: Algorithm name

    Returns:
        CommunityAlgorithmRunner instance

    Raises:
        ValueError: If algorithm not found
    """
    runner_class = _RUNNER_REGISTRY.get(algorithm)
    if runner_class is None:
        raise ValueError(f"Unknown algorithm: {algorithm}. Available: {list(_RUNNER_REGISTRY.keys())}")

    return runner_class()


def create_runner_from_spec(algo_spec: Union[str, Tuple[str, dict]]) -> Tuple[CommunityAlgorithmRunner, dict]:
    """Create a runner from an algorithm specification.

    Args:
        algo_spec: Algorithm specification:
            - "algorithm_name"
            - ("algorithm_name", {"param": value})
            - ("algorithm_name", {"grid": {...}})

    Returns:
        Tuple of (runner, params_dict)

    Raises:
        ValueError: If spec is invalid
    """
    if isinstance(algo_spec, str):
        # Simple string spec
        runner = get_runner(algo_spec)
        return runner, {}

    elif isinstance(algo_spec, tuple) and len(algo_spec) == 2:
        algo_name, params = algo_spec

        # Check if this is a grid spec
        if "grid" in params:
            # Grid will be expanded later by executor
            runner = get_runner(algo_name)
            return runner, params
        else:
            # Single config
            runner = get_runner(algo_name)
            return runner, params

    else:
        raise ValueError(f"Invalid algorithm spec: {algo_spec}")


def compute_config_id(params: dict) -> str:
    """Compute stable hash for algorithm configuration.

    Args:
        params: Parameter dictionary

    Returns:
        Hex hash string
    """
    # Normalize params for hashing
    normalized = json.dumps(params, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
