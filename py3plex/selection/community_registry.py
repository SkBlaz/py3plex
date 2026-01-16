"""Registry of community detection algorithms for AutoCommunity."""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .capabilities import CapabilitiesReport, AlgorithmInfo

logger = logging.getLogger(__name__)


@dataclass
class CandidateSpec:
    """Specification for a candidate algorithm + params combination.
    
    Attributes:
        name: Algorithm name
        callable: Algorithm callable
        params: Parameter dictionary
        supports_multilayer: Whether algorithm supports multilayer networks
        seed_param_name: Name of seed parameter (if any)
        contestant_id: Unique ID for this candidate
    """
    
    name: str
    callable: Callable
    params: Dict[str, Any]
    supports_multilayer: bool = False
    seed_param_name: Optional[str] = None
    contestant_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate contestant ID if not provided."""
        if self.contestant_id is None:
            self.contestant_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique contestant ID from name and params."""
        # Sort params for stable hash
        param_str = ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        if param_str:
            return f"{self.name}:{param_str}"
        else:
            return self.name


class CommunityRegistry:
    """Registry of community detection algorithm candidates."""
    
    # Default parameter grids for algorithms
    DEFAULT_PARAM_GRIDS = {
        "gamma": [0.8, 1.0, 1.2],
        "resolution": [0.8, 1.0, 1.2],
        "omega": [0.0, 0.1, 0.2],
        "coupling": [0.0, 0.1, 0.2],
        "lambda": [0.0, 0.1, 0.2],
        "n_blocks": [2, 3, 4, 5],
        "B_min": [2],
        "B_max": [8],
        "mode": ["shared_blocks", "coupled"],
    }
    
    # Smaller grids for fast mode
    FAST_PARAM_GRIDS = {
        "gamma": [1.0],
        "resolution": [1.0],
        "omega": [0.1],
        "coupling": [0.1],
        "lambda": [0.1],
        "n_blocks": [3],
        "B_min": [2],
        "B_max": [5],
        "mode": ["shared_blocks"],
    }
    
    def __init__(self, capabilities: CapabilitiesReport):
        """Initialize registry from capabilities report.
        
        Args:
            capabilities: CapabilitiesReport from scanner
        """
        self.capabilities = capabilities
        self.algorithms = capabilities.algorithms_found
        self.candidates: List[CandidateSpec] = []
    
    def build_candidate_set(
        self,
        is_multilayer: bool,
        fast_mode: bool = True,
        max_candidates: int = 10,
    ) -> List[CandidateSpec]:
        """Build candidate set based on network type.
        
        Args:
            is_multilayer: Whether network is multilayer
            fast_mode: Use smaller parameter grids
            max_candidates: Maximum number of candidates
        
        Returns:
            List of CandidateSpec objects
        """
        self.candidates = []
        
        # Select algorithms based on network type
        if is_multilayer:
            # Prefer multilayer algorithms
            priority_algos = [
                "multilayer_leiden",
                "leiden_multilayer",
                "multilayer_louvain",
                "louvain_multilayer",
                "sbm_fit",
                "fit_multilayer_sbm",
            ]
        else:
            # Prefer single-layer algorithms
            priority_algos = [
                "leiden_multilayer",  # Works on both
                "multilayer_leiden",
                "louvain_multilayer",
                "multilayer_louvain",
                "sbm_fit",
            ]
        
        # Add candidates from priority algorithms
        for algo_name in priority_algos:
            if algo_name in self.algorithms:
                self._add_candidates_for_algorithm(
                    algo_name,
                    self.algorithms[algo_name],
                    fast_mode=fast_mode
                )
        
        # If we don't have enough, add more
        if len(self.candidates) < max_candidates:
            for algo_name, algo_info in self.algorithms.items():
                if algo_name not in priority_algos:
                    self._add_candidates_for_algorithm(
                        algo_name,
                        algo_info,
                        fast_mode=fast_mode
                    )
                
                if len(self.candidates) >= max_candidates:
                    break
        
        # Trim to max_candidates
        self.candidates = self.candidates[:max_candidates]
        
        logger.info(f"Built candidate set with {len(self.candidates)} candidates")
        return self.candidates
    
    def _add_candidates_for_algorithm(
        self,
        algo_name: str,
        algo_info: AlgorithmInfo,
        fast_mode: bool = True
    ):
        """Add candidates for a specific algorithm with parameter grid.
        
        Args:
            algo_name: Algorithm name
            algo_info: AlgorithmInfo from scanner
            fast_mode: Use smaller parameter grids
        """
        param_grids = self.FAST_PARAM_GRIDS if fast_mode else self.DEFAULT_PARAM_GRIDS
        
        # Detect which parameters this algorithm supports
        params_to_grid = {}
        for param_name in algo_info.params:
            if param_name in param_grids:
                params_to_grid[param_name] = param_grids[param_name]
        
        # Generate combinations
        if not params_to_grid:
            # No gridable params - just use default
            candidate = CandidateSpec(
                name=algo_name,
                callable=algo_info.callable,
                params={},
                supports_multilayer=algo_info.supports_multilayer,
                seed_param_name=algo_info.seed_param_name,
            )
            self.candidates.append(candidate)
        else:
            # Generate grid combinations
            param_combinations = self._generate_param_combinations(params_to_grid)
            
            for param_combo in param_combinations:
                candidate = CandidateSpec(
                    name=algo_name,
                    callable=algo_info.callable,
                    params=param_combo,
                    supports_multilayer=algo_info.supports_multilayer,
                    seed_param_name=algo_info.seed_param_name,
                )
                self.candidates.append(candidate)
    
    def _generate_param_combinations(
        self,
        param_grids: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters.
        
        Args:
            param_grids: Dict of param_name -> list of values
        
        Returns:
            List of parameter dictionaries
        """
        if not param_grids:
            return [{}]
        
        # Recursive generation
        param_names = list(param_grids.keys())
        first_param = param_names[0]
        rest_params = {k: v for k, v in param_grids.items() if k != first_param}
        
        rest_combinations = self._generate_param_combinations(rest_params)
        
        all_combinations = []
        for value in param_grids[first_param]:
            for rest_combo in rest_combinations:
                combo = {first_param: value, **rest_combo}
                all_combinations.append(combo)
        
        return all_combinations
    
    def get_candidate_by_id(self, contestant_id: str) -> Optional[CandidateSpec]:
        """Get candidate by contestant ID.
        
        Args:
            contestant_id: Contestant ID
        
        Returns:
            CandidateSpec or None
        """
        for candidate in self.candidates:
            if candidate.contestant_id == contestant_id:
                return candidate
        return None


def build_registry_from_capabilities(
    capabilities: CapabilitiesReport,
    is_multilayer: bool,
    fast_mode: bool = True,
    max_candidates: int = 10,
) -> Tuple[CommunityRegistry, List[CandidateSpec]]:
    """Convenience function to build registry and candidates.
    
    Args:
        capabilities: CapabilitiesReport from scanner
        is_multilayer: Whether network is multilayer
        fast_mode: Use smaller parameter grids
        max_candidates: Maximum number of candidates
    
    Returns:
        Tuple of (CommunityRegistry, List[CandidateSpec])
    """
    registry = CommunityRegistry(capabilities)
    candidates = registry.build_candidate_set(
        is_multilayer=is_multilayer,
        fast_mode=fast_mode,
        max_candidates=max_candidates,
    )
    return registry, candidates
