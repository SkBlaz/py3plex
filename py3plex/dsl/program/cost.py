"""Cost model for py3plex Graph Programs.

This module provides cost estimation for DSL operators, enabling:
- Concrete time/memory estimates based on graph statistics
- Budget enforcement for bounded execution
- Cost-based query optimization
- Multi-objective optimization (time/memory/stability)

Example:
    >>> from py3plex.dsl import Q
    >>> from py3plex.dsl.program import GraphProgram
    >>> from py3plex.dsl.program.cost import CostModel, GraphStats
    >>> 
    >>> # Create cost model
    >>> model = CostModel()
    >>> 
    >>> # Estimate cost
    >>> stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=3)
    >>> program = GraphProgram.from_ast(Q.nodes().compute("betweenness").to_ast())
    >>> cost = model.estimate_program_cost(program, stats)
    >>> print(f"Estimated time: {cost.time_estimate_seconds:.2f}s")
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from ..ast import (
    Query,
    SelectStmt,
    Target,
    ComputeItem,
    ConditionExpr,
    OrderItem,
)
from .types import Type, ScalarType, TableType


@dataclass(frozen=True)
class GraphStats:
    """Statistics about a graph for cost estimation.
    
    Attributes:
        num_nodes: Total number of nodes
        num_edges: Total number of edges
        num_layers: Number of layers
        avg_degree: Average node degree
        max_degree: Maximum node degree
        edge_density: Edge density per layer (dict of layer -> density)
        is_directed: Whether the graph is directed
        has_temporal: Whether the graph has temporal data
    
    Example:
        >>> stats = GraphStats(
        ...     num_nodes=1000,
        ...     num_edges=5000,
        ...     num_layers=3,
        ...     avg_degree=5.0,
        ...     max_degree=50
        ... )
    """
    
    num_nodes: int
    num_edges: int
    num_layers: int = 1
    avg_degree: float = 0.0
    max_degree: int = 0
    edge_density: Dict[str, float] = field(default_factory=dict)
    is_directed: bool = False
    has_temporal: bool = False
    
    @classmethod
    def from_network(cls, network: Any) -> GraphStats:
        """Extract statistics from a multilayer network.
        
        Args:
            network: Multilayer network object
            
        Returns:
            GraphStats instance
        """
        import networkx as nx
        
        # Get basic counts (properties, not methods)
        num_nodes = network.node_count
        num_edges = network.edge_count
        
        # Get layer info
        layers = network.get_layers() if hasattr(network, 'get_layers') else set()
        num_layers = len(layers) if layers else 1
        
        # Compute degree statistics
        try:
            degrees = network.get_degrees()
            if degrees:
                degree_values = list(degrees.values()) if isinstance(degrees, dict) else degrees
                avg_degree = sum(degree_values) / len(degree_values) if degree_values else 0.0
                max_degree = max(degree_values) if degree_values else 0
            else:
                avg_degree = 0.0
                max_degree = 0
        except Exception:
            # Fallback if get_degrees doesn't work as expected
            avg_degree = (2 * num_edges / num_nodes) if num_nodes > 0 else 0.0
            max_degree = 0
        
        # Compute edge density per layer
        edge_density = {}
        # For multilayer networks, density computation is complex; use simple estimate
        if num_layers > 0 and layers:
            for layer in layers:
                # Simple approximation - skipping actual density calculation
                # to avoid complexity with layer structure
                pass
        
        is_directed = network.directed if hasattr(network, 'directed') else False
        has_temporal = hasattr(network, 'get_snapshot')
        
        return cls(
            num_nodes=num_nodes,
            num_edges=num_edges,
            num_layers=num_layers,
            avg_degree=avg_degree,
            max_degree=max_degree,
            edge_density=edge_density,
            is_directed=is_directed,
            has_temporal=has_temporal,
        )


@dataclass(frozen=True)
class Cost:
    """Cost estimate for an operation.
    
    Attributes:
        time_complexity: Big-O notation (e.g., "O(V + E)")
        time_estimate_seconds: Concrete time estimate in seconds
        memory_estimate_bytes: Memory estimate in bytes
        parallelizable: Whether the operation can be parallelized
        constants: Algorithm-specific constant factors
        confidence: Confidence in the estimate (0.0-1.0)
    
    Example:
        >>> cost = Cost(
        ...     time_complexity="O(V * E)",
        ...     time_estimate_seconds=12.5,
        ...     memory_estimate_bytes=1024 * 1024,
        ...     parallelizable=True,
        ...     constants={"brandes_factor": 1.2}
        ... )
    """
    
    time_complexity: str
    time_estimate_seconds: float
    memory_estimate_bytes: int
    parallelizable: bool = False
    constants: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    
    def __add__(self, other: Cost) -> Cost:
        """Add two costs together (sequential composition)."""
        return Cost(
            time_complexity=f"{self.time_complexity} + {other.time_complexity}",
            time_estimate_seconds=self.time_estimate_seconds + other.time_estimate_seconds,
            memory_estimate_bytes=max(self.memory_estimate_bytes, other.memory_estimate_bytes),
            parallelizable=self.parallelizable and other.parallelizable,
            constants={**self.constants, **other.constants},
            confidence=min(self.confidence, other.confidence),
        )
    
    def scale(self, factor: float) -> Cost:
        """Scale the cost by a factor."""
        return Cost(
            time_complexity=self.time_complexity,
            time_estimate_seconds=self.time_estimate_seconds * factor,
            memory_estimate_bytes=int(self.memory_estimate_bytes * factor),
            parallelizable=self.parallelizable,
            constants=self.constants.copy(),
            confidence=self.confidence * 0.9,  # Less confident when scaled
        )


class CostObjective(Enum):
    """Optimization objective for cost-based planning.
    
    Attributes:
        MIN_TIME: Minimize execution time
        MIN_MEMORY: Minimize memory usage
        MAX_STABILITY: Maximize numerical stability
        BALANCED: Balance time and memory
    """
    
    MIN_TIME = "min_time"
    MIN_MEMORY = "min_memory"
    MAX_STABILITY = "max_stability"
    BALANCED = "balanced"


# Empirical constants (calibrated from benchmarks)
# These should be tuned based on actual hardware and implementation
_CONSTANTS = {
    # Base costs per operation (seconds)
    "node_iteration_per_1k": 0.0001,  # Iterate 1000 nodes
    "edge_iteration_per_1k": 0.0002,  # Iterate 1000 edges
    
    # Centrality algorithm factors (relative to theoretical complexity)
    "degree_factor": 1.0,
    "betweenness_brandes_factor": 2.5,  # Brandes algorithm overhead
    "closeness_factor": 2.0,
    "pagerank_iteration_factor": 0.5,
    "eigenvector_iteration_factor": 0.8,
    "clustering_factor": 1.5,
    
    # Memory per element (bytes)
    "node_memory": 128,  # Memory per node in results
    "edge_memory": 192,  # Memory per edge in results
    "centrality_memory": 64,  # Additional memory per centrality value
    
    # Sorting and filtering
    "sort_factor": 1.2,  # n log n overhead
    "filter_factor": 0.8,  # Filter pass over data
    
    # Community detection
    "louvain_factor": 3.0,
    "label_propagation_factor": 2.0,
    "infomap_factor": 5.0,
    
    # PageRank iterations
    "pagerank_default_iterations": 100,
    "pagerank_convergence_factor": 0.7,  # Often converges early
}


class CostModel:
    """Cost estimation model for DSL operations.
    
    This class provides methods to estimate execution costs for individual
    operators and complete programs. Estimates are based on graph statistics
    and empirical constants.
    
    Example:
        >>> model = CostModel()
        >>> stats = GraphStats(num_nodes=1000, num_edges=5000)
        >>> cost = model.estimate_operator_cost("degree", None, stats)
        >>> print(f"Time: {cost.time_estimate_seconds:.4f}s")
    """
    
    def __init__(self, constants: Optional[Dict[str, float]] = None):
        """Initialize the cost model.
        
        Args:
            constants: Optional custom constant factors
        """
        self.constants = {**_CONSTANTS}
        if constants:
            self.constants.update(constants)
        
        # Register cost functions for different operators
        self._cost_functions: Dict[str, Callable] = {
            # Centrality measures
            "degree": self._cost_degree,
            "betweenness_centrality": self._cost_betweenness,
            "betweenness": self._cost_betweenness,
            "closeness_centrality": self._cost_closeness,
            "closeness": self._cost_closeness,
            "pagerank": self._cost_pagerank,
            "eigenvector_centrality": self._cost_eigenvector,
            "eigenvector": self._cost_eigenvector,
            "clustering": self._cost_clustering,
            "clustering_coefficient": self._cost_clustering,
            
            # Community detection
            "louvain": self._cost_louvain,
            "label_propagation": self._cost_label_propagation,
            "infomap": self._cost_infomap,
            
            # Structural measures
            "katz_centrality": self._cost_katz,
            "core_number": self._cost_core_number,
            "eccentricity": self._cost_eccentricity,
        }
    
    def estimate_operator_cost(
        self,
        operator: str,
        input_type: Optional[Type],
        stats: GraphStats,
        **kwargs: Any,
    ) -> Cost:
        """Estimate cost for a specific operator.
        
        Args:
            operator: Operator name (e.g., "betweenness_centrality")
            input_type: Input type (may affect cost)
            stats: Graph statistics
            **kwargs: Additional operator-specific parameters
            
        Returns:
            Cost estimate
            
        Example:
            >>> model = CostModel()
            >>> stats = GraphStats(num_nodes=1000, num_edges=5000)
            >>> cost = model.estimate_operator_cost("betweenness_centrality", None, stats)
        """
        # Normalize operator name
        operator_clean = operator.lower().replace("_", "")
        
        # Look up cost function
        cost_fn = None
        for key, fn in self._cost_functions.items():
            if key.lower().replace("_", "") == operator_clean:
                cost_fn = fn
                break
        
        if cost_fn is None:
            # Default cost for unknown operators
            return self._cost_default(operator, stats, **kwargs)
        
        return cost_fn(stats, **kwargs)
    
    def estimate_program_cost(
        self,
        program: Any,  # GraphProgram
        stats: GraphStats,
    ) -> Cost:
        """Estimate cost for a complete program.
        
        Args:
            program: GraphProgram instance
            stats: Graph statistics
            
        Returns:
            Total cost estimate
            
        Example:
            >>> from py3plex.dsl import Q
            >>> from py3plex.dsl.program import GraphProgram
            >>> program = GraphProgram.from_ast(Q.nodes().compute("degree").to_ast())
            >>> cost = model.estimate_program_cost(program, stats)
        """
        ast = program.canonical_ast
        return self._estimate_query_cost(ast, stats)
    
    def _estimate_query_cost(self, query: Query, stats: GraphStats) -> Cost:
        """Estimate cost for a Query AST."""
        return self._estimate_select_cost(query.select, stats)
    
    def _estimate_select_cost(self, select: SelectStmt, stats: GraphStats) -> Cost:
        """Estimate cost for a SelectStmt."""
        total_cost = Cost(
            time_complexity="O(1)",
            time_estimate_seconds=0.0,
            memory_estimate_bytes=0,
            parallelizable=True,
            confidence=1.0,
        )
        
        # Base iteration cost
        if select.target == Target.NODES:
            base_cost = self._cost_nodes_iteration(stats)
        elif select.target == Target.EDGES:
            base_cost = self._cost_edges_iteration(stats)
        else:
            base_cost = self._cost_default("communities", stats)
        
        total_cost = total_cost + base_cost
        
        # Where clause cost
        if select.where:
            filter_cost = self._cost_filter(select.where, stats)
            total_cost = total_cost + filter_cost
        
        # Compute costs
        for compute_item in select.compute:
            compute_cost = self.estimate_operator_cost(
                compute_item.name,
                None,
                stats,
                uncertainty=compute_item.uncertainty,
                n_samples=compute_item.n_samples or 50,
            )
            
            # Scale by uncertainty if enabled
            if compute_item.uncertainty:
                n_samples = compute_item.n_samples or 50
                compute_cost = compute_cost.scale(n_samples * 1.1)  # 10% overhead
            
            total_cost = total_cost + compute_cost
        
        # Layer grouping cost
        if select.group_by:
            group_cost = self._cost_grouping(stats, select.group_by)
            total_cost = total_cost + group_cost
        
        # Sorting cost
        if select.order_by:
            sort_cost = self._cost_sorting(stats, len(select.order_by))
            total_cost = total_cost + sort_cost
        
        # Limit doesn't add cost (just truncates)
        
        # Export cost
        if select.export or select.file_export:
            export_cost = self._cost_export(stats)
            total_cost = total_cost + export_cost
        
        return total_cost
    
    # Cost functions for specific operators
    
    def _cost_nodes_iteration(self, stats: GraphStats) -> Cost:
        """Cost of iterating all nodes."""
        time_est = (stats.num_nodes / 1000.0) * self.constants["node_iteration_per_1k"]
        memory_est = stats.num_nodes * self.constants["node_memory"]
        
        return Cost(
            time_complexity="O(V)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.95,
        )
    
    def _cost_edges_iteration(self, stats: GraphStats) -> Cost:
        """Cost of iterating all edges."""
        time_est = (stats.num_edges / 1000.0) * self.constants["edge_iteration_per_1k"]
        memory_est = stats.num_edges * self.constants["edge_memory"]
        
        return Cost(
            time_complexity="O(E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.95,
        )
    
    def _cost_filter(self, where: ConditionExpr, stats: GraphStats) -> Cost:
        """Cost of filtering with WHERE clause."""
        # Check if filter involves degree computation
        needs_degree = False
        for atom in where.atoms:
            if atom.comparison and "degree" in atom.comparison.left.lower():
                needs_degree = True
        
        if needs_degree:
            # Need to compute degrees first
            return self._cost_degree(stats)
        else:
            # Simple attribute filter
            time_est = (stats.num_nodes / 1000.0) * self.constants["node_iteration_per_1k"]
            time_est *= self.constants["filter_factor"]
            
            return Cost(
                time_complexity="O(V)",
                time_estimate_seconds=time_est,
                memory_estimate_bytes=0,  # No extra memory
                parallelizable=True,
                confidence=0.9,
            )
    
    def _cost_grouping(self, stats: GraphStats, group_cols: List[str]) -> Cost:
        """Cost of grouping operation."""
        # Grouping requires a pass over data and hash table construction
        time_est = (stats.num_nodes / 1000.0) * self.constants["node_iteration_per_1k"]
        time_est *= 1.5  # Hash table overhead
        
        # Memory for group keys
        num_groups = min(stats.num_nodes, stats.num_layers ** len(group_cols))
        memory_est = num_groups * 256  # Hash table entry
        
        return Cost(
            time_complexity="O(V)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=False,  # Grouping is inherently sequential
            confidence=0.85,
        )
    
    def _cost_sorting(self, stats: GraphStats, num_keys: int) -> Cost:
        """Cost of sorting results."""
        n = stats.num_nodes
        time_est = (n / 1000.0) * self.constants["node_iteration_per_1k"]
        time_est *= math.log2(max(n, 2)) * self.constants["sort_factor"]
        time_est *= num_keys  # Multiple sort keys
        
        return Cost(
            time_complexity="O(V log V)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=0,  # In-place sort
            parallelizable=True,
            confidence=0.95,
        )
    
    def _cost_export(self, stats: GraphStats) -> Cost:
        """Cost of exporting results."""
        # Export is mainly I/O bound, estimate serialization time
        time_est = (stats.num_nodes / 1000.0) * 0.001  # Fast serialization
        
        return Cost(
            time_complexity="O(V)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=stats.num_nodes * 256,  # Serialization buffer
            parallelizable=False,  # I/O is sequential
            confidence=0.7,
        )
    
    # Centrality measure cost functions
    
    def _cost_degree(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing degree centrality."""
        # Degree is O(E) - iterate edges and count
        time_est = (stats.num_edges / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= self.constants["degree_factor"]
        
        memory_est = stats.num_nodes * self.constants["centrality_memory"]
        
        return Cost(
            time_complexity="O(E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.95,
        )
    
    def _cost_betweenness(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing betweenness centrality."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # Brandes algorithm: O(VE) for unweighted graphs
        # For multilayer, multiply by layers
        complexity_multiplier = V * E * stats.num_layers
        
        # Base time from edge iterations
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= V / 100.0  # Scale by nodes
        time_est *= self.constants["betweenness_brandes_factor"]
        time_est *= stats.num_layers  # Multilayer factor
        
        memory_est = V * self.constants["centrality_memory"] * 3  # Multiple arrays
        
        return Cost(
            time_complexity=f"O(V * E * L) = O({V} * {E} * {stats.num_layers})",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            constants={"brandes_factor": self.constants["betweenness_brandes_factor"]},
            confidence=0.8,
        )
    
    def _cost_closeness(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing closeness centrality."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # Similar to betweenness but slightly cheaper
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= V / 100.0
        time_est *= self.constants["closeness_factor"]
        time_est *= stats.num_layers
        
        memory_est = V * self.constants["centrality_memory"] * 2
        
        return Cost(
            time_complexity=f"O(V * E * L)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.8,
        )
    
    def _cost_pagerank(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing PageRank."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # PageRank: O(iterations * E)
        iterations = self.constants["pagerank_default_iterations"]
        iterations *= self.constants["pagerank_convergence_factor"]  # Often converges early
        
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= iterations
        time_est *= self.constants["pagerank_iteration_factor"]
        time_est *= stats.num_layers
        
        memory_est = V * self.constants["centrality_memory"] * 2  # Current + next
        
        return Cost(
            time_complexity=f"O(iterations * E) ≈ O({int(iterations)} * {E})",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            constants={"iterations": iterations},
            confidence=0.75,
        )
    
    def _cost_eigenvector(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing eigenvector centrality."""
        # Similar to PageRank
        V = stats.num_nodes
        E = stats.num_edges
        
        iterations = self.constants["pagerank_default_iterations"]
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= iterations
        time_est *= self.constants["eigenvector_iteration_factor"]
        
        memory_est = V * self.constants["centrality_memory"] * 2
        
        return Cost(
            time_complexity=f"O(iterations * E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.75,
        )
    
    def _cost_clustering(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing clustering coefficient."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # Clustering: O(V * avg_degree^2) ≈ O(V * E) for sparse graphs
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= V / 100.0
        time_est *= self.constants["clustering_factor"]
        
        memory_est = V * self.constants["centrality_memory"]
        
        return Cost(
            time_complexity="O(V * d^2)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.8,
        )
    
    # Community detection cost functions
    
    def _cost_louvain(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of Louvain community detection."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # Louvain: O(E) per iteration, multiple passes
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= V / 100.0  # Depends on network structure
        time_est *= self.constants["louvain_factor"]
        
        memory_est = V * 128  # Community assignments
        
        return Cost(
            time_complexity="O(E * log V)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=False,
            confidence=0.7,
        )
    
    def _cost_label_propagation(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of label propagation community detection."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # Label propagation: O(E) per iteration
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= self.constants["label_propagation_factor"]
        
        memory_est = V * 128
        
        return Cost(
            time_complexity="O(E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=False,
            confidence=0.75,
        )
    
    def _cost_infomap(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of Infomap community detection."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # Infomap is more expensive
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= V / 100.0
        time_est *= self.constants["infomap_factor"]
        
        memory_est = V * 256
        
        return Cost(
            time_complexity="O(E * log V)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=False,
            confidence=0.65,
        )
    
    # Structural measure cost functions
    
    def _cost_katz(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of Katz centrality."""
        # Similar to eigenvector
        return self._cost_eigenvector(stats, **kwargs)
    
    def _cost_core_number(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of k-core decomposition."""
        V = stats.num_nodes
        E = stats.num_edges
        
        # k-core: O(E)
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= 2.0  # Iterative peeling
        
        memory_est = V * 64
        
        return Cost(
            time_complexity="O(E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=False,
            confidence=0.85,
        )
    
    def _cost_eccentricity(self, stats: GraphStats, **kwargs: Any) -> Cost:
        """Cost of computing eccentricity."""
        # Requires APSP or BFS from each node
        V = stats.num_nodes
        E = stats.num_edges
        
        time_est = (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= V / 10.0  # BFS from each node
        
        memory_est = V * V * 4  # Distance matrix (if cached)
        if memory_est > 1e9:  # Cap at 1GB
            memory_est = int(1e9)
        
        return Cost(
            time_complexity="O(V * E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=True,
            confidence=0.7,
        )
    
    def _cost_default(self, operator: str, stats: GraphStats, **kwargs: Any) -> Cost:
        """Default cost for unknown operators."""
        # Conservative estimate: assume O(V + E)
        V = stats.num_nodes
        E = stats.num_edges
        
        time_est = (V / 1000.0) * self.constants["node_iteration_per_1k"]
        time_est += (E / 1000.0) * self.constants["edge_iteration_per_1k"]
        time_est *= 2.0  # Conservative multiplier
        
        memory_est = V * self.constants["centrality_memory"]
        
        return Cost(
            time_complexity="O(V + E)",
            time_estimate_seconds=time_est,
            memory_estimate_bytes=memory_est,
            parallelizable=False,
            constants={"operator": operator, "warning": "unknown_operator"},
            confidence=0.5,
        )


def parse_time_budget(budget: str) -> float:
    """Parse time budget string to seconds.
    
    Supports:
        - Plain numbers: "30" -> 30.0 seconds
        - Seconds: "30s" -> 30.0 seconds
        - Minutes: "5m" -> 300.0 seconds
        - Hours: "2h" -> 7200.0 seconds
    
    Args:
        budget: Budget string
        
    Returns:
        Time in seconds
        
    Example:
        >>> parse_time_budget("30s")
        30.0
        >>> parse_time_budget("5m")
        300.0
    """
    if isinstance(budget, (int, float)):
        return float(budget)
    
    budget_str = str(budget).strip().lower()
    
    # Try to parse with units
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([smh]?)$', budget_str)
    if not match:
        raise ValueError(f"Invalid time budget format: {budget}")
    
    value, unit = match.groups()
    value = float(value)
    
    if unit == 's' or unit == '':
        return value
    elif unit == 'm':
        return value * 60.0
    elif unit == 'h':
        return value * 3600.0
    else:
        raise ValueError(f"Unknown time unit: {unit}")


def format_time_estimate(seconds: float) -> str:
    """Format time estimate in human-readable form.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string
        
    Example:
        >>> format_time_estimate(45.5)
        '45.5s'
        >>> format_time_estimate(125.0)
        '2m 5s'
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def format_memory_estimate(bytes_val: int) -> str:
    """Format memory estimate in human-readable form.
    
    Args:
        bytes_val: Memory in bytes
        
    Returns:
        Formatted string
        
    Example:
        >>> format_memory_estimate(1024)
        '1.0 KB'
        >>> format_memory_estimate(1048576)
        '1.0 MB'
    """
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
