## e2e decomposition -- blaz skrlj, 2018

import pandas as pd
from sklearn.model_selection import cross_val_score
from py3plex.core import multinet
from sklearn.decomposition import PCA
import json
from py3plex.algorithms.node_ranking import sparse_page_rank, stochastic_normalization_hin
from py3plex.algorithms.general.benchmark_classification import *
from functools import reduce
import itertools
import numpy as np
import multiprocessing as mp
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from scipy import optimize, sparse
from random import shuffle
#from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import KFold
from sklearn.cross_validation import train_test_split


def return_decomposed_matrix(input_tuple):

    #try:
    input_tuple = input_tuple
    heuristics_subset = np.rint(input_tuple[0:len(heuristics_set)])
    triplet_subset = np.rint(
        input_tuple[len(heuristics_set):(len(input_tuple - len(merge_set)))])
    mlen = len(input_tuple) - len(merge_set)
    ablen = len(input_tuple) - len(alpha_beta)
    merge_subset = np.rint(input_tuple[mlen:ablen])
    albeta = input_tuple[ablen:]

    heuristics = [i for (i, v) in zip(heuristics_set, heuristics_subset) if v]
    triplets = [i for (i, v) in zip(triplet_set, triplet_subset) if v]
    operators = [i for (i, v) in zip(merge_set, merge_subset) if v]

    outstring = " ".join(heuristics) + " ".join(triplets) + " ".join(
        operators) + " ".join(str(albeta))
    decomposed_matrices = []
    decomposed_label_matrix = None

    for decomposition in multilayer_network.get_decomposition(
            heuristic=heuristics,
            cycle=triplets,
            parallel=False,
            alpha=albeta[0],
            beta=albeta[1]):
        decomposed_matrices.append(decomposition[0])
        decomposed_label_matrix = decomposition[1]

    if len(decomposed_matrices) < 2:
        combined_matrix = multilayer_network.get_decomposition(
            heuristic=["idf", "rf"], cycle=triplets, parallel=False)
        combined_matrix = next(combined_matrix)[0]
    else:
        ## type of aggregation
        if len(operators) == 0:
            combined_matrix = reduce(lambda a, b: a + b, decomposed_matrices)

        elif operators[0] == "sum":
            combined_matrix = reduce(lambda a, b: a + b, decomposed_matrices)

        elif operators[0] == "prod":
            combined_matrix = reduce(lambda a, b: a * b, decomposed_matrices)

        elif operators[0] == "norm_sum":
            combined_matrix = reduce(
                lambda a, b: (a / a.max()) + (b / b.max()),
                decomposed_matrices)

        elif operators[0] == "norm_prod":
            combined_matrix = reduce(
                lambda a, b: (a / a.max()) * (b / b.max()),
                decomposed_matrices)

    return (combined_matrix, decomposed_label_matrix)

    # except:
    #     return (None,None)


def page_rank_kernel(index_row):
    pr = sparse_page_rank(normalized_aggregate, [index_row],
                          epsilon=1e-6,
                          max_steps=100000,
                          damping=0.90,
                          spread_step=10,
                          spread_percent=0.1,
                          try_shrink=True)

    norm = np.linalg.norm(pr, 2)
    if norm > 0:
        pr = pr / np.linalg.norm(pr, 2)
        return (index_row, pr)
    else:
        return (index_row, np.zeros(normalized_aggregate.shape[1]))


def get_f_measure(M, Tr):
    clf = OneVsRestClassifier(LogisticRegression())
    scores = cross_val_score(clf, M, Tr, cv=2, scoring='f1_macro')
    return np.mean(scores)


def scoring_function_f_measure(combined_matrix, decomposed_label_matrix):

    global normalized_aggregate
    normalized_aggregate = stochastic_normalization_hin(combined_matrix)
    n = normalized_aggregate.shape[1]
    vectors = np.zeros((n, n))
    with mp.Pool(processes=4) as p:
        results = p.map(page_rank_kernel, range(n))

    for pr_vector in results:
        if pr_vector != None:
            vectors[pr_vector[0], :] = pr_vector[1]
    try:
        fm = get_f_measure(vectors, decomposed_label_matrix)
        return fm
    except:
        return 0


def evaluate_triplet_heuristic_tuple(input_tuple):

    decomposed_matrix, labels = return_decomposed_matrix(input_tuple)
    if decomposed_matrix is None:
        return 0
    else:
        return scoring_function_f_measure(decomposed_matrix, labels)


def evolve_decomposition(
        multilayer_network,
        heuristics=["idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi"],
        merges=["sum", "prod", "norm_prod", "norm_sum"],
        alpha=1,
        beta=1,
        iterations=5,
        popsize=5):

    global triplet_set
    global heuristics_set
    global merge_set
    global alpha_beta

    heuristics_set = heuristics
    merge_set = merges
    multilayer_network.monitor("Starting evolution..")
    triplet_set = set(multilayer_network.get_decomposition_cycles())
    alpha_beta = [alpha, beta]
    input_array = np.random.randint(2,
                                    size=len(heuristics_set) +
                                    len(triplet_set) + len(merge_set) +
                                    len(alpha_beta))
    inputs = list(((0, 1) for x in input_array))
    res = optimize.differential_evolution(evaluate_triplet_heuristic_tuple,
                                          inputs,
                                          popsize=popsize,
                                          maxiter=iterations,
                                          disp=True)
    result_array = res['x']
    input_tuple = np.rint(result_array)
    heuristics_subset = input_tuple[0:len(heuristics_set)]
    triplet_subset = input_tuple[len(heuristics_set):(len(input_tuple -
                                                          len(merge_set)))]
    mlen = len(input_tuple) - len(merge_set)
    ablen = len(input_tuple) - len(alpha_beta)
    merge_subset = input_tuple[mlen:ablen]
    albeta = input_tuple[ablen:]
    heuristics = [i for (i, v) in zip(heuristics_set, heuristics_subset) if v]
    triplets = [i for (i, v) in zip(triplet_set, triplet_subset) if v]
    operators = [i for (i, v) in zip(merge_set, merge_subset) if v]
    outstring = " ".join(heuristics) + " ".join(triplets) + " ".join(
        operators) + " ".join(str(albeta)) + " " + str(res['fun'])

    return outstring


if __name__ == "__main__":

    import sys
    import warnings

    if not sys.warnoptions:
        warnings.simplefilter("ignore")

    np.random.seed(555)  # Seeded to allow replication.
    datasets = [
        "../datasets/imdb_gml.gml", "../datasets/labeled_epigenetics.gpickle"
    ]

    ## iterate through datasets..
    for en, dataset in enumerate(datasets):
        multilayer_network = multinet.multi_layer_network().load_network(
            input_file=dataset,
            directed=True,
            input_type=dataset.split(".")[-1])
        print("Running optimization for {}".format(dataset))
        multilayer_network.basic_stats()  ## check core import
        optimal_setting = evolve_decomposition(multilayer_network)
        print(optimal_setting)
