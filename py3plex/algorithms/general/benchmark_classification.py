# algorithms for benchmarking node performance

from sklearn.metrics import f1_score
import numpy as np
import scipy.sparse as sp


def evaluate_oracle_F1(probs, Y_real):

    y_test = [[] for _ in range(Y_real.shape[0])]
    cy = sp.csr_matrix(Y_real).tocoo()
    for i, b in zip(cy.row, cy.col):
        y_test[i].append(b)
    top_k_list = [len(l) for l in y_test]
    assert Y_real.shape[0] == len(top_k_list)
    predictions = []
    for i, k in enumerate(top_k_list):
        probs_ = probs[i, :]
        a = np.zeros(probs.shape[1])
        labels_tmp = probs_.argsort()[-k:]
        a[labels_tmp] = 1
        predictions.append(a)
    predictions = np.matrix(predictions)

    micro = f1_score(Y_real, predictions, average='micro')
    macro = f1_score(Y_real, predictions, average='macro')
    return (micro, macro)
