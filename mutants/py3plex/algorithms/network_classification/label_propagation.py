# label propagation routines

# label propagation algorithms:
import time
from typing import List, Union, cast

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.metrics import f1_score
from sklearn.model_selection import ShuffleSplit


def label_propagation_normalization(matrix: sp.spmatrix) -> sp.spmatrix:
    """Normalize a matrix for label propagation.

    Args:
        matrix: Sparse matrix to normalize

    Returns:
        Normalized sparse matrix
    """
    matrix = matrix.tocsr()
    try:
        matrix.setdiag(0)
    except TypeError:
        matrix.setdiag(np.zeros(matrix.shape[0]))
    d = matrix.sum(axis=1).getA1()
    nzs = np.where(d > 0)
    d[nzs] = 1 / np.sqrt(d[nzs])
    dm = sp.diags(d, 0).tocsc()
    return dm.dot(matrix).dot(dm)


# suggested as part of the hinmine..
def normalize_initial_matrix_freq(mat: np.ndarray) -> np.ndarray:
    """Normalize matrix by frequency.

    Args:
        mat: Matrix to normalize

    Returns:
        Normalized matrix
    """
    sums = np.sum(mat, axis=0)
    mat = mat / sums
    return mat


def normalize_amplify_freq(mat: np.ndarray) -> np.ndarray:
    """Normalize and amplify matrix by frequency.

    Args:
        mat: Matrix to normalize

    Returns:
        Normalized and amplified matrix
    """
    sums = np.sum(mat, axis=0)
    mat = mat * sums
    return mat


def normalize_exp(mat: np.ndarray) -> np.ndarray:
    """Apply exponential normalization.

    Args:
        mat: Matrix to normalize

    Returns:
        Exponentially normalized matrix
    """
    return cast(np.ndarray, np.exp(mat))


def normalize_none(mat: np.ndarray) -> np.ndarray:
    """No normalization (identity function).

    Args:
        mat: Matrix to return unchanged

    Returns:
        Original matrix
    """
    return mat


def label_propagation(
    graph_matrix: sp.spmatrix,
    class_matrix: np.ndarray,
    alpha: float = 0.001,
    epsilon: float = 1e-12,
    max_steps: int = 100000,
    normalization: Union[str, List[str]] = "freq",
) -> np.ndarray:
    """Propagate labels through a graph.

    Args:
        graph_matrix: Sparse graph adjacency matrix
        class_matrix: Initial class label matrix
        alpha: Propagation weight parameter
        epsilon: Convergence threshold
        max_steps: Maximum number of iterations
        normalization: Normalization scheme(s) to apply

    Returns:
        Propagated label matrix
    """

    # This method assumes the label-propagation normalization and a symmetric matrix with no rank sinks.

    funHash = {
        "freq": normalize_initial_matrix_freq,
        "freqAmplify": normalize_amplify_freq,
        "exp": normalize_exp,
        "basic": normalize_none,
    }

    diff = np.inf
    steps = 0
    current_labels = class_matrix

    for candidate in normalization:
        normalization_func = funHash[candidate]
        current_labels = normalization_func(current_labels)

    while diff > epsilon and steps < max_steps:
        steps += 1
        new_labels = (
            alpha * graph_matrix.dot(current_labels) + (1 - alpha) * class_matrix
        )
        diff = np.linalg.norm(new_labels - current_labels) / np.linalg.norm(new_labels)
        current_labels = new_labels

    return current_labels


def validate_label_propagation(
    core_network: sp.spmatrix,
    labels: Union[np.ndarray, sp.spmatrix],
    dataset_name: str = "test",
    repetitions: int = 5,
    normalization_scheme: Union[str, List[str]] = "basic",
    alpha_value: float = 0.001,
    random_seed: int = 123,
    verbose: bool = False,
) -> pd.DataFrame:
    """Validate label propagation with cross-validation.

    Args:
        core_network: Sparse network adjacency matrix
        labels: Label matrix
        dataset_name: Name of the dataset
        repetitions: Number of repetitions
        normalization_scheme: Normalization scheme to use
        alpha_value: Alpha parameter for propagation
        random_seed: Random seed for reproducibility
        verbose: Whether to print progress

    Returns:
        DataFrame with validation results
    """

    try:
        labels = labels.todense()  # type: ignore[union-attr]
    except AttributeError:
        pass

    matrix = label_propagation_normalization(core_network)
    if verbose:
        print("Propagation..")
    results = []
    df = pd.DataFrame()
    for k in range(repetitions):
        for j in np.arange(0.1, 1, 0.1):
            if verbose:
                print(f"Train size:{np.round(j, 2)}, method {normalization_scheme}")
            rs = ShuffleSplit(n_splits=10, test_size=j, random_state=random_seed)
            micros = []
            macros = []
            times = []
            for _X_train, X_test in rs.split(labels):
                start = time.time()
                tmp_labels = labels.copy()
                true_labels = tmp_labels[X_test].copy()
                tmp_labels[X_test] = 0
                probs = label_propagation(
                    matrix,
                    tmp_labels,
                    alpha=alpha_value,
                    normalization=normalization_scheme,
                )

                y_test: List[List[int]] = [[] for _ in range(labels.shape[0])]
                cy = sp.csr_matrix(labels).tocoo()
                for i, b in zip(cy.row, cy.col):
                    y_test[i].append(b)
                top_k_list = [len(l) for l in y_test]
                assert labels.shape[0] == len(top_k_list)
                predictions = []
                for i, k in enumerate(top_k_list):
                    probs_ = probs[i, :]
                    a = np.zeros(probs.shape[1])
                    labels_tmp = probs_.argsort()[-k:]
                    a[labels_tmp] = 1
                    predictions.append(a)

                predicted_labels = np.matrix(predictions)[X_test]
                micro = f1_score(true_labels, predicted_labels, average="micro")
                macro = f1_score(true_labels, predicted_labels, average="macro")
                end = time.time()
                elapsed = end - start
                micros.append(micro)
                macros.append(macro)
                times.append(elapsed)

            outarray = {
                "percent_train": np.round(1 - j, 1),
                "micro_F": np.mean(micros),
                "macro_F": np.mean(macros),
                "setting": "LP_" + "_".join(normalization_scheme),
                "dataset": dataset_name,
                "time": np.mean(times),
                "alpha": alpha_value,
            }
            results.append(outarray)
            df = df.append(outarray, ignore_index=True)

    df = df.reset_index()
    return df


def label_propagation_tf() -> None:
    """TensorFlow-based label propagation (TODO: implement).

    Placeholder for future TensorFlow implementation.
    """
    # todo..
    pass
