## label propagation routines

## label propagation algorithms:
import networkx as nx
import numpy as np
import scipy.sparse as sp
import time
import multiprocessing as mp ## initialize the MP part
import mkl

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

def pr_kernel(index_row):
    pr = sparse_page_rank(graph, [index_row],
                          epsilon=1e-6,
                          max_steps=100000,
                          try_shrink=True)
    
    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row,pr)
    else:
        return (index_row,np.zeros(graph.shape[1]))
    
## dodaj numba compiler tule
def label_propagation(graph_matrix, class_matrix, alpha, epsilon=1e-12, max_steps=100000):
    # This method assumes the label-propagation normalization and a symmetric matrix with no rank sinks.

    ## zracunej pageranke            
    diff = np.inf
    steps = 0
    current_labels = class_matrix
    while diff > epsilon and steps < max_steps:
        steps += 1
        new_labels = alpha * graph_matrix.dot(current_labels) + (1 - alpha) * class_matrix
        diff = np.linalg.norm(new_labels - current_labels) / np.linalg.norm(new_labels)
        current_labels = new_labels
    
    return current_labels

