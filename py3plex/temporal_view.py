"""Temporal view layer for multilayer networks.

This module provides a thin, non-owning temporal view over existing multilayer networks.
The TemporalMultinetView class wraps a base network and filters edges based on temporal
constraints without copying data.

This is an experimental feature that provides:
- Read-only temporal filtering
- Snapshot and time-range queries
- Backwards compatibility (atemporal edges always included)
- Minimal overhead (no data copying)

Examples:
    >>> from py3plex.core import multinet
    >>> from py3plex.temporal_view import TemporalMultinetView
    >>> 
    >>> # Create a network with temporal edges
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([
    ...     {'source': 'A', 'target': 'B', 
    ...      'source_type': 'layer1', 'target_type': 'layer1',
    ...      't': 100.0},
    ...     {'source': 'B', 'target': 'C',
    ...      'source_type': 'layer1', 'target_type': 'layer1',
    ...      't': 200.0}
    ... ])
    >>> 
    >>> # Create a temporal view
    >>> view = TemporalMultinetView(net)
    >>> 
    >>> # Get snapshot at time 150
    >>> snapshot = view.snapshot_at(150.0)
    >>> # Only edges at or before t=150 are visible
    >>> 
    >>> # Get time range [100, 200]
    >>> range_view = view.with_slice(100.0, 200.0)
    >>> # All edges in range are visible
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Iterator, Optional

from .temporal_utils import extract_edge_time


@dataclass
class TemporalSlice:
    """Represents a temporal slice [t0, t1].
    
    Attributes:
        t0: Start time (None means -infinity)
        t1: End time (None means +infinity)
    """
    t0: Optional[float] = None
    t1: Optional[float] = None


class TemporalMultinetView:
    """A read-only temporal view over an existing multilayer network.
    
    This class provides temporal filtering of edges when iterating or constructing
    derived graphs. It does not copy data; it simply filters on access based on
    temporal constraints.
    
    **Experimental**: This is an experimental feature. The API may change in future
    versions. However, it is safe to use and provides backwards compatibility for
    networks without temporal information.
    
    Temporal Filtering Rules:
        - Edges with no temporal attributes are always included (backwards compatible)
        - Point-in-time edges (with 't') are included if t is in [t0, t1]
        - Interval edges (with 't_start', 't_end') are included if interval overlaps [t0, t1]
    
    Attributes:
        _base: The underlying multilayer network
        _time_attr: Name of point-in-time attribute (default: "t")
        _t_start_attr: Name of interval start attribute (default: "t_start")
        _t_end_attr: Name of interval end attribute (default: "t_end")
        _slice: Current temporal slice
    
    Examples:
        >>> view = TemporalMultinetView(network)
        >>> 
        >>> # Snapshot at specific time
        >>> snapshot = view.snapshot_at(1234567890.0)
        >>> 
        >>> # Time range query
        >>> range_view = view.with_slice(start_time, end_time)
        >>> 
        >>> # Iterate over filtered edges
        >>> for edge in range_view.iter_edges():
        ...     print(edge)
    """
    
    def __init__(
        self,
        base_multinet: Any,
        time_attr: str = "t",
        t_start_attr: str = "t_start",
        t_end_attr: str = "t_end"
    ) -> None:
        """Initialize a temporal view.
        
        Args:
            base_multinet: The underlying multilayer network to wrap
            time_attr: Name of point-in-time attribute (default: "t")
            t_start_attr: Name of interval start attribute (default: "t_start")
            t_end_attr: Name of interval end attribute (default: "t_end")
        """
        self._base = base_multinet
        self._time_attr = time_attr
        self._t_start_attr = t_start_attr
        self._t_end_attr = t_end_attr
        self._slice = TemporalSlice()  # Initially no temporal filter
    
    def with_slice(self, t0: Optional[float], t1: Optional[float]) -> "TemporalMultinetView":
        """Return a new TemporalMultinetView with a temporal slice [t0, t1].
        
        This method returns a new view sharing the same base network but with
        different temporal constraints. The original view is not modified.
        
        Args:
            t0: Start time (None means -infinity)
            t1: End time (None means +infinity)
            
        Returns:
            New TemporalMultinetView with the specified temporal slice
            
        Examples:
            >>> # View for time range [100, 200]
            >>> view = original.with_slice(100.0, 200.0)
            >>> 
            >>> # View from time 100 onwards
            >>> view = original.with_slice(100.0, None)
            >>> 
            >>> # View up to time 200
            >>> view = original.with_slice(None, 200.0)
        """
        new_view = TemporalMultinetView(
            self._base,
            time_attr=self._time_attr,
            t_start_attr=self._t_start_attr,
            t_end_attr=self._t_end_attr
        )
        new_view._slice = TemporalSlice(t0=t0, t1=t1)
        return new_view
    
    def snapshot_at(self, t: float) -> "TemporalMultinetView":
        """Return a new TemporalMultinetView at an instantaneous time t.
        
        This is equivalent to with_slice(t, t) and returns a snapshot of the
        network at a specific point in time.
        
        Args:
            t: Snapshot time
            
        Returns:
            New TemporalMultinetView representing the network at time t
            
        Examples:
            >>> snapshot = view.snapshot_at(1234567890.0)
        """
        return self.with_slice(t, t)
    
    def _matches_temporal_filter(self, edge_attrs: dict[str, Any]) -> bool:
        """Check if an edge matches the current temporal filter.
        
        Args:
            edge_attrs: Edge attribute dictionary
            
        Returns:
            True if edge should be included, False otherwise
        """
        temporal_attrs = {
            canonical: edge_attrs[configured]
            for canonical, configured in (
                ("t", self._time_attr),
                ("t_start", self._t_start_attr),
                ("t_end", self._t_end_attr),
            )
            if configured in edge_attrs
        }
        interval = extract_edge_time(temporal_attrs)
        return interval.overlaps(self._slice.t0, self._slice.t1)
    
    def iter_edges(self, *args, **kwargs) -> Iterator[Any]:
        """Iterate over edges that respect the current temporal slice.
        
        This delegates to the base network's edge iterator but filters by time
        using extract_edge_time. Any arguments are passed through to the
        underlying network's get_edges() method.
        
        Args:
            *args: Positional arguments passed to base network's get_edges()
            **kwargs: Keyword arguments passed to base network's get_edges()
            
        Yields:
            Edges that match the temporal filter
            
        Examples:
            >>> for edge in view.iter_edges():
            ...     print(edge)
        """
        # A freshly constructed multi_layer_network is empty but leaves its
        # NetworkX graph uninitialized. Treat that state like an empty edge
        # iterator instead of forwarding into get_edges() and dereferencing
        # ``None.edges``.
        if hasattr(self._base, "core_network") and self._base.core_network is None:
            return

        # Always fetch attributes with each edge so parallel edges retain identity.
        requested_data = args[0] if args else kwargs.get("data", False)
        if args:
            data_args = (True,) + args[1:]
            data_kwargs = kwargs
        else:
            data_args = args
            data_kwargs = {**kwargs, "data": True}

        for edge in self._base.get_edges(*data_args, **data_kwargs):
            if len(edge) >= 3 and isinstance(edge[-1], Mapping):
                if self._matches_temporal_filter(edge[-1]):
                    yield edge if requested_data else edge[:-1]
            else:
                # Preserve the fallback for unexpected edge formats.
                yield edge

    def get_edges(self, *args, **kwargs) -> list[Any]:
        """Get a list of edges that respect the current temporal slice.
        
        This is a convenience method that returns a list instead of an iterator.
        
        Args:
            *args: Positional arguments passed to base network's get_edges()
            **kwargs: Keyword arguments passed to base network's get_edges()
            
        Returns:
            List of edges that match the temporal filter
        """
        return list(self.iter_edges(*args, **kwargs))
    
    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the base network.
        
        This allows transparent access to base network methods and attributes
        that don't require special temporal handling.
        
        Args:
            name: Attribute name
            
        Returns:
            Attribute from base network
        """
        return getattr(self._base, name)
    
    @property
    def base_network(self) -> Any:
        """Get the underlying base network.
        
        Returns:
            The wrapped multilayer network
        """
        return self._base
    
    @property
    def temporal_slice(self) -> TemporalSlice:
        """Get the current temporal slice.
        
        Returns:
            Current TemporalSlice configuration
        """
        return self._slice
