# implement scale free network estimation
# do this according to the paper WCGA

from collections import Counter

import numpy as np
from scipy import stats

from ...logging_config import get_logger

logger = get_logger(__name__)


def _spearman_matrix(observations: np.ndarray) -> np.ndarray:
    data = np.asarray(observations, dtype=float)
    if data.ndim != 2:
        raise ValueError("Expected a matrix of observations by variables.")
    n_features = data.shape[1]
    if data.shape[0] < 2:
        return np.zeros((n_features, n_features))
    if not np.isfinite(data).all():
        raise ValueError("Correlation observations must be finite.")
    ranks = stats.rankdata(data, axis=0)
    centered = ranks - ranks.mean(axis=0)
    norms = np.linalg.norm(centered, axis=0)
    normalized = centered / np.where(norms > 0, norms, 1)
    return np.clip(normalized.T @ normalized, -1, 1)


def pick_threshold(matrix: np.ndarray) -> float:
    """Select a positive correlation threshold from a matrix of observations."""
    data = np.asarray(matrix)
    if data.ndim != 2 or data.shape[1] < 2:
        return 0.0
    return _threshold_from_correlation(_spearman_matrix(data))


def _threshold_from_correlation(correlation):
    best_threshold, best_score = 0.0, 0.0
    for threshold in np.linspace(0, 1, 50, endpoint=False):
        adjacency = correlation > threshold
        np.fill_diagonal(adjacency, False)
        frequencies = Counter(degree for degree in adjacency.sum(axis=0) if degree > 0)
        if len(frequencies) < 2:
            continue
        fit = stats.linregress(
            np.log(list(frequencies)), np.log(list(frequencies.values()))
        )
        score = fit.rvalue**2 if fit.slope < 0 else 0.0
        if score > best_score:
            best_threshold, best_score = float(threshold), score
        if score > 0.8:
            return float(threshold)
    return best_threshold


def default_correlation_to_network(
    matrix: np.ndarray, input_type: str = "matrix", preprocess: str = "standard"
) -> np.ndarray:
    """Return a binary symmetric adjacency over the input variables.

    A matrix of observations has shape (observations, variables). For
    input_type="correlation", pass a symmetric precomputed correlation matrix.
    Standardizing variables does not change Spearman ranks.
    """
    if preprocess not in {"standard", "none"}:
        raise ValueError(f"Unknown preprocess mode: {preprocess}")
    if input_type == "matrix":
        correlation = _spearman_matrix(matrix)
        threshold = _threshold_from_correlation(correlation)
    elif input_type == "correlation":
        correlation = np.asarray(matrix, dtype=float)
        if (correlation.ndim != 2 or correlation.shape[0] != correlation.shape[1]
                or not np.isfinite(correlation).all() or not np.allclose(correlation, correlation.T)
                or np.any(np.abs(correlation) > 1)):
            raise ValueError("Expected a symmetric finite correlation matrix with values in [-1, 1].")
        threshold = _threshold_from_correlation(correlation)
    else:
        raise ValueError(f"Unknown input type: {input_type}")
    adjacency = (correlation > threshold).astype(np.int8)
    np.fill_diagonal(adjacency, 0)
    return adjacency


if __name__ == "__main__":
    import argparse

    from numpy import genfromtxt

    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", default="/home/skblaz/Downloads/expression.tsv")
    args = parser.parse_args()
    datta = args.filename
    a = genfromtxt(datta, delimiter="\t", skip_header=4)
    a = np.nan_to_num(a)
    logger.info("Read the data..")
    logger.info("Network shape: %s", default_correlation_to_network(a).shape)
