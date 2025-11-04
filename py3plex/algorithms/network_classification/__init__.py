# label propagation routines

# Import the actual implementations from label_propagation module
from .label_propagation import (
    label_propagation,
    label_propagation_normalization,
    normalize_amplify_freq,
    normalize_exp,
    normalize_initial_matrix_freq,
    validate_label_propagation,
)

# label propagation algorithms:
import time
from typing import Any, List, Optional

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.metrics import f1_score
from sklearn.model_selection import ShuffleSplit


def benchmark_classification(
    matrix: sp.spmatrix,
    labels: np.ndarray,
    alpha_value: float = 0.85,
    iterations: int = 30,
    normalization_scheme: str = "freq",
    dataset_name: str = "example",
    verbose: bool = False,
    test_size: Optional[float] = None,
) -> pd.DataFrame:

    # check whether this is integer-based partitioning..
    if test_size is not None:

        micros = []
        macros = []
        times = []
        cv = ShuffleSplit(
            n_splits=iterations, test_size=test_size, random_state=0
        )  # single iteration.
        if verbose:
            print(f"Starting evaluation on {dataset_name} with {iterations} splits..")
        train_space = np.arange(labels.shape[0])
        for _, test_index in cv.split(train_space):
            start = time.time()
            tmp_labels = labels.copy()
            X_test = test_index
            true_labels = tmp_labels[X_test].copy()
            tmp_labels[X_test] = 0
            probs = label_propagation(
                matrix,
                tmp_labels,
                alpha=alpha_value,
                normalization=normalization_scheme,
            )

            y_test: List[List[Any]] = [[] for _ in range(labels.shape[0])]
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
            "percent_train": 1 - test_size,
            "micro_F": np.mean(micros),
            "macro_F": np.mean(macros),
            "setting": "LP_" + normalization_scheme,
            "dataset": dataset_name,
            "time": np.mean(times),
        }
        df = pd.DataFrame(columns=["percent_train", "micro_F", "macro_F", "setting", "dataset", "time"])
        df = pd.concat([df, pd.DataFrame([outarray])], ignore_index=True)
        return df

    else:
        df = pd.DataFrame()
        results = []
        for j in np.arange(0.1, 0.9, 0.1):
            micros = []
            macros = []
            times = []
            cv = ShuffleSplit(
                n_splits=iterations, test_size=j, random_state=0
            )  # single iteration.
            if verbose:
                print("Doing one with test size {}.".format(j))
            train_space = np.arange(labels.shape[0])
            for _, test_index in cv.split(train_space):
                start = time.time()
                tmp_labels = labels.copy()
                X_test = test_index
                true_labels = tmp_labels[X_test].copy()
                tmp_labels[X_test] = 0
                probs = label_propagation(
                    matrix,
                    tmp_labels,
                    alpha=alpha_value,
                    normalization=normalization_scheme,
                )

                y_test: List[List[Any]] = [[] for _ in range(labels.shape[0])]
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
                "setting": "LP_" + normalization_scheme,
                "dataset": dataset_name,
                "time": np.mean(times),
            }
            results.append(outarray)
            df = pd.concat([df, pd.DataFrame([outarray])], ignore_index=True)

    df = df.reset_index()
    return df


def label_propagation_tf() -> None:
    # todo..
    pass


__all__ = [
    "label_propagation",
    "label_propagation_normalization",
    "normalize_initial_matrix_freq",
    "normalize_amplify_freq",
    "normalize_exp",
    "benchmark_classification",
    "label_propagation_tf",
    "validate_label_propagation",
]
