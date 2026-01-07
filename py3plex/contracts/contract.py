"""Main Robustness contract class with sensible defaults."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from .predicates import Predicate, JaccardAtK, KendallTau, PartitionVI, PartitionARI


@dataclass
class Budget:
    """Resource budget for contract evaluation.
    
    Attributes:
        max_seconds: Maximum execution time in seconds
        max_memory_mb: Maximum memory usage in MB (None = no limit)
    """
    max_seconds: float = 10.0
    max_memory_mb: Optional[float] = None


@dataclass
class Robustness:
    """Robustness contract with sensible defaults.
    
    This contract ensures that query conclusions are stable under structural
    perturbations. All parameters have sensible defaults that make 1-line
    usage possible while preserving explicit control.
    
    **Minimal Usage** (all defaults)::
    
        Q.nodes().compute("pagerank").top_k(20).contract(Robustness()).execute(net)
    
    **Default Inference Rules**:
    
    - **Perturbation**: edge_drop (layer-aware)
    - **p_max**: 0.10 (10% edge drop), or 0.05 if graph is tiny (E < 20)
    - **grid**: [0.0, 0.05, 0.10] (always includes 0 and p_max)
    - **n_samples**: 30 (adaptive: 50 for small graphs with N<=100, E<=1000)
    - **seed**: 0 (deterministic by default for reproducibility)
    - **mode**: "soft" (returns ContractResult on failure)
    - **repair**: True (enabled by default)
    - **tie_policy**: "break" (stable sort by node id/layer)
    - **budget**: 10 seconds, no memory limit
    
    **Auto-Predicate Selection** (based on conclusion type):
    
    - Top-k or set-like: JaccardAtK(k) >= 0.85
    - Ranking (order_by): KendallTau >= 0.8
    - Community/partition: PartitionVI <= 0.25 (or ARI >= 0.8)
    
    Attributes:
        perturb: Perturbation type ("edge_drop", "node_drop", "rewire", "weight_noise")
        grid: List of perturbation strengths to test
        p_max: Maximum perturbation strength
        n_samples: Number of samples per perturbation strength
        seed: Random seed (None only if allow_nondeterminism=True)
        mode: "soft" (return ContractResult) or "hard" (raise on violation)
        allow_nondeterminism: Allow seed=None (default: False)
        budget: Resource budget
        repair: Enable repair mechanisms
        tie_policy: How to handle ties in rankings ("break", "undefined")
        predicates: List of predicates to evaluate (None = auto-infer)
        domain: Predicate domain semantics ("all_p_leq_pmax")
    
    Examples:
        >>> # Use all defaults
        >>> contract = Robustness()
        >>> 
        >>> # Override specific defaults
        >>> contract = Robustness(n_samples=100, p_max=0.2)
        >>> 
        >>> # Explicit predicates
        >>> contract = Robustness(
        ...     predicates=[JaccardAtK(k=10, threshold=0.9)]
        ... )
        >>> 
        >>> # Hard mode (raise on violation)
        >>> contract = Robustness(mode="hard")
    """
    
    # Perturbation config
    perturb: str = "edge_drop"
    grid: Optional[List[float]] = None
    p_max: Optional[float] = None
    
    # Sampling config
    n_samples: Optional[int] = None
    seed: Optional[int] = 0
    allow_nondeterminism: bool = False
    
    # Execution config
    mode: str = "soft"
    budget: Budget = field(default_factory=Budget)
    
    # Repair config
    repair: bool = True
    tie_policy: str = "break"
    
    # Predicate config
    predicates: Optional[List[Predicate]] = None
    domain: str = "all_p_leq_pmax"
    
    def __post_init__(self):
        """Validate parameters."""
        # Validate mode
        if self.mode not in ("soft", "hard"):
            raise ValueError(f"mode must be 'soft' or 'hard', got {self.mode}")
        
        # Validate tie_policy
        if self.tie_policy not in ("break", "undefined"):
            raise ValueError(f"tie_policy must be 'break' or 'undefined', got {self.tie_policy}")
        
        # Validate domain
        if self.domain not in ("all_p_leq_pmax", "exists_p_leq_pmax"):
            raise ValueError(f"domain must be 'all_p_leq_pmax' or 'exists_p_leq_pmax', got {self.domain}")
        
        # Validate perturbation type
        valid_perturbs = ("edge_drop", "node_drop", "rewire", "weight_noise")
        if self.perturb not in valid_perturbs:
            raise ValueError(f"perturb must be one of {valid_perturbs}, got {self.perturb}")
        
        # Validate seed/determinism
        if self.seed is None and not self.allow_nondeterminism:
            raise ValueError(
                "seed cannot be None when allow_nondeterminism=False. "
                "Either set seed to an integer or set allow_nondeterminism=True."
            )
        
        # Validate p_max
        if self.p_max is not None and not (0.0 <= self.p_max <= 1.0):
            raise ValueError(f"p_max must be in [0, 1], got {self.p_max}")
        
        # Validate grid
        if self.grid is not None:
            if not all(0.0 <= p <= 1.0 for p in self.grid):
                raise ValueError(f"All grid values must be in [0, 1], got {self.grid}")
            if 0.0 not in self.grid:
                raise ValueError("Grid must include 0.0 (baseline)")
        
        # Validate n_samples
        if self.n_samples is not None and self.n_samples < 1:
            raise ValueError(f"n_samples must be positive, got {self.n_samples}")
        
        # Ensure budget is a Budget object
        if not isinstance(self.budget, Budget):
            self.budget = Budget()
    
    def resolve_defaults(
        self,
        network: Any,
        conclusion_type: str,
        top_k: Optional[int] = None,
        metric: Optional[str] = None
    ) -> "Robustness":
        """Resolve defaults based on network and query context.
        
        This method creates a new Robustness instance with all defaults
        resolved to explicit values based on network characteristics and
        query structure.
        
        Args:
            network: Multilayer network object
            conclusion_type: Type of conclusion ("top_k", "ranking", "community")
            top_k: Value of k for top-k queries (if applicable)
            metric: Metric name being computed (if applicable)
            
        Returns:
            New Robustness instance with resolved defaults
        """
        # Get network stats
        n_nodes = len(list(network.get_nodes())) if hasattr(network, "get_nodes") else 0
        n_edges = len(list(network.get_edges())) if hasattr(network, "get_edges") else 0
        
        # Resolve p_max
        p_max = self.p_max
        if p_max is None:
            if n_edges < 20:
                p_max = 0.05  # Tiny graph: cap at 5%
            else:
                p_max = 0.10  # Default: 10%
        
        # Resolve grid
        grid = self.grid
        if grid is None:
            if n_edges < 20:
                grid = [0.0, 0.05]
            else:
                grid = [0.0, 0.05, p_max]
            # Deduplicate and sort
            grid = sorted(list(set(grid)))
        
        # Resolve n_samples (adaptive)
        n_samples = self.n_samples
        if n_samples is None:
            if n_nodes >= 500 or n_edges >= 5000:
                n_samples = 30  # Large graph: keep default
            elif n_nodes <= 100 and n_edges <= 1000:
                n_samples = 50  # Small graph: increase samples
            else:
                n_samples = 30  # Medium graph: default
        
        # Resolve predicates (auto-select based on conclusion type)
        predicates = self.predicates
        if predicates is None:
            if conclusion_type == "top_k" and top_k is not None:
                predicates = [JaccardAtK(k=top_k, threshold=0.85, metric=metric)]
            elif conclusion_type == "ranking":
                predicates = [KendallTau(threshold=0.8, tie_policy=self.tie_policy, metric=metric)]
            elif conclusion_type == "community":
                # Use VI by default (could also use ARI)
                predicates = [PartitionVI(threshold=0.25)]
            else:
                # Fallback: use Jaccard with k=20
                predicates = [JaccardAtK(k=20, threshold=0.85, metric=metric)]
        
        # Return new instance with resolved defaults
        return Robustness(
            perturb=self.perturb,
            grid=grid,
            p_max=p_max,
            n_samples=n_samples,
            seed=self.seed,
            allow_nondeterminism=self.allow_nondeterminism,
            mode=self.mode,
            budget=self.budget,
            repair=self.repair,
            tie_policy=self.tie_policy,
            predicates=predicates,
            domain=self.domain,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for provenance.
        
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "perturb": self.perturb,
            "grid": self.grid,
            "p_max": self.p_max,
            "n_samples": self.n_samples,
            "seed": self.seed,
            "allow_nondeterminism": self.allow_nondeterminism,
            "mode": self.mode,
            "budget": {
                "max_seconds": self.budget.max_seconds,
                "max_memory_mb": self.budget.max_memory_mb,
            },
            "repair": self.repair,
            "tie_policy": self.tie_policy,
            "predicates": [p.to_dict() for p in self.predicates] if self.predicates else None,
            "domain": self.domain,
        }
