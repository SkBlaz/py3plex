"""
Scikit-learn style pipeline abstraction for py3plex.

This module provides a Pipeline class that enables chaining multiple network
analysis steps together in a scikit-learn style API. This is useful for
creating reproducible workflows and prototyping different analysis strategies.

Public API:
    - Pipeline: Main class for chaining pipeline steps
    - PipelineStep: Abstract base class for custom pipeline steps
    - LoadStep: Load network from file or generate random network
    - AggregateLayers: Aggregate edges across layers
    - LeidenMultilayer: Community detection using Leiden algorithm
    - LouvainCommunity: Community detection using Louvain algorithm
    - ComputeStats: Compute basic network statistics
    - FilterNodes: Filter nodes based on conditions
    - SaveNetwork: Save network to file

Example:
    >>> from py3plex.pipeline import Pipeline, LoadStep, AggregateLayers
    >>> from py3plex.pipeline import LeidenMultilayer
    >>> 
    >>> pipe = Pipeline([
    ...     ("load", LoadStep(path="network.graphml")),
    ...     ("aggregate", AggregateLayers()),
    ...     ("community", LeidenMultilayer(resolution=1.0)),
    ... ])
    >>> result = pipe.run()
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod
import networkx as nx

from py3plex.core import multinet, random_generators
from py3plex.logging_config import get_logger

logger = get_logger(__name__)

__all__ = [
    "Pipeline",
    "PipelineStep",
    "LoadStep",
    "AggregateLayers",
    "LeidenMultilayer",
    "LouvainCommunity",
    "ComputeStats",
    "FilterNodes",
    "SaveNetwork",
]


class PipelineStep(ABC):
    """
    Abstract base class for pipeline steps.
    
    All pipeline steps must implement the `transform` method which takes
    a network or result from the previous step and returns a transformed result.
    """
    
    @abstractmethod
    def transform(self, data: Any) -> Any:
        """
        Transform the input data.
        
        Args:
            data: Input data from previous step (or None for first step)
            
        Returns:
            Any: Transformed data to pass to next step
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """
        Get parameters for this step.
        
        Returns:
            Dictionary of parameter names and values
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def set_params(self, **params) -> 'PipelineStep':
        """
        Set parameters for this step.
        
        Args:
            **params: Parameters to set
            
        Returns:
            Self for method chaining
        """
        for key, value in params.items():
            setattr(self, key, value)
        return self


class Pipeline:
    """
    Pipeline for chaining network analysis steps.
    
    The Pipeline allows you to chain multiple steps together, where each step
    transforms the output of the previous step. The final step's output is
    returned when calling `run()`.
    
    Args:
        steps: List of (name, step) tuples where step is a PipelineStep
        
    Attributes:
        steps: List of named pipeline steps
        named_steps: Dictionary mapping step names to step objects
        
    Example:
        >>> pipe = Pipeline([
        ...     ("load", LoadStep(path="network.graphml")),
        ...     ("stats", ComputeStats()),
        ... ])
        >>> result = pipe.run()
    """
    
    def __init__(self, steps: List[Tuple[str, PipelineStep]]):
        """Initialize pipeline with steps."""
        self.steps = steps
        self.named_steps = {name: step for name, step in steps}
        self._validate_steps()
    
    def _validate_steps(self) -> None:
        """Validate that all steps are PipelineStep instances."""
        for name, step in self.steps:
            if not isinstance(step, PipelineStep):
                raise TypeError(
                    f"Step '{name}' must be a PipelineStep instance, "
                    f"got {type(step).__name__}"
                )
    
    def run(self) -> Any:
        """
        Run the pipeline by executing all steps in sequence.
        
        Returns:
            Output of the final step
            
        Example:
            >>> result = pipe.run()
        """
        logger.info(f"Starting pipeline with {len(self.steps)} step(s)")
        
        data = None
        for i, (name, step) in enumerate(self.steps):
            logger.info(f"Step {i+1}/{len(self.steps)}: {name}")
            data = step.transform(data)
            logger.debug(f"  Output type: {type(data).__name__}")
        
        logger.info("Pipeline completed successfully")
        return data
    
    def __repr__(self) -> str:
        """String representation of pipeline."""
        step_names = [name for name, _ in self.steps]
        return f"Pipeline(steps={step_names})"
    
    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """
        Get parameters for all steps in the pipeline.
        
        Args:
            deep: If True, return parameters for each step as well
            
        Returns:
            Dictionary of parameters
        """
        if not deep:
            return {'steps': self.steps}
        
        params = {}
        for name, step in self.steps:
            step_params = step.get_params()
            for param_name, param_value in step_params.items():
                params[f"{name}__{param_name}"] = param_value
        
        return params


# ============================================================================
# Built-in Pipeline Steps
# ============================================================================


class LoadStep(PipelineStep):
    """
    Load a network from file or generate a random network.
    
    Args:
        path: Path to network file (mutually exclusive with generator)
        generator: Type of random generator ('random_er', 'random_ba', etc.)
        input_type: Type of input file ('graphml', 'gpickle', 'multiedgelist')
        directed: Whether network is directed (for generated networks)
        **generator_params: Additional parameters for network generator
        
    Example:
        >>> # Load from file
        >>> step = LoadStep(path="network.graphml")
        >>> 
        >>> # Generate random network
        >>> step = LoadStep(generator='random_er', num_nodes=100, 
        ...                 num_layers=3, edge_prob=0.1)
    """
    
    def __init__(
        self,
        path: Optional[str] = None,
        generator: Optional[str] = None,
        input_type: str = 'graphml',
        directed: bool = False,
        **generator_params
    ):
        """Initialize load step."""
        if path is None and generator is None:
            raise ValueError("Either 'path' or 'generator' must be specified")
        if path is not None and generator is not None:
            raise ValueError("Cannot specify both 'path' and 'generator'")
        
        self.path = path
        self.generator = generator
        self.input_type = input_type
        self.directed = directed
        self.generator_params = generator_params
    
    def transform(self, data: Any) -> multinet.multi_layer_network:
        """Load or generate a network."""
        if self.path is not None:
            return self._load_from_file()
        else:
            return self._generate_network()
    
    def _load_from_file(self) -> multinet.multi_layer_network:
        """Load network from file."""
        logger.info(f"Loading network from {self.path}")
        network = multinet.multi_layer_network(directed=self.directed)
        
        if self.input_type == 'graphml':
            G = nx.read_graphml(self.path)
            network.core_network = G
            network.directed = G.is_directed()
        elif self.input_type == 'gpickle':
            network.load_network(self.path, input_type='gpickle')
        else:
            network.load_network(self.path, input_type=self.input_type)
        
        logger.info(
            f"  Loaded: {network.core_network.number_of_nodes()} nodes, "
            f"{network.core_network.number_of_edges()} edges"
        )
        return network
    
    def _generate_network(self) -> multinet.multi_layer_network:
        """Generate random network."""
        logger.info(f"Generating network: {self.generator}")
        
        if self.generator == 'random_er':
            network = random_generators.random_multilayer_ER(
                directed=self.directed,
                **self.generator_params
            )
        else:
            raise ValueError(f"Unknown generator: {self.generator}")
        
        logger.info(
            f"  Generated: {network.core_network.number_of_nodes()} nodes, "
            f"{network.core_network.number_of_edges()} edges"
        )
        return network


class AggregateLayers(PipelineStep):
    """
    Aggregate edges across multiple layers.
    
    Args:
        method: Aggregation method ('sum', 'mean', 'max')
        
    Example:
        >>> step = AggregateLayers(method='sum')
    """
    
    def __init__(self, method: str = 'sum'):
        """Initialize aggregation step."""
        if method not in ['sum', 'mean', 'max']:
            raise ValueError(f"method must be 'sum', 'mean', or 'max', got '{method}'")
        self.method = method
    
    def transform(self, data: multinet.multi_layer_network) -> multinet.multi_layer_network:
        """Aggregate network layers."""
        if not isinstance(data, multinet.multi_layer_network):
            raise TypeError(
                f"Expected multi_layer_network, got {type(data).__name__}"
            )
        
        logger.info(f"Aggregating layers using method: {self.method}")
        aggregated_nx = data.aggregate_edges(metric=self.method)
        
        # Create a new multi_layer_network with the aggregated graph
        result = multinet.multi_layer_network()
        result.core_network = aggregated_nx
        result.directed = aggregated_nx.is_directed()
        
        logger.info(
            f"  Aggregated: {result.core_network.number_of_nodes()} nodes, "
            f"{result.core_network.number_of_edges()} edges"
        )
        return result


class LeidenMultilayer(PipelineStep):
    """
    Detect communities using Leiden algorithm for multilayer networks.
    
    Args:
        interlayer_coupling: Coupling strength between layers (default: 1.0)
        resolution: Resolution parameter for modularity (default: 1.0)
        seed: Random seed for reproducibility (default: None)
        max_iter: Maximum number of iterations (default: 100)
        
    Example:
        >>> step = LeidenMultilayer(resolution=1.0, seed=42)
    """
    
    def __init__(
        self,
        interlayer_coupling: float = 1.0,
        resolution: float = 1.0,
        seed: Optional[int] = None,
        max_iter: int = 100
    ):
        """Initialize Leiden community detection step."""
        self.interlayer_coupling = interlayer_coupling
        self.resolution = resolution
        self.seed = seed
        self.max_iter = max_iter
    
    def transform(self, data: multinet.multi_layer_network) -> 'LeidenResult':
        """
        Detect communities in multilayer network.
        
        Args:
            data: Multilayer network to analyze
            
        Returns:
            LeidenResult: Object containing communities and modularity information
        """
        if not isinstance(data, multinet.multi_layer_network):
            raise TypeError(
                f"Expected multi_layer_network, got {type(data).__name__}"
            )
        
        from py3plex.algorithms.community_detection.leiden_multilayer import leiden_multilayer
        
        logger.info("Running Leiden community detection")
        result = leiden_multilayer(
            data,
            interlayer_coupling=self.interlayer_coupling,
            resolution=self.resolution,
            seed=self.seed,
            max_iter=self.max_iter
        )
        
        n_communities = len(set(result.communities.values()))
        logger.info(
            f"  Found {n_communities} communities "
            f"(modularity: {result.modularity:.4f})"
        )
        
        return result


class LouvainCommunity(PipelineStep):
    """
    Detect communities using Louvain algorithm.
    
    Note: The py3plex Louvain wrapper does not expose a resolution parameter.
    The resolution parameter is stored for reference but does not affect
    the algorithm. For resolution control, consider using the Louvain
    implementation from python-louvain directly.
    
    Args:
        resolution: Resolution parameter (stored for reference only)
        seed: Random seed for reproducibility (default: None)
        
    Example:
        >>> step = LouvainCommunity()
    """
    
    def __init__(self, resolution: float = 1.0, seed: Optional[int] = None):
        """Initialize Louvain community detection step."""
        self.resolution = resolution
        self.seed = seed
    
    def transform(self, data: multinet.multi_layer_network) -> Dict[str, Any]:
        """Detect communities using Louvain."""
        if not isinstance(data, multinet.multi_layer_network):
            raise TypeError(
                f"Expected multi_layer_network, got {type(data).__name__}"
            )
        
        from py3plex.algorithms.community_detection import community_wrapper
        
        logger.info("Running Louvain community detection")
        
        # Convert to undirected if needed
        G = (
            data.core_network.to_undirected()
            if data.core_network.is_directed()
            else data.core_network
        )
        
        # Note: py3plex's louvain_communities wrapper does not expose resolution parameter
        partition = community_wrapper.louvain_communities(G)
        communities = {str(node): int(comm) for node, comm in partition.items()}
        n_communities = len(set(communities.values()))
        
        logger.info(f"  Found {n_communities} communities")
        
        return {
            'algorithm': 'louvain',
            'num_communities': n_communities,
            'communities': communities,
        }


class ComputeStats(PipelineStep):
    """
    Compute basic network statistics.
    
    Args:
        include_layer_stats: Whether to compute layer-specific statistics
        
    Example:
        >>> step = ComputeStats(include_layer_stats=True)
    """
    
    def __init__(self, include_layer_stats: bool = True):
        """Initialize statistics computation step."""
        self.include_layer_stats = include_layer_stats
    
    def transform(self, data: multinet.multi_layer_network) -> Dict[str, Any]:
        """Compute network statistics."""
        if not isinstance(data, multinet.multi_layer_network):
            raise TypeError(
                f"Expected multi_layer_network, got {type(data).__name__}"
            )
        
        logger.info("Computing network statistics")
        
        stats = {
            'nodes': data.core_network.number_of_nodes(),
            'edges': data.core_network.number_of_edges(),
            'density': nx.density(data.core_network),
        }
        
        # Add layer statistics if requested
        if self.include_layer_stats:
            from py3plex.algorithms.statistics import multilayer_statistics as mls
            
            layers = self._get_layer_names(data)
            if layers:
                stats['layers'] = len(layers)
                stats['layer_densities'] = {
                    layer: float(mls.layer_density(data, layer))
                    for layer in layers
                }
        
        logger.info(f"  Stats: {stats['nodes']} nodes, {stats['edges']} edges")
        
        return stats
    
    def _get_layer_names(self, network: multinet.multi_layer_network) -> List[str]:
        """Extract layer names from network."""
        layers = set()
        try:
            for node in network.core_network.nodes():
                if isinstance(node, tuple) and len(node) >= 2:
                    layers.add(node[1])
        except Exception:
            pass
        return sorted(layers)


class FilterNodes(PipelineStep):
    """
    Filter nodes based on a condition.
    
    Args:
        min_degree: Minimum degree (default: None)
        max_degree: Maximum degree (default: None)
        node_list: Explicit list of nodes to keep (default: None)
        
    Example:
        >>> step = FilterNodes(min_degree=2)
    """
    
    def __init__(
        self,
        min_degree: Optional[int] = None,
        max_degree: Optional[int] = None,
        node_list: Optional[List] = None
    ):
        """Initialize node filtering step."""
        self.min_degree = min_degree
        self.max_degree = max_degree
        self.node_list = node_list
    
    def transform(self, data: multinet.multi_layer_network) -> multinet.multi_layer_network:
        """Filter nodes from network."""
        if not isinstance(data, multinet.multi_layer_network):
            raise TypeError(
                f"Expected multi_layer_network, got {type(data).__name__}"
            )
        
        logger.info("Filtering nodes")
        
        # Determine nodes to keep
        if self.node_list is not None:
            nodes_to_keep = set(self.node_list)
        else:
            nodes_to_keep = set(data.core_network.nodes())
            
            # Filter by degree
            if self.min_degree is not None or self.max_degree is not None:
                degree_dict = dict(data.core_network.degree())
                nodes_to_keep = {
                    node for node in nodes_to_keep
                    if (self.min_degree is None or degree_dict[node] >= self.min_degree)
                    and (self.max_degree is None or degree_dict[node] <= self.max_degree)
                }
        
        # Create subnetwork
        filtered = data.subnetwork(nodes_to_keep)
        
        logger.info(
            f"  Kept {filtered.core_network.number_of_nodes()} nodes, "
            f"{filtered.core_network.number_of_edges()} edges"
        )
        
        return filtered


class SaveNetwork(PipelineStep):
    """
    Save network to file.
    
    Args:
        path: Output file path
        format: Output format ('graphml', 'gpickle', 'edgelist')
        
    Example:
        >>> step = SaveNetwork(path="output.graphml", format="graphml")
    """
    
    def __init__(self, path: str, format: str = 'graphml'):
        """Initialize save step."""
        self.path = path
        self.format = format
    
    def transform(self, data: multinet.multi_layer_network) -> multinet.multi_layer_network:
        """Save network and pass it through."""
        if not isinstance(data, multinet.multi_layer_network):
            raise TypeError(
                f"Expected multi_layer_network, got {type(data).__name__}"
            )
        
        logger.info(f"Saving network to {self.path}")
        
        if self.format == 'graphml':
            nx.write_graphml(data.core_network, self.path)
        elif self.format == 'gpickle':
            data.save_network(self.path, output_type='gpickle')
        elif self.format == 'edgelist':
            data.save_network(self.path, output_type='edgelist')
        else:
            raise ValueError(f"Unsupported format: {self.format}")
        
        logger.info(f"  Saved to {self.path}")
        
        # Pass through the network for further processing
        return data
