# implement scale free network estimation
# do this according to the paper WCGA

from collections import Counter

import numpy as np
from scipy import stats

from ...logging_config import get_logger

logger = get_logger(__name__)


def pick_threshold(matrix: np.ndarray) -> float:
    """
    Pick optimal threshold for correlation network construction.

    Args:
        matrix: Input data matrix

    Returns:
        Optimal threshold value
    """
    current_r_opt = 0
    rho, pval = stats.spearmanr(matrix)
    for j in np.linspace(0, 1, 50):
        tmp_array = rho.copy()
        tmp_array[tmp_array > j] = 1
        tmp_array[tmp_array < j] = 0
        np.fill_diagonal(tmp_array, 0)  # self loops
        rw_sum = np.sum(tmp_array, axis=0)
        count_dict = Counter(rw_sum)
        key_counts = np.log(np.fromiter(count_dict.keys(), dtype=float))
        counts = np.log(np.fromiter(count_dict.values(), dtype=float))
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            key_counts, counts
        )
        if r_value > current_r_opt:
            logger.debug("Updating R^2: %s", r_value)
            current_r_opt = r_value
        if r_value > 0.80:
            return float(j)
    return float(current_r_opt)


def default_correlation_to_network(
    matrix: np.ndarray, input_type: str = "matrix", preprocess: str = "standard"
) -> np.ndarray:
    """
    Convert correlation matrix to network using optimal thresholding.

    Args:
        matrix: Input data matrix
        input_type: Type of input (default: "matrix")
        preprocess: Preprocessing method (default: "standard")

    Returns:
        Binary adjacency matrix
    """
    if preprocess == "standard":
        std = np.std(matrix, axis=0)
        # Avoid division by zero for columns with constant values
        std = np.where(std == 0, 1, std)
        matrix = (matrix - np.mean(matrix, axis=0)) / std

    optimal_threshold = pick_threshold(matrix)
    logger.info("Rsq threshold %s", optimal_threshold)
    matrix[matrix > optimal_threshold] = 1
    matrix[matrix < optimal_threshold] = 0
    return matrix


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
