## decomposition via different meta paths

from py3plex.core import multinet
from py3plex.algorithms.network_classification import PPR
from sklearn.svm import SVC
from sklearn.metrics import f1_score
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
import matplotlib.pyplot as plt
import seaborn as sns

# a simple decomposition example. Note that target nodes need to have "labels" property, to which labels are assigned in class1---class2---...and so on...

dataset = "../datasets/imdb.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, directed=True, input_type=dataset.split(".")[-1])

print("Running optimization for {}".format(dataset))
multilayer_network.basic_stats()  # check core imports
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))

for tcycle in triplet_set:
    print(tcycle)
    for decomposition in multilayer_network.get_decomposition(heuristic=["tf"],
                                                              cycle=[tcycle]):
        network = decomposition[0]
        print(network.todense())
