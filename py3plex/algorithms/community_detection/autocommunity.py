"""AutoCommunity: Multi-objective, uncertainty-aware meta-algorithm for community detection.

This module implements a principled meta-algorithm for selecting and synthesizing
community structures in multilayer networks based on Pareto dominance, uncertainty
quantification, and null-model calibration.

Core Design Principles:
- Multi-objective evaluation (no single scalar optimization)
- Uncertainty as first-class citizen (metrics, partitions, node memberships)
- Null-model calibration mandatory
- Multilayer-native metrics and stability
- Reproducible and inspectable decisions

Example Usage:
    >>> from py3plex.algorithms.community_detection import AutoCommunity
    >>> from py3plex.core import multinet
    >>> 
    >>> # Create network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> # ... add nodes and edges ...
    >>> 
    >>> # Run AutoCommunity with full pipeline
    >>> result = (
    ...     AutoCommunity()
    ...       .candidates("louvain", "leiden", "infomap")
    ...       .metrics("modularity", "stability", "coverage")
    ...       .uq(method="perturbation", n_samples=50)
    ...       .null_model(type="configuration", samples=50)
    ...       .pareto()
    ...       .execute(net)
    ... )
    >>> 
    >>> # Access results
    >>> print(result.explain())
    >>> partition = result.consensus_partition
    >>> confidence = result.community_stats.node_confidence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
import warnings

import numpy as np
import pandas as pd

from py3plex.exceptions import AlgorithmError
from py3plex.uncertainty.partition import CommunityDistribution


@dataclass
class CommunityStats:
    """Statistics about community structure with uncertainty quantification.
    
    Attributes:
        n_communities: Number of communities
        community_sizes: List of community sizes
        community_sizes_ci: Confidence intervals for sizes
        node_confidence: Per-node confidence scores (dict: node -> float)
        node_entropy: Per-node entropy scores (dict: node -> float)
        node_margin: Per-node margin scores (dict: node -> float)
        membership_probs: Per-node membership probabilities (if available)
        co_assignment_matrix: Co-assignment matrix (if computed)
        stability_score: Overall partition stability
        coverage: Fraction of nodes assigned to non-singleton communities
        orphan_nodes: List of nodes in singleton communities
    """
    
    n_communities: int
    community_sizes: List[int]
    community_sizes_ci: Optional[Tuple[List[float], List[float]]] = None
    node_confidence: Optional[Dict[Any, float]] = None
    node_entropy: Optional[Dict[Any, float]] = None
    node_margin: Optional[Dict[Any, float]] = None
    membership_probs: Optional[Dict[Any, np.ndarray]] = None
    co_assignment_matrix: Optional[np.ndarray] = None
    stability_score: Optional[float] = None
    coverage: Optional[float] = None
    orphan_nodes: Optional[List[Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'n_communities': self.n_communities,
            'community_sizes': self.community_sizes,
            'community_sizes_ci': self.community_sizes_ci,
            'stability_score': self.stability_score,
            'coverage': self.coverage,
            'n_orphan_nodes': len(self.orphan_nodes) if self.orphan_nodes else 0,
        }


@dataclass
class AutoCommunityResult:
    """Result of AutoCommunity meta-algorithm.
    
    Immutable result container with comprehensive provenance and diagnostics.
    
    Attributes:
        algorithms_tested: List of algorithm names tested
        pareto_front: List of non-dominated algorithm IDs
        selected: ID of selected algorithm (or "consensus")
        consensus_partition: Final partition (dict: (node, layer) -> community_id)
        community_stats: Structured statistics with uncertainty
        evaluation_matrix: DataFrame with all metrics for all algorithms
        diagnostics: Per-algorithm diagnostics
        provenance: Full provenance information
        null_model_results: Null model comparison results (if enabled)
        graph_regime: Network regime features
    """
    
    algorithms_tested: List[str]
    pareto_front: List[str]
    selected: str
    consensus_partition: Dict[Tuple[Any, Any], int]
    community_stats: CommunityStats
    evaluation_matrix: pd.DataFrame
    diagnostics: Dict[str, Any]
    provenance: Dict[str, Any]
    null_model_results: Optional[Dict[str, Any]] = None
    graph_regime: Optional[Dict[str, float]] = None
    
    def explain(self, n: int = 5) -> str:
        """Generate natural language explanation of selection rationale.
        
        Args:
            n: Maximum number of reasons to include
        
        Returns:
            Human-readable explanation
        """
        reasons = []
        
        # Pareto front information
        if len(self.pareto_front) > 1:
            reasons.append(
                f"Multiple algorithms ({len(self.pareto_front)}) were non-dominated, "
                f"so consensus was computed"
            )
        elif len(self.pareto_front) == 1:
            reasons.append(f"Algorithm '{self.selected}' dominated all others")
        
        # Null model significance
        if self.null_model_results:
            z_scores = self.null_model_results.get('z_scores', {})
            if z_scores:
                max_z = max(z_scores.values()) if z_scores else 0
                if max_z > 3.0:
                    reasons.append(
                        f"Community structure is highly significant (Z-score > 3.0) "
                        f"compared to null models"
                    )
                elif max_z < 2.0:
                    reasons.append(
                        f"Warning: Weak signal relative to null models (Z-score < 2.0)"
                    )
        
        # Uncertainty information
        if self.community_stats.stability_score:
            stability = self.community_stats.stability_score
            if stability > 0.8:
                reasons.append(f"High partition stability ({stability:.3f})")
            elif stability < 0.5:
                reasons.append(f"Warning: Low stability ({stability:.3f})")
        
        # Coverage
        if self.community_stats.coverage:
            coverage = self.community_stats.coverage
            if coverage > 0.9:
                reasons.append(f"High coverage ({coverage:.3f})")
            elif coverage < 0.7:
                reasons.append(f"Warning: Many orphan nodes (coverage={coverage:.3f})")
        
        # Graph regime
        if self.graph_regime:
            if self.graph_regime.get('degree_heterogeneity', 0) > 2.0:
                reasons.append("High degree heterogeneity detected")
            if self.graph_regime.get('coupling_strength', 0) > 0.5:
                reasons.append("Strong inter-layer coupling")
        
        # Limit to n reasons
        reasons = reasons[:n]
        
        explanation = f"Selection: '{self.selected}'\n\nRationale:\n"
        for i, reason in enumerate(reasons, 1):
            explanation += f"  {i}. {reason}\n"
        
        if not reasons:
            explanation += "  (No specific reasons available)\n"
        
        return explanation.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'algorithms_tested': self.algorithms_tested,
            'pareto_front': self.pareto_front,
            'selected': self.selected,
            'consensus_partition': {str(k): v for k, v in self.consensus_partition.items()},
            'community_stats': self.community_stats.to_dict(),
            'evaluation_matrix': self.evaluation_matrix.to_dict(orient='records'),
            'diagnostics': self.diagnostics,
            'provenance': self.provenance,
            'null_model_results': self.null_model_results,
            'graph_regime': self.graph_regime,
        }
    
    def to_pandas(self) -> pd.DataFrame:
        """Convert community assignments to pandas DataFrame.
        
        Returns:
            DataFrame with columns: node, layer, community, confidence, entropy
        """
        rows = []
        for (node, layer), comm_id in self.consensus_partition.items():
            row = {
                'node': node,
                'layer': layer,
                'community': comm_id,
            }
            
            # Add uncertainty metrics if available
            if self.community_stats.node_confidence:
                row['confidence'] = self.community_stats.node_confidence.get((node, layer), None)
            if self.community_stats.node_entropy:
                row['entropy'] = self.community_stats.node_entropy.get((node, layer), None)
            if self.community_stats.node_margin:
                row['margin'] = self.community_stats.node_margin.get((node, layer), None)
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def __repr__(self) -> str:
        n_comms = self.community_stats.n_communities
        n_algos = len(self.algorithms_tested)
        return (
            f"AutoCommunityResult(selected='{self.selected}', "
            f"n_communities={n_comms}, algorithms_tested={n_algos})"
        )


class AutoCommunity:
    """Multi-objective, uncertainty-aware community detection meta-algorithm.
    
    Builder-style API for configuring and executing principled community detection
    with Pareto selection, uncertainty quantification, and null-model calibration.
    
    Example:
        >>> result = (
        ...     AutoCommunity()
        ...       .candidates("louvain", "leiden")
        ...       .metrics("modularity", "stability", "coverage")
        ...       .uq(method="perturbation", n_samples=50)
        ...       .null_model(type="configuration", samples=50)
        ...       .pareto()
        ...       .execute(network)
        ... )
    """
    
    def __init__(self):
        """Initialize AutoCommunity builder."""
        self._candidate_algorithms: List[str] = []
        self._metric_names: List[str] = []
        self._uq_config: Optional[Dict[str, Any]] = None
        self._null_config: Optional[Dict[str, Any]] = None
        self._use_pareto: bool = True
        self._seed: int = 0
        self._custom_metrics: List[Callable] = []
        self._custom_candidates: List[Dict[str, Any]] = []
        self._strategy: str = "default"
        self._racer_config: Optional[Dict[str, Any]] = None
    
    def candidates(self, *algorithms: str) -> AutoCommunity:
        """Specify candidate algorithms to evaluate.
        
        Args:
            *algorithms: Algorithm names ("louvain", "leiden", "sbm", "dc_sbm", "infomap")
        
        Returns:
            Self for chaining
        """
        self._candidate_algorithms = list(algorithms)
        return self
    
    def metrics(self, *metric_names: str) -> AutoCommunity:
        """Specify evaluation metrics.
        
        Args:
            *metric_names: Metric names ("modularity", "stability", "coverage", 
                          "sbm_log_likelihood", "sbm_mdl")
        
        Returns:
            Self for chaining
        """
        self._metric_names = list(metric_names)
        return self
    
    def uq(
        self,
        method: str = "perturbation",
        n_samples: int = 50,
        **kwargs
    ) -> AutoCommunity:
        """Enable uncertainty quantification.
        
        Args:
            method: UQ method ("perturbation", "bootstrap", "seed")
            n_samples: Number of samples for UQ
            **kwargs: Additional UQ configuration
        
        Returns:
            Self for chaining
        """
        self._uq_config = {
            'method': method,
            'n_samples': n_samples,
            **kwargs
        }
        return self
    
    def null_model(
        self,
        type: str = "configuration",
        samples: int = 50,
        **kwargs
    ) -> AutoCommunity:
        """Enable null-model calibration.
        
        Args:
            type: Null model type ("configuration", "erdos_renyi", "edge_swap")
            samples: Number of null model samples
            **kwargs: Additional null model configuration
        
        Returns:
            Self for chaining
        """
        self._null_config = {
            'type': type,
            'samples': samples,
            **kwargs
        }
        return self
    
    def pareto(self, enabled: bool = True) -> AutoCommunity:
        """Enable/disable Pareto selection.
        
        Args:
            enabled: Whether to use Pareto dominance (default: True)
        
        Returns:
            Self for chaining
        """
        self._use_pareto = enabled
        return self
    
    def seed(self, seed: int) -> AutoCommunity:
        """Set random seed for reproducibility.
        
        Args:
            seed: Random seed
        
        Returns:
            Self for chaining
        """
        self._seed = seed
        return self
    
    def strategy(
        self,
        strategy: str = "default",
        **racer_config
    ) -> AutoCommunity:
        """Set selection strategy.
        
        Args:
            strategy: Selection strategy ("default", "successive_halving")
            **racer_config: Configuration for racing strategy (if applicable)
                For "successive_halving":
                - eta: int = 3 (elimination factor)
                - rounds: int | None = None (auto-compute if None)
                - budget0: dict | None = None (initial budget)
                - budget_growth: float | None = None (budget scaling, default=eta)
                - early_stop: bool = True
                - tie_mode: str = "keep_more" (or "underdetermined")
                - utility_method: str = "mean_minus_std"
                - utility_lambda: float = 1.0
                - metric_weights: dict | None = None
        
        Returns:
            Self for chaining
        
        Examples:
            >>> # Default Pareto strategy
            >>> AutoCommunity().strategy("default")
            >>> 
            >>> # Successive Halving with custom parameters
            >>> AutoCommunity().strategy(
            ...     "successive_halving",
            ...     eta=3,
            ...     budget0={"max_iter": 10, "uq_samples": 20},
            ...     utility_method="mean_minus_std",
            ... )
        """
        if strategy not in ("default", "successive_halving"):
            raise ValueError(
                f"Invalid strategy '{strategy}'. "
                f"Supported: 'default', 'successive_halving'"
            )
        
        self._strategy = strategy
        self._racer_config = racer_config if racer_config else None
        return self
    
    def execute(self, network: Any) -> AutoCommunityResult:
        """Execute AutoCommunity meta-algorithm.
        
        Args:
            network: Multilayer network to analyze
        
        Returns:
            AutoCommunityResult with selection, consensus, and diagnostics
        
        Raises:
            AlgorithmError: If configuration is invalid or execution fails
        """
        # Validate configuration
        if not self._candidate_algorithms:
            raise AlgorithmError(
                "No candidate algorithms specified",
                suggestions=["Call .candidates() with algorithm names"]
            )
        
        if not self._metric_names:
            raise AlgorithmError(
                "No metrics specified",
                suggestions=["Call .metrics() with metric names"]
            )
        
        # Route to appropriate strategy
        if self._strategy == "successive_halving":
            # Use Successive Halving racer
            from py3plex.algorithms.community_detection.autocommunity_executor import (
                execute_autocommunity_sh
            )
            
            result = execute_autocommunity_sh(
                network=network,
                candidate_algorithms=self._candidate_algorithms,
                metric_names=self._metric_names,
                uq_config=self._uq_config,
                seed=self._seed,
                racer_config=self._racer_config,
            )
        else:
            # Default: use Pareto selection
            from py3plex.algorithms.community_detection.autocommunity_executor import (
                execute_autocommunity
            )
            
            result = execute_autocommunity(
                network=network,
                candidate_algorithms=self._candidate_algorithms,
                metric_names=self._metric_names,
                uq_config=self._uq_config,
                null_config=self._null_config,
                use_pareto=self._use_pareto,
                seed=self._seed,
                custom_metrics=self._custom_metrics,
                custom_candidates=self._custom_candidates,
            )
        
        return result
