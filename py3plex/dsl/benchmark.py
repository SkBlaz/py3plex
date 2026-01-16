"""Benchmark DSL builder (B namespace).

This module provides the B builder for creating benchmarking queries that
compare algorithms with fair budgets, deterministic seeding, and rich results.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from py3plex.dsl.ast import (
    BenchmarkNode,
    BenchmarkAlgorithmSpec,
    BenchmarkProtocol,
    LayerExpr,
    UQConfig,
)
from py3plex.dsl.result import QueryResult


class CommunityBenchmarkBuilder:
    """Builder for community detection benchmarks.

    Supports fluent API for benchmarking community detection algorithms
    with fair budgets and deterministic evaluation.

    Example:
        >>> from py3plex.dsl import B, L
        >>> 
        >>> res = (
        ...     B.community()
        ...      .on(network)
        ...      .layers(L["social"])
        ...      .algorithms(
        ...          ("louvain", {"grid": {"resolution": [0.8, 1.0, 1.2]}}),
        ...          ("autocommunity", {"mode": "pareto"}),
        ...      )
        ...      .metrics("modularity", "runtime_ms")
        ...      .repeat(5, seed=42)
        ...      .budget(runtime_ms=10_000)
        ...      .execute()
        ... )
    """

    def __init__(self):
        """Initialize builder."""
        self._node = BenchmarkNode(
            benchmark_type="community",
            datasets=None,
        )

    def on(self, dataset: Any) -> "CommunityBenchmarkBuilder":
        """Set the dataset(s) to benchmark on.

        Args:
            dataset: Single network, dataset name, dict of networks, or list

        Returns:
            Self for chaining
        """
        self._node.datasets = dataset
        return self

    def on_networks(self, networks: Dict[str, Any]) -> "CommunityBenchmarkBuilder":
        """Set multiple named networks to benchmark on.

        Args:
            networks: Dict mapping dataset_id -> network

        Returns:
            Self for chaining
        """
        self._node.datasets = networks
        return self

    def layers(self, layer_expr: Union[str, "LayerExprBuilder", LayerExpr]) -> "CommunityBenchmarkBuilder":
        """Set the layer expression to evaluate on.

        Args:
            layer_expr: Layer expression (L["social"], "all", None)

        Returns:
            Self for chaining
        """
        if isinstance(layer_expr, str):
            if layer_expr == "all":
                self._node.layer_expr = None
            else:
                # Simple layer name
                from py3plex.dsl.ast import LayerExpr, LayerTerm
                self._node.layer_expr = LayerExpr(terms=[LayerTerm(layer_expr)])
        elif hasattr(layer_expr, "_to_ast"):
            # LayerExprBuilder
            self._node.layer_expr = layer_expr._to_ast()
        elif isinstance(layer_expr, LayerExpr):
            self._node.layer_expr = layer_expr
        else:
            self._node.layer_expr = None

        return self

    def algorithms(self, *algo_specs: Union[str, Tuple[str, dict]]) -> "CommunityBenchmarkBuilder":
        """Specify algorithms to benchmark.

        Supports:
        - String: "leiden"
        - Tuple with params: ("leiden", {"gamma": 1.0})
        - Tuple with grid: ("leiden", {"grid": {"gamma": [0.8, 1.0, 1.2]}})
        - AutoCommunity: ("autocommunity", {"mode": "pareto"})

        Args:
            *algo_specs: Algorithm specifications

        Returns:
            Self for chaining
        """
        self._node.algorithm_specs = []

        for spec in algo_specs:
            if isinstance(spec, str):
                # Simple string
                self._node.algorithm_specs.append(
                    BenchmarkAlgorithmSpec(algorithm=spec, params={})
                )
            elif isinstance(spec, tuple) and len(spec) == 2:
                algo_name, params = spec
                self._node.algorithm_specs.append(
                    BenchmarkAlgorithmSpec(algorithm=algo_name, params=params)
                )
            else:
                raise ValueError(f"Invalid algorithm spec: {spec}")

        return self

    def metrics(self, *metric_names: str) -> "CommunityBenchmarkBuilder":
        """Specify metrics to compute.

        Args:
            *metric_names: Metric names (e.g., "modularity", "runtime_ms")

        Returns:
            Self for chaining
        """
        self._node.metrics = list(metric_names)
        return self

    def using(self, protocol: BenchmarkProtocol) -> "CommunityBenchmarkBuilder":
        """Set a pre-configured protocol.

        Args:
            protocol: BenchmarkProtocol instance

        Returns:
            Self for chaining
        """
        self._node.protocol = protocol
        return self

    def repeat(self, k: int, seed: Optional[int] = None) -> "CommunityBenchmarkBuilder":
        """Set number of repeats and seed.

        Args:
            k: Number of repeats
            seed: Base seed for reproducibility

        Returns:
            Self for chaining
        """
        self._node.protocol.repeat = k
        if seed is not None:
            self._node.protocol.seed = seed
        return self

    def uq(
        self,
        method: str = "seed",
        n_samples: int = 10,
        ci: float = 0.95,
        seed: Optional[int] = None,
        **kwargs
    ) -> "CommunityBenchmarkBuilder":
        """Enable uncertainty quantification.

        Args:
            method: UQ method ("seed", "bootstrap", "perturbation")
            n_samples: Number of UQ samples
            ci: Confidence interval level
            seed: UQ seed
            **kwargs: Additional UQ parameters

        Returns:
            Self for chaining
        """
        self._node.protocol.uq_config = UQConfig(
            method=method,
            n_samples=n_samples,
            ci=ci,
            seed=seed,
            kwargs=kwargs,
        )
        return self

    def budget(
        self,
        runtime_ms: Optional[float] = None,
        evals: Optional[int] = None,
        per: str = "repeat",
    ) -> "CommunityBenchmarkBuilder":
        """Set budget constraints.

        Args:
            runtime_ms: Time budget in milliseconds
            evals: Evaluation budget
            per: Budgeting unit ("dataset", "repeat")

        Returns:
            Self for chaining
        """
        self._node.protocol.budget_limit_ms = runtime_ms
        self._node.protocol.budget_limit_evals = evals
        self._node.protocol.budget_per = per
        return self

    def n_jobs(self, n: int) -> "CommunityBenchmarkBuilder":
        """Set number of parallel jobs.

        Args:
            n: Number of jobs

        Returns:
            Self for chaining
        """
        self._node.protocol.n_jobs = n
        return self

    def select(
        self,
        mode: Union[str, Tuple[str, Dict[str, float]]] = "wins",
    ) -> "CommunityBenchmarkBuilder":
        """Set selection mode for winners.

        Args:
            mode: Selection mode:
                - "wins": Count wins across metrics
                - "pareto": Pareto front
                - ("weighted", {"modularity": 0.6, "runtime_ms": -0.4})

        Returns:
            Self for chaining
        """
        if isinstance(mode, str):
            self._node.selection_mode = mode
        elif isinstance(mode, tuple) and len(mode) == 2:
            self._node.selection_mode = mode[0]
            self._node.selection_weights = mode[1]
        else:
            raise ValueError(f"Invalid selection mode: {mode}")

        return self

    def return_trace(self, enabled: bool = True) -> "CommunityBenchmarkBuilder":
        """Enable/disable trace return for AutoCommunity.

        Args:
            enabled: Whether to return traces

        Returns:
            Self for chaining
        """
        self._node.return_trace = enabled
        return self

    def to_ast(self) -> BenchmarkNode:
        """Convert to AST node.

        Returns:
            BenchmarkNode
        """
        # Set default metrics if not specified
        if not self._node.metrics:
            if self._node.protocol.uq_config:
                self._node.metrics = ["modularity", "n_communities", "runtime_ms", "stability"]
            else:
                self._node.metrics = ["modularity", "n_communities", "runtime_ms"]

        return self._node

    def execute(self, **params) -> QueryResult:
        """Execute the benchmark.

        Args:
            **params: Additional parameters

        Returns:
            QueryResult with benchmark results

        Raises:
            ValueError: If configuration is invalid
        """
        from py3plex.dsl.executors.benchmark_executor import execute_benchmark

        # Validate
        if self._node.datasets is None:
            raise ValueError("Must specify dataset via .on()")

        if not self._node.algorithm_specs:
            raise ValueError("Must specify algorithms via .algorithms()")

        # Get AST
        ast = self.to_ast()

        # Execute
        return execute_benchmark(ast, **params)


class BenchmarkProxy:
    """Proxy for creating benchmark builders.

    Entry point for benchmark DSL via B namespace.
    """

    @staticmethod
    def community() -> CommunityBenchmarkBuilder:
        """Create a community detection benchmark builder.

        Returns:
            CommunityBenchmarkBuilder

        Example:
            >>> from py3plex.dsl import B
            >>> B.community().on(net).algorithms("louvain").execute()
        """
        return CommunityBenchmarkBuilder()

    @staticmethod
    def protocol(
        repeat: int = 1,
        seed: Optional[int] = None,
        budget_ms: Optional[float] = None,
        **kwargs
    ) -> BenchmarkProtocol:
        """Create a reusable benchmark protocol.

        Args:
            repeat: Number of repeats
            seed: Base seed
            budget_ms: Time budget in milliseconds
            **kwargs: Additional protocol parameters

        Returns:
            BenchmarkProtocol

        Example:
            >>> protocol = B.protocol(repeat=5, seed=42, budget_ms=10_000)
            >>> B.community().on(net).using(protocol).execute()
        """
        return BenchmarkProtocol(
            repeat=repeat,
            seed=seed,
            budget_limit_ms=budget_ms,
            **kwargs
        )


# Singleton instance
B = BenchmarkProxy()
