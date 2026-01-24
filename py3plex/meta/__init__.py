"""Meta-analysis module for py3plex.

This module provides meta-analytic pooling of network statistics across
multiple networks with support for fixed-effect and random-effects models.

Main exports:
- M: Meta-analysis builder factory
- MetaBuilder: Builder class for meta-analysis
- MetaResult: Result container for meta-analysis
- MetaAnalysisError: Exception class for meta-analysis errors
"""

from .builder import M, MetaBuilder, MetaProxy
from .result import MetaResult
from .stats import (
    meta_analysis,
    fixed_effect_meta,
    random_effects_meta,
    PooledEffect,
)

__all__ = [
    "M",
    "MetaBuilder",
    "MetaProxy",
    "MetaResult",
    "meta_analysis",
    "fixed_effect_meta",
    "random_effects_meta",
    "PooledEffect",
]
