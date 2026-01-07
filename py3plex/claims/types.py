"""Data types for claim learning.

This module defines core dataclasses for inductive claim discovery:
- Antecedent: Predicate on node attributes (e.g., degree >= 5)
- Consequent: Predicate on computed metrics (e.g., pagerank_rank <= 10)
- ClaimScore: Statistical support and coverage measures
- Claim: Complete claim with provenance and counterexample integration
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class Antecedent:
    """Represents an antecedent predicate (left side of implication).
    
    Antecedents are simple predicates on node attributes like degree, strength,
    layer_count, or top_p membership.
    
    Attributes:
        metric: Metric name (e.g., "degree", "strength")
        predicate_type: Type of predicate ("threshold", "top_p", "layer_count")
        threshold: Threshold value for comparison (e.g., 5 for "degree >= 5")
        operator: Comparison operator (">=", ">", "<=", "<", "=")
        percentile: Percentile value for top_p predicates (e.g., 0.1 for top 10%)
        layer: Optional layer restriction (e.g., "social")
    """
    
    metric: str
    predicate_type: str  # "threshold", "top_p", "layer_count"
    threshold: Optional[float] = None
    operator: Optional[str] = None  # ">=", ">", "<=", "<", "="
    percentile: Optional[float] = None  # for top_p predicates
    layer: Optional[str] = None
    
    def to_dsl_string(self) -> str:
        """Convert to DSL-compatible string representation.
        
        Returns:
            String like "degree__ge(5)" or "top_p(degree, 0.1)"
        """
        if self.predicate_type == "threshold":
            op_map = {">=": "gte", ">": "gt", "<=": "lte", "<": "lt", "=": "eq"}
            op_suffix = op_map.get(self.operator, "gte")
            return f"{self.metric}__{op_suffix}({self.threshold})"
        elif self.predicate_type == "top_p":
            return f"top_p({self.metric}, {self.percentile})"
        elif self.predicate_type == "layer_count":
            op_map = {">=": "gte", ">": "gt", "<=": "lte", "<": "lt", "=": "eq"}
            op_suffix = op_map.get(self.operator, "gte")
            return f"layer_count__{op_suffix}({self.threshold})"
        else:
            return f"{self.metric}({self.threshold})"
    
    def evaluate(self, node_data: Dict[str, Any], all_values: Optional[Dict[str, List[float]]] = None) -> bool:
        """Evaluate predicate on a node's data.
        
        Args:
            node_data: Dictionary of node attributes and metrics
            all_values: Optional dict of metric_name -> list of all values (for top_p)
            
        Returns:
            True if predicate is satisfied
        """
        if self.predicate_type == "threshold":
            value = node_data.get(self.metric)
            if value is None:
                return False
            
            if self.operator == ">=":
                return value >= self.threshold
            elif self.operator == ">":
                return value > self.threshold
            elif self.operator == "<=":
                return value <= self.threshold
            elif self.operator == "<":
                return value < self.threshold
            elif self.operator == "=":
                return value == self.threshold
            return False
        
        elif self.predicate_type == "top_p":
            if all_values is None or self.metric not in all_values:
                return False
            
            value = node_data.get(self.metric)
            if value is None:
                return False
            
            # Calculate threshold for top p%
            sorted_vals = sorted(all_values[self.metric], reverse=True)
            k = int(len(sorted_vals) * self.percentile)
            if k >= len(sorted_vals):
                return False
            threshold = sorted_vals[k]
            return value >= threshold
        
        elif self.predicate_type == "layer_count":
            value = node_data.get("layer_count", 0)
            if self.operator == ">=":
                return value >= self.threshold
            elif self.operator == ">":
                return value > self.threshold
            elif self.operator == "<=":
                return value <= self.threshold
            elif self.operator == "<":
                return value < self.threshold
            elif self.operator == "=":
                return value == self.threshold
            return False
        
        return False


@dataclass(frozen=True)
class Consequent:
    """Represents a consequent predicate (right side of implication).
    
    Consequents are predicates on computed centrality metrics, either as
    threshold predicates or rank predicates.
    
    Attributes:
        metric: Metric name (e.g., "pagerank", "betweenness_centrality")
        predicate_type: Type of predicate ("threshold", "rank")
        threshold: Threshold value (for threshold predicates)
        operator: Comparison operator (">=", ">", "<=", "<", "=")
        rank: Rank threshold (for rank predicates, e.g., 20 for "rank <= 20")
        rank_operator: Rank comparison operator ("<=", "<", ">=", ">")
        layer: Optional layer restriction
    """
    
    metric: str
    predicate_type: str  # "threshold", "rank"
    threshold: Optional[float] = None
    operator: Optional[str] = None  # ">=", ">", "<=", "<", "="
    rank: Optional[int] = None
    rank_operator: Optional[str] = None  # "<=", "<", ">=", ">"
    layer: Optional[str] = None
    
    def to_dsl_string(self) -> str:
        """Convert to DSL-compatible string representation.
        
        Returns:
            String like "pagerank__gte(0.1)" or "pagerank__rank_lte(20)"
        """
        if self.predicate_type == "threshold":
            op_map = {">=": "gte", ">": "gt", "<=": "lte", "<": "lt", "=": "eq"}
            op_suffix = op_map.get(self.operator, "gte")
            return f"{self.metric}__{op_suffix}({self.threshold})"
        elif self.predicate_type == "rank":
            op_map = {">=": "gte", ">": "gt", "<=": "lte", "<": "lt", "=": "eq"}
            op_suffix = op_map.get(self.rank_operator, "lte")
            return f"{self.metric}__rank_{op_suffix}({self.rank})"
        else:
            return f"{self.metric}({self.threshold})"
    
    def evaluate(self, node_data: Dict[str, Any], all_values: Optional[Dict[str, List[float]]] = None) -> bool:
        """Evaluate predicate on a node's data.
        
        Args:
            node_data: Dictionary of node attributes and metrics
            all_values: Optional dict of metric_name -> list of all values (for rank)
            
        Returns:
            True if predicate is satisfied
        """
        if self.predicate_type == "threshold":
            value = node_data.get(self.metric)
            if value is None:
                return False
            
            if self.operator == ">=":
                return value >= self.threshold
            elif self.operator == ">":
                return value > self.threshold
            elif self.operator == "<=":
                return value <= self.threshold
            elif self.operator == "<":
                return value < self.threshold
            elif self.operator == "=":
                return value == self.threshold
            return False
        
        elif self.predicate_type == "rank":
            if all_values is None or self.metric not in all_values:
                return False
            
            value = node_data.get(self.metric)
            if value is None:
                return False
            
            # Calculate rank (1-indexed, higher value = lower rank number)
            sorted_vals = sorted(all_values[self.metric], reverse=True)
            try:
                rank = sorted_vals.index(value) + 1
            except ValueError:
                return False
            
            if self.rank_operator == "<=":
                return rank <= self.rank
            elif self.rank_operator == "<":
                return rank < self.rank
            elif self.rank_operator == ">=":
                return rank >= self.rank
            elif self.rank_operator == ">":
                return rank > self.rank
            elif self.rank_operator == "=":
                return rank == self.rank
            return False
        
        return False


@dataclass
class ClaimScore:
    """Statistical measures for a claim.
    
    Attributes:
        support: P(consequent | antecedent) - fraction of nodes satisfying both
        coverage: P(antecedent) - fraction of nodes satisfying antecedent
        n_antecedent: Number of nodes satisfying antecedent
        n_both: Number of nodes satisfying both
        n_total: Total number of nodes
    """
    
    support: float  # P(consequent | antecedent)
    coverage: float  # P(antecedent)
    n_antecedent: int
    n_both: int
    n_total: int
    
    def __post_init__(self):
        """Round floats for determinism."""
        self.support = round(self.support, 6)
        self.coverage = round(self.coverage, 6)


@dataclass
class Claim:
    """Complete inductive claim with metadata and provenance.
    
    A claim represents a discovered implication of the form:
        antecedent -> consequent
    
    For example: "degree >= 10 -> pagerank_rank <= 50"
    
    Attributes:
        antecedent: Left side of implication
        consequent: Right side of implication
        score: Statistical support and coverage
        claim_string: DSL-compatible claim string
        meta: Metadata including provenance
    """
    
    antecedent: Antecedent
    consequent: Consequent
    score: ClaimScore
    claim_string: str
    meta: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def support(self) -> float:
        """Support: P(consequent | antecedent)."""
        return self.score.support
    
    @property
    def coverage(self) -> float:
        """Coverage: P(antecedent)."""
        return self.score.coverage
    
    def counterexample(self, network: Any, **kwargs) -> Optional[Any]:
        """Find counterexample for this claim using counterexample engine.
        
        This is a lazy integration point - counterexamples are only computed
        when explicitly requested.
        
        Args:
            network: py3plex multi_layer_network object
            **kwargs: Additional arguments for counterexample finder
            
        Returns:
            Counterexample object if found, None otherwise
        """
        from py3plex.counterexamples import find_counterexample
        from py3plex.counterexamples.types import Budget
        
        # Extract params from meta if available
        params = self.meta.get("params", {})
        layers = self.meta.get("layers")
        seed = kwargs.get("seed", self.meta.get("provenance", {}).get("randomness", {}).get("seed", 42))
        
        budget = Budget(
            max_tests=kwargs.get("max_tests", 200),
            max_witness_size=kwargs.get("max_witness_size", 500),
        )
        
        try:
            return find_counterexample(
                network=network,
                claim_str=self.claim_string,
                params=params,
                layers=layers,
                seed=seed,
                find_minimal=kwargs.get("find_minimal", True),
                budget=budget,
                initial_radius=kwargs.get("initial_radius", 2),
            )
        except Exception:
            # Counterexample not found or engine error
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to JSON-serializable dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "claim_string": self.claim_string,
            "antecedent": {
                "metric": self.antecedent.metric,
                "predicate_type": self.antecedent.predicate_type,
                "threshold": self.antecedent.threshold,
                "operator": self.antecedent.operator,
                "percentile": self.antecedent.percentile,
                "layer": self.antecedent.layer,
            },
            "consequent": {
                "metric": self.consequent.metric,
                "predicate_type": self.consequent.predicate_type,
                "threshold": self.consequent.threshold,
                "operator": self.consequent.operator,
                "rank": self.consequent.rank,
                "rank_operator": self.consequent.rank_operator,
                "layer": self.consequent.layer,
            },
            "score": {
                "support": self.score.support,
                "coverage": self.score.coverage,
                "n_antecedent": self.score.n_antecedent,
                "n_both": self.score.n_both,
                "n_total": self.score.n_total,
            },
            "meta": self.meta,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Claim({self.claim_string}, "
            f"support={self.support:.3f}, coverage={self.coverage:.3f})"
        )
