"""Context management for global uncertainty settings.

This module provides context variables and context managers for controlling
uncertainty estimation globally across a pipeline or workflow.
"""

from __future__ import annotations

import contextvars
import copy
from contextlib import contextmanager
from typing import Optional

from .types import UncertaintyConfig, UncertaintyMode, ResamplingStrategy


# Global context variable for uncertainty configuration
_uncertainty_ctx = contextvars.ContextVar(
    "py3plex_uncertainty_config",
    default=UncertaintyConfig()
)


def get_uncertainty_config() -> UncertaintyConfig:
    """Get the current uncertainty configuration.
    
    Returns
    -------
    UncertaintyConfig
        The current configuration from the context.
    
    Examples
    --------
    >>> from py3plex.uncertainty import get_uncertainty_config
    >>> cfg = get_uncertainty_config()
    >>> cfg.mode
    <UncertaintyMode.OFF: 'off'>
    >>> cfg.default_n_runs
    50
    """
    return _uncertainty_ctx.get()


def set_uncertainty_config(config: UncertaintyConfig) -> contextvars.Token:
    """Set the uncertainty configuration.
    
    Parameters
    ----------
    config : UncertaintyConfig
        The new configuration to set.
    
    Returns
    -------
    Token
        A token that can be used to reset the configuration.
    
    Examples
    --------
    >>> from py3plex.uncertainty import set_uncertainty_config, UncertaintyConfig
    >>> from py3plex.uncertainty import UncertaintyMode
    >>> cfg = UncertaintyConfig(mode=UncertaintyMode.ON, default_n_runs=100)
    >>> token = set_uncertainty_config(cfg)
    >>> # ... do work ...
    >>> _uncertainty_ctx.reset(token)  # restore previous config
    """
    return _uncertainty_ctx.set(config)


@contextmanager
def uncertainty_enabled(
    *,
    n_runs: Optional[int] = None,
    resampling: Optional[ResamplingStrategy] = None,
):
    """Context manager to enable uncertainty estimation.
    
    Within this context, all supported functions will compute uncertainty
    by default (unless explicitly disabled with uncertainty=False).
    
    Parameters
    ----------
    n_runs : int, optional
        Number of runs for uncertainty estimation. If None, uses the
        default from the current config.
    resampling : ResamplingStrategy, optional
        Resampling strategy to use. If None, uses the default from
        the current config.
    
    Yields
    ------
    None
    
    Examples
    --------
    >>> from py3plex.uncertainty import uncertainty_enabled
    >>> from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    >>> 
    >>> # Without uncertainty
    >>> result = multilayer_pagerank(network)
    >>> result.is_deterministic
    True
    >>> 
    >>> # With uncertainty
    >>> with uncertainty_enabled(n_runs=100):
    ...     result = multilayer_pagerank(network)
    >>> result.is_deterministic
    False
    >>> result.std is not None
    True
    
    Notes
    -----
    This uses contextvars, so it's thread-safe and async-safe. Each
    context gets its own configuration.
    """
    cfg = _uncertainty_ctx.get()
    new_cfg = copy.copy(cfg)
    new_cfg.mode = UncertaintyMode.ON
    
    if n_runs is not None:
        new_cfg.default_n_runs = n_runs
    if resampling is not None:
        new_cfg.default_resampling = resampling
    
    token = _uncertainty_ctx.set(new_cfg)
    try:
        yield
    finally:
        _uncertainty_ctx.reset(token)


@contextmanager
def uncertainty_disabled():
    """Context manager to disable uncertainty estimation.
    
    Within this context, all functions will compute deterministic results
    (unless explicitly requested with uncertainty=True).
    
    Yields
    ------
    None
    
    Examples
    --------
    >>> from py3plex.uncertainty import uncertainty_disabled, uncertainty_enabled
    >>> 
    >>> with uncertainty_enabled():
    ...     # Nested context to temporarily disable
    ...     with uncertainty_disabled():
    ...         result = multilayer_pagerank(network)
    >>> result.is_deterministic
    True
    """
    cfg = _uncertainty_ctx.get()
    new_cfg = copy.copy(cfg)
    new_cfg.mode = UncertaintyMode.OFF
    
    token = _uncertainty_ctx.set(new_cfg)
    try:
        yield
    finally:
        _uncertainty_ctx.reset(token)
