"""
Algorithms Service - Execute graph algorithms with progress tracking.

Provides non-blocking execution of py3plex algorithms with cancellation
support and progress updates using Qt's threading mechanisms.
"""

from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import networkx as nx

from .logger import get_logger

logger = get_logger()


class AlgorithmCategory(Enum):
    """Categories of available algorithms."""
    CENTRALITY = "Centrality"
    COMMUNITY = "Community Detection"
    LAYOUT = "Layout"
    METRICS = "Metrics"
    ANALYSIS = "Analysis"


@dataclass
class AlgorithmInfo:
    """Information about an available algorithm."""
    id: str
    name: str
    category: AlgorithmCategory
    description: str
    parameters: Dict[str, Any]
    min_nodes: int = 1
    max_nodes: int = 1000000


class AlgorithmsService:
    """Service for running graph algorithms."""

    # Registry of available algorithms
    ALGORITHMS: Dict[str, AlgorithmInfo] = {
        "degree_centrality": AlgorithmInfo(
            id="degree_centrality",
            name="Degree Centrality",
            category=AlgorithmCategory.CENTRALITY,
            description="Compute degree centrality for all nodes",
            parameters={},
        ),
        "betweenness_centrality": AlgorithmInfo(
            id="betweenness_centrality",
            name="Betweenness Centrality",
            category=AlgorithmCategory.CENTRALITY,
            description="Compute betweenness centrality (may be slow for large graphs)",
            parameters={
                "normalized": {"type": "bool", "default": True},
                "endpoints": {"type": "bool", "default": False},
            },
            max_nodes=5000,  # Can be slow
        ),
        "closeness_centrality": AlgorithmInfo(
            id="closeness_centrality",
            name="Closeness Centrality",
            category=AlgorithmCategory.CENTRALITY,
            description="Compute closeness centrality for all nodes",
            parameters={},
            max_nodes=5000,
        ),
        "louvain": AlgorithmInfo(
            id="louvain",
            name="Louvain Community Detection",
            category=AlgorithmCategory.COMMUNITY,
            description="Detect communities using Louvain method",
            parameters={
                "resolution": {"type": "float", "default": 1.0, "min": 0.1, "max": 10.0},
            },
        ),
        "spring_layout": AlgorithmInfo(
            id="spring_layout",
            name="Spring Layout (Force-Directed)",
            category=AlgorithmCategory.LAYOUT,
            description="Position nodes using Fruchterman-Reingold force-directed algorithm",
            parameters={
                "k": {"type": "float", "default": None, "description": "Optimal distance between nodes"},
                "iterations": {"type": "int", "default": 50, "min": 10, "max": 1000},
            },
        ),
        "kamada_kawai": AlgorithmInfo(
            id="kamada_kawai",
            name="Kamada-Kawai Layout",
            category=AlgorithmCategory.LAYOUT,
            description="Position nodes using Kamada-Kawai path-length cost-function",
            parameters={},
            max_nodes=1000,  # Can be slow for large graphs
        ),
    }

    def __init__(self):
        """Initialize algorithms service."""
        self._running = False
        self._cancel_requested = False

    def get_algorithms(
        self,
        category: Optional[AlgorithmCategory] = None
    ) -> List[AlgorithmInfo]:
        """Get list of available algorithms."""
        if category:
            return [
                algo for algo in self.ALGORITHMS.values()
                if algo.category == category
            ]
        return list(self.ALGORITHMS.values())

    def get_algorithm(self, algorithm_id: str) -> Optional[AlgorithmInfo]:
        """Get algorithm info by ID."""
        return self.ALGORITHMS.get(algorithm_id)

    def can_run(self, algorithm_id: str, num_nodes: int) -> tuple[bool, str]:
        """
        Check if algorithm can run on a graph.
        
        Returns:
            (can_run, message)
        """
        algo = self.get_algorithm(algorithm_id)
        if not algo:
            return False, "Algorithm not found"

        if num_nodes < algo.min_nodes:
            return False, f"Graph too small (minimum {algo.min_nodes} nodes)"

        if num_nodes > algo.max_nodes:
            return False, f"Graph too large (maximum {algo.max_nodes} nodes)"

        return True, ""

    def run_algorithm(
        self,
        graph: nx.Graph,
        algorithm_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run an algorithm on a graph.
        
        Args:
            graph: NetworkX graph
            algorithm_id: ID of algorithm to run
            parameters: Algorithm parameters
            progress_callback: Optional callback(percent, message)
            
        Returns:
            Results dictionary or None on error
        """
        try:
            self._running = True
            self._cancel_requested = False

            algo = self.get_algorithm(algorithm_id)
            if not algo:
                raise ValueError(f"Unknown algorithm: {algorithm_id}")

            # Check if can run
            can_run, msg = self.can_run(algorithm_id, graph.number_of_nodes())
            if not can_run:
                raise ValueError(msg)

            logger.info(f"Running algorithm: {algo.name}")

            if progress_callback:
                progress_callback(0, f"Running {algo.name}...")

            # Merge default parameters
            params = parameters or {}
            for param_name, param_info in algo.parameters.items():
                if param_name not in params:
                    params[param_name] = param_info.get("default")

            # Run algorithm based on ID
            result = self._execute_algorithm(graph, algorithm_id, params, progress_callback)

            if self._cancel_requested:
                logger.info("Algorithm cancelled by user")
                if progress_callback:
                    progress_callback(0, "Cancelled")
                return None

            if progress_callback:
                progress_callback(100, "Complete")

            logger.info(f"Algorithm completed: {algo.name}")
            return result

        except Exception as e:
            logger.error(f"Error running algorithm: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return None
        finally:
            self._running = False
            self._cancel_requested = False

    def _execute_algorithm(
        self,
        graph: nx.Graph,
        algorithm_id: str,
        params: Dict[str, Any],
        progress_callback: Optional[Callable[[int, str], None]]
    ) -> Dict[str, Any]:
        """Execute the actual algorithm."""

        if algorithm_id == "degree_centrality":
            if progress_callback:
                progress_callback(50, "Computing degree centrality...")
            centrality = nx.degree_centrality(graph)
            return {"centrality": centrality, "type": "degree"}

        elif algorithm_id == "betweenness_centrality":
            if progress_callback:
                progress_callback(30, "Computing betweenness centrality...")
            centrality = nx.betweenness_centrality(
                graph,
                normalized=params.get("normalized", True),
                endpoints=params.get("endpoints", False)
            )
            return {"centrality": centrality, "type": "betweenness"}

        elif algorithm_id == "closeness_centrality":
            if progress_callback:
                progress_callback(50, "Computing closeness centrality...")
            centrality = nx.closeness_centrality(graph)
            return {"centrality": centrality, "type": "closeness"}

        elif algorithm_id == "louvain":
            if progress_callback:
                progress_callback(30, "Running Louvain algorithm...")
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(
                    graph,
                    resolution=params.get("resolution", 1.0)
                )
                if progress_callback:
                    progress_callback(80, "Computing community statistics...")
                num_communities = len(set(communities.values()))
                return {
                    "communities": communities,
                    "num_communities": num_communities,
                    "type": "louvain"
                }
            except ImportError:
                logger.warning("python-louvain not installed")
                return {
                    "error": "python-louvain package not installed",
                    "install": "pip install python-louvain"
                }

        elif algorithm_id == "spring_layout":
            if progress_callback:
                progress_callback(30, "Computing spring layout...")
            pos = nx.spring_layout(
                graph,
                k=params.get("k"),
                iterations=params.get("iterations", 50)
            )
            return {"positions": pos, "type": "spring"}

        elif algorithm_id == "kamada_kawai":
            if progress_callback:
                progress_callback(30, "Computing Kamada-Kawai layout...")
            pos = nx.kamada_kawai_layout(graph)
            return {"positions": pos, "type": "kamada_kawai"}

        else:
            raise ValueError(f"Algorithm execution not implemented: {algorithm_id}")

    def cancel(self) -> None:
        """Request cancellation of running algorithm."""
        if self._running:
            self._cancel_requested = True
            logger.info("Algorithm cancellation requested")

    def is_running(self) -> bool:
        """Check if an algorithm is currently running."""
        return self._running


# Singleton instance
_algorithms_service: Optional[AlgorithmsService] = None


def get_algorithms_service() -> AlgorithmsService:
    """Get the global algorithms service instance."""
    global _algorithms_service
    if _algorithms_service is None:
        _algorithms_service = AlgorithmsService()
    return _algorithms_service
