## algorithms for benchmarking node performance

from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
import numpy as np
import scipy.sparse as sp

class TopKRanker(OneVsRestClassifier):
    def predict(self, X, top_k_list):
        assert X.shape[0] == len(top_k_list)
        probs = numpy.asarray(super(TopKRanker, self).predict_proba(X))
        all_labels = []
        for i, k in enumerate(top_k_list):
            probs_ = probs[i, :]
            labels = self.classes_[probs_.argsort()[-k:]].tolist()
            all_labels.append(labels)
        return all_labels


def evaluate_oracle_F1(model,X,Y_real):

    probs = np.asarray(model.predict_proba(X))
    all_labels = []
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
    return(micro)
