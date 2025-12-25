"""Temporal utility functions for multilayer networks.

This module provides utilities for working with temporal data in multilayer networks.
It defines conventions for time attributes and provides helper functions to extract
and parse temporal information from edges.

Temporal Attribute Conventions:
    Edges may have any of these temporal attributes:
    
    - **t**: A scalar timestamp (float, int, or ISO string)
    - **t_start** and **t_end**: Interval timestamps
    
    If both styles exist, interval form (t_start/t_end) takes precedence.
    Time is optional: if no such attributes exist, the graph is considered "atemporal".

Examples:
    >>> # Point-in-time edge
    >>> edge = {'source': 'A', 'target': 'B', 't': 1234567890.0}
    >>> interval = extract_edge_time(edge)
    >>> # interval.start == interval.end == 1234567890.0
    
    >>> # Interval edge
    >>> edge = {'source': 'A', 'target': 'B', 't_start': 100.0, 't_end': 200.0}
    >>> interval = extract_edge_time(edge)
    >>> # interval.start == 100.0, interval.end == 200.0
    
    >>> # Atemporal edge
    >>> edge = {'source': 'A', 'target': 'B'}
    >>> interval = extract_edge_time(edge)
    >>> # interval.start == None, interval.end == None
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Optional, Union

from py3plex.exceptions import ParsingError

# Type alias for time-like values
TimeLike = Union[int, float, str, _dt.datetime]


@dataclass
class EdgeTimeInterval:
    """Represents a temporal interval for an edge.
    
    Attributes:
        start: Start timestamp (seconds since epoch), or None if atemporal
        end: End timestamp (seconds since epoch), or None if atemporal
    """
    start: Optional[float]
    end: Optional[float]
    
    def overlaps(self, t0: Optional[float], t1: Optional[float]) -> bool:
        """Check if this interval overlaps with [t0, t1].
        
        Args:
            t0: Start of query interval (None means -infinity)
            t1: End of query interval (None means +infinity)
            
        Returns:
            True if intervals overlap, False otherwise.
            If this interval is atemporal (start=None, end=None), returns True.
        """
        # Atemporal edges are always included
        if self.start is None and self.end is None:
            return True
        
        # If query interval is unbounded, include all temporal edges
        if t0 is None and t1 is None:
            return True
        
        # Handle unbounded query start
        if t0 is None:
            t0 = float('-inf')
        
        # Handle unbounded query end
        if t1 is None:
            t1 = float('inf')
        
        # Check for overlap: [a, b] overlaps [c, d] if a <= d and c <= b
        return self.start <= t1 and t0 <= self.end


def _parse_time(value: TimeLike) -> float:
    """Parse a time-like value into a float timestamp (seconds since epoch).
    
    Args:
        value: A time-like value (int, float, str, or datetime)
        
    Returns:
        Float timestamp in seconds since epoch
        
    Raises:
        ValueError: If the value cannot be parsed as a time
        
    Examples:
        >>> _parse_time(1234567890)
        1234567890.0
        
        >>> _parse_time(1234567890.5)
        1234567890.5
        
        >>> _parse_time("2009-02-13T23:31:30")  # doctest: +SKIP
        1234567890.0
        
        >>> import datetime
        >>> dt = datetime.datetime(2009, 2, 13, 23, 31, 30)
        >>> _parse_time(dt)  # doctest: +SKIP
        1234567890.0
    """
    # Handle numeric types
    if isinstance(value, (int, float)):
        return float(value)
    
    # Handle datetime objects
    if isinstance(value, _dt.datetime):
        return value.timestamp()
    
    # Handle string types
    if isinstance(value, str):
        # Try to parse as ISO format
        try:
            dt = _dt.datetime.fromisoformat(value)
            return dt.timestamp()
        except (ValueError, AttributeError):
            pass
        
        # Try to parse as float string
        try:
            return float(value)
        except ValueError:
            pass
        
        # If all else fails, raise error with helpful suggestions
        raise ParsingError(
            f"Cannot parse time value '{value}'",
            expected="numeric timestamp or ISO 8601 datetime string",
            got=f"{type(value).__name__}: '{value}'",
            suggestions=[
                "Use numeric timestamps (e.g., 1234567890.0 for seconds since epoch)",
                "Use ISO 8601 format strings (e.g., '2023-01-01T12:00:00')",
                "Ensure datetime objects are properly formatted"
            ]
        )
    
    # Unsupported type
    raise ParsingError(
        f"Unsupported time value type: {type(value).__name__}",
        expected="int, float, str, or datetime",
        got=str(type(value)),
        suggestions=[
            "Convert your time value to one of: int, float, str (ISO 8601), or datetime",
            f"Example: convert {type(value).__name__} to float timestamp"
        ]
    )


def extract_edge_time(attrs: dict[str, Any]) -> EdgeTimeInterval:
    """Extract temporal information from edge attributes.
    
    Given an edge attribute dict, return a unified EdgeTimeInterval.
    
    Rules:
        - If 't_start' or 't_end' present: use interval semantics
        - Else if 't' present: treat as instantaneous (start=end=t)
        - If no time attributes: return EdgeTimeInterval(start=None, end=None)
    
    Args:
        attrs: Dictionary of edge attributes
        
    Returns:
        EdgeTimeInterval representing the temporal extent of the edge
        
    Examples:
        >>> # Point-in-time edge
        >>> extract_edge_time({'t': 100.0})
        EdgeTimeInterval(start=100.0, end=100.0)
        
        >>> # Interval edge
        >>> extract_edge_time({'t_start': 100.0, 't_end': 200.0})
        EdgeTimeInterval(start=100.0, end=200.0)
        
        >>> # Interval with only start
        >>> extract_edge_time({'t_start': 100.0})
        EdgeTimeInterval(start=100.0, end=inf)
        
        >>> # Atemporal edge
        >>> extract_edge_time({'weight': 1.0})
        EdgeTimeInterval(start=None, end=None)
    """
    # Check for interval form (takes precedence)
    if 't_start' in attrs or 't_end' in attrs:
        start = None
        end = None
        
        if 't_start' in attrs:
            try:
                start = _parse_time(attrs['t_start'])
            except (ValueError, TypeError):
                pass
        
        if 't_end' in attrs:
            try:
                end = _parse_time(attrs['t_end'])
            except (ValueError, TypeError):
                pass
        
        # Handle unbounded intervals
        if start is not None and end is None:
            end = float('inf')
        elif start is None and end is not None:
            start = float('-inf')
        
        return EdgeTimeInterval(start=start, end=end)
    
    # Check for point-in-time form
    if 't' in attrs:
        try:
            t = _parse_time(attrs['t'])
            return EdgeTimeInterval(start=t, end=t)
        except (ValueError, TypeError):
            pass
    
    # No temporal information
    return EdgeTimeInterval(start=None, end=None)
