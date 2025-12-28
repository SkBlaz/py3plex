"""
Algorithms module for py3plex.

This module provides access to various network analysis algorithms.
"""

from .multicentrality import multiplex_participation_coefficient
from .meta_flow_report import MetaFlowReport, run_meta_analysis
from .multilayer_clustering import multilayer_clustering

# Centrality explanation module
from . import centrality

# Routing algorithms
from . import routing

# SIR epidemic simulator (requires numpy and scipy)
try:
    from .sir_multiplex import (
        simulate_sir_multiplex_discrete,
        simulate_sir_multiplex_gillespie,
        basic_reproduction_number,
        summarize,
        EpidemicResult
    )
    SIR_AVAILABLE = True
except ImportError:
    SIR_AVAILABLE = False
    # Create placeholder that raises informative error
    def _sir_not_available(*args, **kwargs):
        raise ImportError(
            "SIR epidemic simulator requires numpy and scipy. "
            "Please install them: pip install numpy scipy"
        )
    simulate_sir_multiplex_discrete = _sir_not_available
    simulate_sir_multiplex_gillespie = _sir_not_available
    basic_reproduction_number = _sir_not_available
    summarize = _sir_not_available
    EpidemicResult = None

__all__ = [
    "multiplex_participation_coefficient",
    "MetaFlowReport",
    "run_meta_analysis",
    "multilayer_clustering",
    "simulate_sir_multiplex_discrete",
    "simulate_sir_multiplex_gillespie",
    "basic_reproduction_number",
    "summarize",
    "EpidemicResult",
    "centrality",
    "routing",
]
