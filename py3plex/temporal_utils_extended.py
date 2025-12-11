"""Extended temporal utilities for duration parsing.

This module provides utilities for parsing duration strings like "7d", "1h", "30m"
into numeric values (seconds).
"""

from __future__ import annotations

import re
from typing import Union


def parse_duration_string(duration: Union[str, float, int]) -> float:
    """Parse a duration string into seconds.
    
    Supports the following formats:
    - Numbers: Treated as seconds (e.g., 100 → 100.0)
    - Days: "7d", "1day", "2days" → seconds
    - Hours: "24h", "1hour", "2hours" → seconds
    - Minutes: "30m", "1min", "2minutes" → seconds
    - Seconds: "60s", "1sec", "2seconds" → seconds
    - Weeks: "1w", "2weeks" → seconds
    
    Args:
        duration: Duration as string or numeric value
        
    Returns:
        Duration in seconds as float
        
    Raises:
        ValueError: If duration string format is invalid
        
    Examples:
        >>> parse_duration_string(100)
        100.0
        
        >>> parse_duration_string("7d")
        604800.0
        
        >>> parse_duration_string("24h")
        86400.0
        
        >>> parse_duration_string("30m")
        1800.0
        
        >>> parse_duration_string("1w")
        604800.0
    """
    # If already numeric, return as float
    if isinstance(duration, (int, float)):
        return float(duration)
    
    # Parse string duration
    duration = duration.strip().lower()
    
    # Pattern: number followed by unit
    # Supports: w/week(s), d/day(s), h/hour(s), m/min(ute)(s), s/sec(ond)(s)
    pattern = r'^(\d+(?:\.\d+)?)\s*([a-z]+)$'
    match = re.match(pattern, duration)
    
    if not match:
        raise ValueError(
            f"Invalid duration format: '{duration}'. "
            f"Expected format: '<number><unit>' (e.g., '7d', '24h', '30m')"
        )
    
    value = float(match.group(1))
    unit = match.group(2)
    
    # Unit conversion to seconds
    conversions = {
        # Weeks
        'w': 7 * 24 * 3600,
        'week': 7 * 24 * 3600,
        'weeks': 7 * 24 * 3600,
        # Days
        'd': 24 * 3600,
        'day': 24 * 3600,
        'days': 24 * 3600,
        # Hours
        'h': 3600,
        'hour': 3600,
        'hours': 3600,
        'hr': 3600,
        'hrs': 3600,
        # Minutes
        'm': 60,
        'min': 60,
        'minute': 60,
        'minutes': 60,
        'mins': 60,
        # Seconds
        's': 1,
        'sec': 1,
        'second': 1,
        'seconds': 1,
        'secs': 1,
    }
    
    if unit not in conversions:
        supported_units = ', '.join(sorted(set(conversions.keys())))
        raise ValueError(
            f"Unknown time unit: '{unit}'. "
            f"Supported units: {supported_units}"
        )
    
    return value * conversions[unit]


def format_duration(seconds: float, precision: int = 2) -> str:
    """Format seconds into a human-readable duration string.
    
    Args:
        seconds: Duration in seconds
        precision: Number of time units to include (default: 2)
        
    Returns:
        Formatted duration string
        
    Examples:
        >>> format_duration(604800)
        '1w'
        
        >>> format_duration(90061)
        '1d 1h'
        
        >>> format_duration(3661, precision=3)
        '1h 1m 1s'
    """
    if seconds == 0:
        return "0s"
    
    units = [
        ('w', 7 * 24 * 3600),
        ('d', 24 * 3600),
        ('h', 3600),
        ('m', 60),
        ('s', 1),
    ]
    
    parts = []
    remaining = abs(seconds)
    
    for unit_name, unit_seconds in units:
        if remaining >= unit_seconds:
            count = int(remaining // unit_seconds)
            remaining %= unit_seconds
            parts.append(f"{count}{unit_name}")
            
            if len(parts) >= precision:
                break
    
    if not parts:
        # Less than 1 second
        return f"{seconds:.3f}s"
    
    result = ' '.join(parts)
    return f"-{result}" if seconds < 0 else result
