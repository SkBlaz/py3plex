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
from typing import Tuple
from dataclasses import dataclass
from scipy.stats import norm, t


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
        z = norm.isf((1 - ci_level) / 2)
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
    z = norm.isf((1 - ci_level) / 2)
    ci_low = pooled_effect - z * pooled_se
    ci_high = pooled_effect + z * pooled_se

    # Heterogeneity: Cochran's Q
    Q = np.sum(weights * (effects - pooled_effect) ** 2)
    df = k - 1

    # I² and H
    if df > 0:
        I2 = max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0
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
        z = norm.isf((1 - ci_level) / 2)
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
    z = norm.isf((1 - ci_level) / 2)
    ci_low = pooled_effect - z * pooled_se
    ci_high = pooled_effect + z * pooled_se

    # Heterogeneity metrics
    if df > 0:
        I2 = max(0.0, (Q - df) / Q) * 100.0 if Q > 0 else 0.0
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
    y: np.ndarray, X: np.ndarray, weights: np.ndarray, *, absolute_weights: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Weighted least squares regression.

    Solves: β = (X'WX)^(-1) X'Wy
    where W = diag(weights)

    Args:
        y: Outcome vector (length n)
        X: Design matrix (n x p)
        weights: Weight vector (length n)
        absolute_weights: Treat weights as inverse known variances. Otherwise
            estimate the residual scale and use Student t tail probabilities.

    Returns:
        Tuple of (coef, se, z_scores, p_values)
    """
    y = np.asarray(y, dtype=np.float64)
    X = np.asarray(X, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)

    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError("Regression weights must be finite and positive.")
    root_weights = np.sqrt(weights)
    design = X * root_weights[:, None]
    outcome = y * root_weights
    coef, _, rank, _ = np.linalg.lstsq(design, outcome, rcond=None)
    if rank < X.shape[1]:
        raise ValueError("Singular matrix in weighted least squares. Check for collinearity.")

    _, triangular = np.linalg.qr(design, mode="reduced")
    inverse = np.linalg.solve(triangular, np.eye(X.shape[1]))
    variance = np.sum(inverse**2, axis=1)
    if not absolute_weights:
        df = len(y) - rank
        if df <= 0:
            raise ValueError("Residual variance requires positive residual degrees of freedom.")
        residuals = outcome - design @ coef
        variance *= residuals @ residuals / df

    se = np.sqrt(variance)
    with np.errstate(divide="ignore", invalid="ignore"):
        scores = coef / se
    p_values = 2 * (norm.sf(np.abs(scores)) if absolute_weights else t.sf(np.abs(scores), df))
    return coef, se, scores, p_values
