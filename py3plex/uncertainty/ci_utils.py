"""Confidence interval utilities for UQ.

This module provides functions to compute confidence intervals for various
statistics, particularly for binomial proportions (present_prob).
"""

import math
from typing import Tuple

import numpy as np


def wilson_score_interval(
    successes: int, n_trials: int, alpha: float = 0.05
) -> Tuple[float, float]:
    """Compute Wilson score confidence interval for a binomial proportion.
    
    The Wilson score interval is robust for small sample sizes and probabilities
    near 0 or 1. It is preferred over the normal approximation (Wald interval).
    
    Parameters
    ----------
    successes : int
        Number of successes (e.g., number of times item appeared in selection)
    n_trials : int
        Total number of trials (e.g., number of UQ samples)
    alpha : float, default=0.05
        Significance level (e.g., 0.05 for 95% CI)
        
    Returns
    -------
    tuple of (float, float)
        Lower and upper bounds of the confidence interval
        
    Notes
    -----
    Based on:
    Wilson, E.B. (1927). "Probable inference, the law of succession, and 
    statistical inference". Journal of the American Statistical Association.
    
    For a CI level of (1-alpha), we use z = Φ^(-1)(1 - alpha/2).
    
    Examples
    --------
    >>> wilson_score_interval(50, 100, alpha=0.05)
    (0.4..., 0.6...)
    
    >>> wilson_score_interval(0, 100, alpha=0.05)
    (0.0, 0.036...)
    
    >>> wilson_score_interval(100, 100, alpha=0.05)
    (0.963..., 1.0)
    """
    if n_trials == 0:
        return (0.0, 1.0)
    
    if successes < 0 or successes > n_trials:
        raise ValueError(
            f"successes ({successes}) must be between 0 and n_trials ({n_trials})"
        )
    
    # Point estimate
    p_hat = successes / n_trials
    
    # z-score for desired confidence level
    from scipy import stats
    z = stats.norm.ppf(1 - alpha / 2)
    
    # Wilson score interval formula
    denominator = 1 + z**2 / n_trials
    center = (p_hat + z**2 / (2 * n_trials)) / denominator
    margin = z * math.sqrt(p_hat * (1 - p_hat) / n_trials + z**2 / (4 * n_trials**2))
    margin = margin / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def clopper_pearson_interval(
    successes: int, n_trials: int, alpha: float = 0.05
) -> Tuple[float, float]:
    """Compute Clopper-Pearson exact confidence interval for a binomial proportion.
    
    This is a more conservative (wider) interval than Wilson score, guaranteed
    to have at least the nominal coverage. Useful when exactness is critical.
    
    Parameters
    ----------
    successes : int
        Number of successes
    n_trials : int
        Total number of trials
    alpha : float, default=0.05
        Significance level (e.g., 0.05 for 95% CI)
        
    Returns
    -------
    tuple of (float, float)
        Lower and upper bounds of the confidence interval
        
    Notes
    -----
    Based on the beta distribution relationship to the binomial.
    
    Examples
    --------
    >>> clopper_pearson_interval(50, 100, alpha=0.05)
    (0.39..., 0.60...)
    """
    if n_trials == 0:
        return (0.0, 1.0)
    
    if successes < 0 or successes > n_trials:
        raise ValueError(
            f"successes ({successes}) must be between 0 and n_trials ({n_trials})"
        )
    
    from scipy import stats
    
    # Special cases
    if successes == 0:
        lower = 0.0
        upper = 1 - (alpha / 2) ** (1 / n_trials)
    elif successes == n_trials:
        lower = (alpha / 2) ** (1 / n_trials)
        upper = 1.0
    else:
        # Use beta distribution quantiles
        lower = stats.beta.ppf(alpha / 2, successes, n_trials - successes + 1)
        upper = stats.beta.ppf(1 - alpha / 2, successes + 1, n_trials - successes)
    
    return (lower, upper)


def binomial_proportion_ci(
    successes: int,
    n_trials: int,
    alpha: float = 0.05,
    method: str = "wilson",
) -> Tuple[float, float]:
    """Compute confidence interval for a binomial proportion.
    
    Parameters
    ----------
    successes : int
        Number of successes
    n_trials : int
        Total number of trials
    alpha : float, default=0.05
        Significance level
    method : str, default="wilson"
        Method to use: "wilson" or "clopper-pearson"
        
    Returns
    -------
    tuple of (float, float)
        Lower and upper bounds of the confidence interval
        
    Raises
    ------
    ValueError
        If method is not recognized
    """
    if method == "wilson":
        return wilson_score_interval(successes, n_trials, alpha)
    elif method == "clopper-pearson":
        return clopper_pearson_interval(successes, n_trials, alpha)
    else:
        raise ValueError(f"Unknown CI method: {method}. Use 'wilson' or 'clopper-pearson'")


def rank_ci_from_samples(
    ranks: np.ndarray, alpha: float = 0.05
) -> Tuple[float, float]:
    """Compute empirical confidence interval for ranks from samples.
    
    Parameters
    ----------
    ranks : np.ndarray
        Array of rank values from different samples
    alpha : float, default=0.05
        Significance level
        
    Returns
    -------
    tuple of (float, float)
        Lower and upper bounds of the confidence interval (quantiles)
    """
    if len(ranks) == 0:
        return (np.nan, np.nan)
    
    lower_q = alpha / 2
    upper_q = 1 - alpha / 2
    
    lower = np.quantile(ranks, lower_q)
    upper = np.quantile(ranks, upper_q)
    
    return (float(lower), float(upper))
