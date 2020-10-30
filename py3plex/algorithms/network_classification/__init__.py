# label propagation routines

# label propagation algorithms:
import pandas as pd
from sklearn.model_selection import ShuffleSplit
import numpy as np
import scipy.sparse as sp
import time
import multiprocessing as mp  # initialize the MP part
from sklearn.metrics import f1_score
import numpy as np
import scipy.sparse as sp


def label_propagation_normalization(matrix):
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
def normalize_initial_matrix_freq(mat):
    sums = np.sum(mat, axis=0)
    mat = mat / sums
    return mat


def normalize_amplify_freq(mat):
    sums = np.sum(mat, axis=0)
    mat = mat * sums
    return mat


def normalize_exp(mat):
    return np.exp(mat)


def label_propagation(graph_matrix,
                      class_matrix,
                      alpha,
                      epsilon=1e-12,
                      max_steps=100000,
                      normalization="freq"):

    # This method assumes the label-propagation normalization and a symmetric matrix with no rank sinks.
    diff = np.inf
    steps = 0
    current_labels = class_matrix

    if normalization == "freq":
        current_labels = normalize_initial_matrix_freq(current_labels)

    if normalization == "freq_amplify":
        current_labels = normalize_amplify_freq(current_labels)

    if normalization == "exp":
        current_labels = normalize_exp(current_labels)

    while diff > epsilon and steps < max_steps:
        steps += 1
        new_labels = alpha * graph_matrix.dot(current_labels) + (
            1 - alpha) * class_matrix
        diff = np.linalg.norm(new_labels -
                              current_labels) / np.linalg.norm(new_labels)
        current_labels = new_labels
    return current_labels


def validate_label_propagation(core_network,
                               labels,
                               dataset_name="test",
                               repetitions=5,
                               normalization_scheme="basic",
                               alpha_value=0.001,
                               random_seed=123):

    try:
        labels = labels.todense()
    except:
        pass

    matrix = label_propagation_normalization(core_network)
    print("Propagation..")
    results = []
    df = pd.DataFrame()
    for k in range(repetitions):
        for j in np.arange(0.1, 1, 0.1):
            print("Train size:{}, method {}".format(j, normalization_scheme))
            rs = ShuffleSplit(n_splits=10,
                              test_size=j,
                              random_state=random_seed)
            micros = []
            macros = []
            times = []
            for X_train, X_test in rs.split(labels):
                start = time.time()
                tmp_labels = labels.copy()
                true_labels = tmp_labels[X_test].copy()
                tmp_labels[X_test] = 0
                probs = label_propagation(matrix,
                                          tmp_labels,
                                          alpha=alpha_value,
                                          normalization=normalization_scheme)

                y_test = [[] for _ in range(labels.shape[0])]
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
                micro = f1_score(true_labels,
                                 predicted_labels,
                                 average='micro')
                macro = f1_score(true_labels,
                                 predicted_labels,
                                 average='macro')
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
                "time": np.mean(times)
            }
            results.append(outarray)
            df = df.append(outarray, ignore_index=True)

    df = df.reset_index()
    return df


def label_propagation_tf():
    # todo..
    pass
