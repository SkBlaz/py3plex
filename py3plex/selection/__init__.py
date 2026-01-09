"""AutoCommunity selection module.

This module provides automatic selection of community detection algorithms
based on multi-metric evaluation and a "most wins" decision engine.

Main components:
    - capabilities: Detection of available algorithms, metrics, and UQ
    - community_registry: Registry of community detection candidates
    - metric_registry: Registry of quality metrics (bucketed)
    - evaluate: Contestant evaluation
    - wins: Most-wins decision engine
    - result: AutoCommunityResult data structure
"""

from .result import AutoCommunityResult, ContestantResult

__all__ = [
    "AutoCommunityResult",
    "ContestantResult",
]
