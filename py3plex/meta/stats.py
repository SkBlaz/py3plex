"""Statistical functions for meta-analysis.

This module implements fixed-effect and random-effects meta-analysis models
with heterogeneity metrics following standard meta-analysis methodology.

Models:
- Fixed-effect: Inverse variance weighting
- Random-effects: DerSimonian-Laird τ² estimation

Heterogeneity metrics:
- Q: Cochran's Q statistic
- τ²: Between-study variance (tau-squared)
- I²: Percentage of total variation due to heterogeneity
- H: Ratio of Q to its degrees of freedom
"""

import numpy as np
import warnings
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PooledEffect:
    """Result of meta-analytic pooling.

    Attributes:
        pooled_effect: Pooled effect estimate
        pooled_se: Standard error of pooled effect
        ci_low: Lower confidence interval bound
        ci_high: Upper confidence interval bound
        tau2: Between-study variance (random-effects only, NaN for fixed)
        Q: Cochran's Q statistic
        I2: I-squared heterogeneity metric (percentage)
        H: H heterogeneity metric
        k: Number of studies
        model: "fixed" or "random"
        warnings: List of warning messages
    """

    pooled_effect: float
    pooled_se: float
    ci_low: float
    ci_high: float
    tau2: float
    Q: float
    I2: float
    H: float
    k: int
    model: str
    warnings: list


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide with protection against division by zero.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if denominator is zero or too small

    Returns:
        Result of division or default value
    """
    if abs(denominator) < 1e-10:
        return default
    return numerator / denominator


def fixed_effect_meta(
    effects: np.ndarray, ses: np.ndarray, ci_level: float = 0.95
) -> PooledEffect:
    """Compute fixed-effect meta-analysis.

    Uses inverse variance weighting:
        w_i = 1 / se_i²
        pooled_effect = Σ(w_i * y_i) / Σ(w_i)
        pooled_se = sqrt(1 / Σ(w_i))

    Args:
        effects: Array of effect estimates (length k)
        ses: Array of standard errors (length k)
        ci_level: Confidence interval level (default 0.95)

    Returns:
        PooledEffect with fixed-effect results
    """
    effects = np.asarray(effects, dtype=np.float64)
    ses = np.asarray(ses, dtype=np.float64)
    k = len(effects)
    warnings_list = []

    # Handle k=1 edge case
    if k == 1:
        z = 1.96 if ci_level == 0.95 else np.abs(np.percentile(np.random.randn(10000), [(1 - ci_level) / 2 * 100]))
        return PooledEffect(
            pooled_effect=float(effects[0]),
            pooled_se=float(ses[0]),
            ci_low=float(effects[0] - z * ses[0]),
            ci_high=float(effects[0] + z * ses[0]),
            tau2=np.nan,
            Q=np.nan,
            I2=np.nan,
            H=np.nan,
            k=1,
            model="fixed",
            warnings=[],
        )

    # Inverse variance weights
    weights = 1.0 / (ses**2)

    # Guard against inf/nan in weights
    if not np.all(np.isfinite(weights)):
        raise ValueError("Non-finite weights detected. Check standard errors.")

    sum_w = np.sum(weights)
    if sum_w <= 0:
        raise ValueError("Sum of weights is non-positive.")

    # Pooled effect
    pooled_effect = np.sum(weights * effects) / sum_w
    pooled_se = np.sqrt(1.0 / sum_w)

    # Confidence interval
    z = 1.96 if ci_level == 0.95 else np.abs(np.percentile(np.random.randn(10000), [(1 - ci_level) / 2 * 100]))
    ci_low = pooled_effect - z * pooled_se
    ci_high = pooled_effect + z * pooled_se

    # Heterogeneity: Cochran's Q
    Q = np.sum(weights * (effects - pooled_effect) ** 2)
    df = k - 1

    # I² and H
    if df > 0:
        I2 = max(0.0, (Q - df) / Q) * 100.0
        H = np.sqrt(Q / df)
    else:
        I2 = 0.0
        H = 1.0

    return PooledEffect(
        pooled_effect=float(pooled_effect),
        pooled_se=float(pooled_se),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        tau2=np.nan,  # Not applicable for fixed-effect
        Q=float(Q),
        I2=float(I2),
        H=float(H),
        k=k,
        model="fixed",
        warnings=warnings_list,
    )


def random_effects_meta(
    effects: np.ndarray,
    ses: np.ndarray,
    ci_level: float = 0.95,
    tau2_estimator: str = "DL",
) -> PooledEffect:
    """Compute random-effects meta-analysis using DerSimonian-Laird method.

    Procedure:
        1. Compute fixed-effect pooled estimate
        2. Compute Q statistic
        3. Estimate τ² using DerSimonian-Laird:
           τ² = max(0, (Q - df) / C)
           where C = Σ(w_i) - Σ(w_i²) / Σ(w_i)
        4. Compute random-effects weights: w_i* = 1 / (se_i² + τ²)
        5. Compute pooled effect and SE using w_i*

    Args:
        effects: Array of effect estimates (length k)
        ses: Array of standard errors (length k)
        ci_level: Confidence interval level (default 0.95)
        tau2_estimator: Estimator for τ² (only "DL" supported)

    Returns:
        PooledEffect with random-effects results

    Raises:
        NotImplementedError: If tau2_estimator is not "DL"
    """
    if tau2_estimator != "DL":
        raise NotImplementedError(
            f"τ² estimator '{tau2_estimator}' not implemented. Only 'DL' (DerSimonian-Laird) is supported."
        )

    effects = np.asarray(effects, dtype=np.float64)
    ses = np.asarray(ses, dtype=np.float64)
    k = len(effects)
    warnings_list = []

    # Handle k=1 edge case
    if k == 1:
        z = 1.96 if ci_level == 0.95 else np.abs(np.percentile(np.random.randn(10000), [(1 - ci_level) / 2 * 100]))
        return PooledEffect(
            pooled_effect=float(effects[0]),
            pooled_se=float(ses[0]),
            ci_low=float(effects[0] - z * ses[0]),
            ci_high=float(effects[0] + z * ses[0]),
            tau2=np.nan,
            Q=np.nan,
            I2=np.nan,
            H=np.nan,
            k=1,
            model="random",
            warnings=[],
        )

    # Step 1: Fixed-effect weights and pooled estimate
    weights_fixed = 1.0 / (ses**2)

    if not np.all(np.isfinite(weights_fixed)):
        raise ValueError("Non-finite weights detected. Check standard errors.")

    sum_w = np.sum(weights_fixed)
    if sum_w <= 0:
        raise ValueError("Sum of weights is non-positive.")

    pooled_fixed = np.sum(weights_fixed * effects) / sum_w

    # Step 2: Cochran's Q
    Q = np.sum(weights_fixed * (effects - pooled_fixed) ** 2)
    df = k - 1

    # Step 3: DerSimonian-Laird τ²
    C = sum_w - np.sum(weights_fixed**2) / sum_w

    if C <= 0:
        warnings_list.append("C ≤ 0 in DL estimation, setting τ² = 0")
        tau2 = 0.0
    else:
        tau2 = max(0.0, (Q - df) / C)

    # Step 4: Random-effects weights
    weights_random = 1.0 / (ses**2 + tau2)
    sum_w_random = np.sum(weights_random)

    if sum_w_random <= 0:
        raise ValueError("Sum of random-effects weights is non-positive.")

    # Step 5: Pooled effect and SE
    pooled_effect = np.sum(weights_random * effects) / sum_w_random
    pooled_se = np.sqrt(1.0 / sum_w_random)

    # Confidence interval
    z = 1.96 if ci_level == 0.95 else np.abs(np.percentile(np.random.randn(10000), [(1 - ci_level) / 2 * 100]))
    ci_low = pooled_effect - z * pooled_se
    ci_high = pooled_effect + z * pooled_se

    # Heterogeneity metrics
    if df > 0:
        I2 = max(0.0, (Q - df) / Q) * 100.0
        H = np.sqrt(Q / df)
    else:
        I2 = 0.0
        H = 1.0

    return PooledEffect(
        pooled_effect=float(pooled_effect),
        pooled_se=float(pooled_se),
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        tau2=float(tau2),
        Q=float(Q),
        I2=float(I2),
        H=float(H),
        k=k,
        model="random",
        warnings=warnings_list,
    )


def meta_analysis(
    effects: np.ndarray,
    ses: np.ndarray,
    model: str = "random",
    ci_level: float = 0.95,
    tau2_estimator: str = "DL",
) -> PooledEffect:
    """Perform meta-analysis with specified model.

    Args:
        effects: Array of effect estimates
        ses: Array of standard errors
        model: "fixed" or "random" (default "random")
        ci_level: Confidence interval level (default 0.95)
        tau2_estimator: τ² estimator for random-effects (default "DL")

    Returns:
        PooledEffect with pooling results

    Raises:
        ValueError: If model is not "fixed" or "random"
    """
    if model == "fixed":
        return fixed_effect_meta(effects, ses, ci_level)
    elif model == "random":
        return random_effects_meta(effects, ses, ci_level, tau2_estimator)
    else:
        raise ValueError(f"Invalid model: {model}. Must be 'fixed' or 'random'.")


def weighted_least_squares(
    y: np.ndarray, X: np.ndarray, weights: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Weighted least squares regression.

    Solves: β = (X'WX)^(-1) X'Wy
    where W = diag(weights)

    Args:
        y: Outcome vector (length n)
        X: Design matrix (n x p)
        weights: Weight vector (length n)

    Returns:
        Tuple of (coef, se, z_scores, p_values)
    """
    y = np.asarray(y, dtype=np.float64)
    X = np.asarray(X, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)

    # Weight matrices
    W = np.diag(weights)

    # Weighted normal equations
    XtWX = X.T @ W @ X
    XtWy = X.T @ W @ y

    # Solve for coefficients
    try:
        coef = np.linalg.solve(XtWX, XtWy)
    except np.linalg.LinAlgError:
        raise ValueError("Singular matrix in weighted least squares. Check for collinearity.")

    # Standard errors
    # Variance-covariance matrix: (X'WX)^(-1)
    try:
        vcov = np.linalg.inv(XtWX)
    except np.linalg.LinAlgError:
        raise ValueError("Cannot invert X'WX matrix.")

    se = np.sqrt(np.diag(vcov))

    # Z-scores and p-values (normal approximation)
    z_scores = coef / se
    # Two-tailed p-values
    from scipy.stats import norm

    p_values = 2 * (1 - norm.cdf(np.abs(z_scores)))

    return coef, se, z_scores, p_values
