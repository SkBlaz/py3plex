"""Temporal multilayer network implementation.

This module provides the TemporalMultiLayerNetwork class, which extends the
standard multi_layer_network with first-class support for temporal dynamics.

Key Features:
    - Time-stamped edges and nodes
    - Efficient time-range queries
    - Sliding window iteration
    - Snapshot extraction at specific times
    - Streaming algorithm support

Example:
    >>> from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
    >>> 
    >>> # Create temporal network
    >>> tnet = TemporalMultiLayerNetwork()
    >>> 
    >>> # Add time-stamped edges
    >>> tnet.add_edge('A', 'layer1', 'B', 'layer1', t=100.0)
    >>> tnet.add_edge('B', 'layer1', 'C', 'layer1', t=200.0)
    >>> 
    >>> # Get snapshot at specific time
    >>> snapshot = tnet.snapshot_at(150.0)
    >>> 
    >>> # Iterate over sliding windows
    >>> for t_start, t_end, window_net in tnet.window_iter(window_size=50, step=25):
    ...     print(f"Window [{t_start}, {t_end}]: {window_net.number_of_edges()} edges")
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

import pandas as pd

from py3plex.temporal_utils import EdgeTimeInterval, TimeLike, _parse_time, extract_edge_time
from .multinet import multi_layer_network


class TemporalMultiLayerNetwork:
    """Temporal multilayer network with time-stamped edges.
    
    This class wraps a multi_layer_network instance and provides temporal
    operations like time slicing, windowing, and snapshot extraction.
    
    Attributes:
        base_network: Underlying multi_layer_network instance
        time_attribute: Name of the time attribute on edges (default: "t")
        temporal_edges: List of (edge_dict, time_interval) tuples
        time_index: Sorted list of unique timestamps for efficient querying
    """
    
    def __init__(
        self,
        base_network: Optional[multi_layer_network] = None,
        time_attribute: str = "t",
        directed: bool = False,
    ):
        """Initialize a temporal multilayer network.
        
        Args:
            base_network: Optional existing multi_layer_network to wrap.
                         If None, creates a new empty network.
            time_attribute: Name of the time attribute on edges (default: "t")
            directed: Whether the network is directed (used if creating new network)
        """
        if base_network is None:
            self.base_network = multi_layer_network(directed=directed)
        else:
            self.base_network = base_network
        
        self.time_attribute = time_attribute
        
        # Storage for temporal edges: list of (edge_dict, EdgeTimeInterval)
        self.temporal_edges: List[Tuple[Dict[str, Any], EdgeTimeInterval]] = []
        
        # Sorted list of timestamps for efficient range queries
        self.time_index: List[float] = []
    
    def add_edge(
        self,
        u: Any,
        layer_u: Any,
        v: Any,
        layer_v: Any,
        t: TimeLike,
        weight: float = 1.0,
        **attr: Any,
    ) -> None:
        """Add a single time-stamped edge.
        
        Args:
            u: Source node identifier
            layer_u: Layer for source node
            v: Target node identifier
            layer_v: Layer for target node
            t: Timestamp (numeric, datetime, or string)
            weight: Edge weight (default: 1.0)
            **attr: Additional edge attributes
        """
        # Parse timestamp
        t_parsed = _parse_time(t)
        
        # Create edge dict in format expected by multi_layer_network
        edge_dict = {
            'source': u,
            'target': v,
            'source_type': layer_u,
            'target_type': layer_v,
            'weight': weight,
            self.time_attribute: t_parsed,
            **attr
        }
        
        # Store temporal edge
        time_interval = EdgeTimeInterval(start=t_parsed, end=t_parsed)
        self.temporal_edges.append((edge_dict, time_interval))
        
        # Update time index
        bisect.insort(self.time_index, t_parsed)
        
        # Add to base network
        self.base_network.add_edges([edge_dict])
    
    def add_edges(
        self,
        edges: Iterable[Union[Dict[str, Any], Tuple]],
        input_type: str = "dict",
        time_attribute: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Add multiple time-stamped edges.
        
        Args:
            edges: Iterable of edges. Each edge can be:
                   - dict with keys: source, target, source_type, target_type, t, ...
                   - tuple: (u, layer_u, v, layer_v, t, weight?)
            input_type: Format of edges ("dict" or "tuple")
            time_attribute: Time attribute name (overrides instance default)
            **kwargs: Additional attributes to add to all edges
        """
        time_attr = time_attribute or self.time_attribute
        
        for edge in edges:
            if input_type == "dict" or isinstance(edge, dict):
                # Extract required fields
                u = edge['source']
                v = edge['target']
                layer_u = edge['source_type']
                layer_v = edge['target_type']
                t = edge.get(time_attr, edge.get('t'))
                weight = edge.get('weight', 1.0)
                
                # Get additional attributes
                extra_attrs = {k: v for k, v in edge.items() 
                              if k not in ['source', 'target', 'source_type', 
                                          'target_type', time_attr, 't', 'weight']}
                extra_attrs.update(kwargs)
                
                self.add_edge(u, layer_u, v, layer_v, t, weight, **extra_attrs)
            
            elif input_type == "tuple" or isinstance(edge, (tuple, list)):
                # Unpack tuple: (u, layer_u, v, layer_v, t, weight?)
                if len(edge) >= 5:
                    u, layer_u, v, layer_v, t = edge[:5]
                    weight = edge[5] if len(edge) > 5 else 1.0
                    self.add_edge(u, layer_u, v, layer_v, t, weight, **kwargs)
                else:
                    raise ValueError(f"Tuple edge must have at least 5 elements, got {len(edge)}")
    
    def edges_between(
        self,
        t_start: Optional[TimeLike] = None,
        t_end: Optional[TimeLike] = None,
        layers: Optional[Iterable[Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over edges whose time falls in [t_start, t_end).
        
        Args:
            t_start: Start of time range (None means -infinity)
            t_end: End of time range (None means +infinity)
            layers: Optional layer filter (only edges in these layers)
            
        Yields:
            Edge dictionaries
        """
        # Parse time bounds
        t0 = _parse_time(t_start) if t_start is not None else None
        t1 = _parse_time(t_end) if t_end is not None else None
        
        # Convert layers to set for faster lookup
        layer_set = set(layers) if layers is not None else None
        
        for edge_dict, time_interval in self.temporal_edges:
            # Check time overlap
            if not time_interval.overlaps(t0, t1):
                continue
            
            # Check layer filter
            if layer_set is not None:
                if edge_dict['source_type'] not in layer_set:
                    continue
                if edge_dict['target_type'] not in layer_set:
                    continue
            
            yield edge_dict
    
    def slice_time_window(
        self,
        t_start: Optional[TimeLike] = None,
        t_end: Optional[TimeLike] = None,
        layers: Optional[Iterable[Any]] = None,
    ) -> "TemporalMultiLayerNetwork":
        """Return a new TemporalMultiLayerNetwork restricted to a time interval.
        
        Args:
            t_start: Start of time range (None means -infinity)
            t_end: End of time range (None means +infinity)
            layers: Optional layer filter
            
        Returns:
            New TemporalMultiLayerNetwork containing only edges in the time range
        """
        # Create new temporal network
        new_tnet = TemporalMultiLayerNetwork(
            base_network=None,  # Will add edges to create base network
            time_attribute=self.time_attribute,
            directed=self.base_network.directed,
        )
        
        # Add filtered edges
        filtered_edges = list(self.edges_between(t_start, t_end, layers))
        if filtered_edges:
            new_tnet.add_edges(filtered_edges, input_type="dict")
        
        return new_tnet
    
    def snapshot_at(
        self,
        t: TimeLike,
        mode: str = "up_to",
        layers: Optional[Iterable[Any]] = None,
    ) -> multi_layer_network:
        """Build a multi_layer_network snapshot at time t.
        
        Args:
            t: Timestamp for snapshot
            mode: Snapshot mode:
                  - "up_to": edges with time <= t (cumulative)
                  - "exact": edges with time == t (only at that instant)
                  - "at": alias for "exact"
            layers: Optional layer filter
            
        Returns:
            multi_layer_network representing the snapshot
        """
        t_parsed = _parse_time(t)
        
        # Create new base network
        snapshot = multi_layer_network(directed=self.base_network.directed)
        
        # Determine time range based on mode
        if mode == "up_to":
            edges_iter = self.edges_between(None, t_parsed, layers)
        elif mode in ("exact", "at"):
            edges_iter = self.edges_between(t_parsed, t_parsed, layers)
        else:
            raise ValueError(f"Unknown mode: {mode}. Must be 'up_to', 'exact', or 'at'")
        
        # Add edges to snapshot
        edges_to_add = list(edges_iter)
        if edges_to_add:
            snapshot.add_edges(edges_to_add)
        
        return snapshot
    
    def window_iter(
        self,
        window_size: Union[float, timedelta],
        step: Optional[Union[float, timedelta]] = None,
        start: Optional[TimeLike] = None,
        end: Optional[TimeLike] = None,
        layers: Optional[Iterable[Any]] = None,
        return_type: str = "temporal",
    ) -> Iterator[Tuple[float, float, Union["TemporalMultiLayerNetwork", multi_layer_network]]]:
        """Iterate over sliding time windows.
        
        Args:
            window_size: Size of each window (numeric or timedelta)
            step: Step size between windows (defaults to window_size for non-overlapping)
            start: Start time for windowing (defaults to first timestamp)
            end: End time for windowing (defaults to last timestamp)
            layers: Optional layer filter
            return_type: Type of window to return:
                        - "temporal": TemporalMultiLayerNetwork
                        - "snapshot": multi_layer_network (cumulative snapshot)
            
        Yields:
            Tuples of (t_start, t_end, window_network)
        """
        if not self.time_index:
            return  # No edges, nothing to iterate
        
        # Convert window_size and step to numeric
        if isinstance(window_size, timedelta):
            window_size = window_size.total_seconds()
        
        if step is None:
            step = window_size
        elif isinstance(step, timedelta):
            step = step.total_seconds()
        
        # Determine time range
        t_start = _parse_time(start) if start is not None else self.time_index[0]
        t_end = _parse_time(end) if end is not None else self.time_index[-1]
        
        # Iterate over windows
        current_start = t_start
        while current_start < t_end:
            current_end = min(current_start + window_size, t_end)
            
            # Create window network
            if return_type == "temporal":
                window_net = self.slice_time_window(current_start, current_end, layers)
            elif return_type == "snapshot":
                window_net = self.snapshot_at(current_end, mode="up_to", layers=layers)
            else:
                raise ValueError(f"Unknown return_type: {return_type}")
            
            yield (current_start, current_end, window_net)
            
            current_start += step
    
    def get_base_network(self) -> multi_layer_network:
        """Return the underlying multi_layer_network.
        
        This returns the full network without temporal filtering,
        useful for algorithms that don't need temporal information.
        
        Returns:
            The base multi_layer_network instance
        """
        return self.base_network
    
    def number_of_edges(self) -> int:
        """Return the total number of temporal edges."""
        return len(self.temporal_edges)
    
    def number_of_nodes(self) -> int:
        """Return the total number of nodes in the base network."""
        if self.base_network is None or self.base_network.core_network is None:
            return 0
        return self.base_network.core_network.number_of_nodes()
    
    def time_range(self) -> Tuple[Optional[float], Optional[float]]:
        """Return the time range of the network.
        
        Returns:
            Tuple of (min_time, max_time), or (None, None) if no edges
        """
        if not self.time_index:
            return (None, None)
        return (self.time_index[0], self.time_index[-1])
    
    @staticmethod
    def from_multilayer_network(
        base_network: multi_layer_network,
        time_attribute: str = "t",
    ) -> "TemporalMultiLayerNetwork":
        """Create a TemporalMultiLayerNetwork from an existing multi_layer_network.
        
        This extracts temporal information from edge attributes in the base network.
        
        Args:
            base_network: Existing multi_layer_network with temporal edge attributes
            time_attribute: Name of the time attribute on edges
            
        Returns:
            New TemporalMultiLayerNetwork instance
        """
        tnet = TemporalMultiLayerNetwork(
            base_network=None,  # Will rebuild
            time_attribute=time_attribute,
            directed=base_network.directed,
        )
        
        # Extract edges from base network with temporal info
        for layer in base_network.get_layers()[0]:
            layer_graph = base_network.get_layers()[1][base_network.get_layers()[0].index(layer)]
            
            for u, v, data in layer_graph.edges(data=True):
                if time_attribute in data or 't' in data:
                    t = data.get(time_attribute, data.get('t'))
                    weight = data.get('weight', 1.0)
                    
                    # Get additional attributes
                    extra = {k: v for k, v in data.items() 
                            if k not in [time_attribute, 't', 'weight']}
                    
                    tnet.add_edge(u, layer, v, layer, t, weight, **extra)
        
        return tnet
    
    @staticmethod
    def from_pandas(
        df: pd.DataFrame,
        source_col: str = "source",
        target_col: str = "target",
        layer_u_col: str = "layer_u",
        layer_v_col: str = "layer_v",
        time_col: str = "t",
        weight_col: str = "weight",
        directed: bool = False,
    ) -> "TemporalMultiLayerNetwork":
        """Create a TemporalMultiLayerNetwork from a pandas DataFrame.
        
        Args:
            df: DataFrame with edge data
            source_col: Column name for source nodes
            target_col: Column name for target nodes
            layer_u_col: Column name for source layer
            layer_v_col: Column name for target layer
            time_col: Column name for timestamps
            weight_col: Column name for weights (optional)
            directed: Whether the network is directed
            
        Returns:
            New TemporalMultiLayerNetwork instance
        """
        tnet = TemporalMultiLayerNetwork(time_attribute=time_col, directed=directed)
        
        for _, row in df.iterrows():
            u = row[source_col]
            v = row[target_col]
            layer_u = row[layer_u_col]
            layer_v = row[layer_v_col]
            t = row[time_col]
            weight = row.get(weight_col, 1.0) if weight_col in df.columns else 1.0
            
            # Get additional columns
            extra = {}
            for col in df.columns:
                if col not in [source_col, target_col, layer_u_col, layer_v_col, 
                              time_col, weight_col]:
                    extra[col] = row[col]
            
            tnet.add_edge(u, layer_u, v, layer_v, t, weight, **extra)
        
        return tnet
