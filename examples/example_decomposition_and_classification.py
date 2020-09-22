## first decompose, then classify!

from py3plex.core import multinet
from py3plex.algorithms.network_classification import PPR
from sklearn.svm import SVC
from sklearn.metrics import f1_score
import time
import numpy as np
import multiprocessing as mp
import pandas as pd
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.multiclass import OneVsRestClassifier
from sklearn import preprocessing
import matplotlib.pyplot as plt
import seaborn as sns

## a simple decomposition example. Note that target nodes need to have "labels" property, to which labels are assigned in class1---class2---...and so on...

dataset = "../datasets/imdb.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, directed=True, input_type=dataset.split(".")[-1])

print("Running optimization for {}".format(dataset))
multilayer_network.basic_stats()  ## check core imports
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))

df = pd.DataFrame()
heuristics = ["idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi"]
for decomposition in multilayer_network.get_decomposition(
        heuristic=heuristics, cycle=triplet_set):

    decomposed_network = decomposition[0]
    labels = decomposition[1][:,1] ## let's predict one target
    
    vectors = PPR.construct_PPR_matrix(decomposed_network)
    heuristic = decomposition[2]
    micros = []
    macros = []
    times = []
    
    for test_size in np.arange(0.1,1,0.1):
        j = 1 - test_size
        rs = StratifiedShuffleSplit(n_splits=10,
                                    test_size=test_size,
                                    random_state=612312)

        for X_train, X_test in rs.split(vectors, labels):
            start = time.time()
            train_x = vectors[X_train]
            test_x = vectors[X_test]

            train_labels = labels[X_train]
            test_labels = labels[X_test]

            clf = SVC()
            clf.fit(train_x, train_labels)
            preds = clf.predict(test_x)

            mi = f1_score(test_labels, preds, average='micro')
            ma = f1_score(test_labels, preds, average='macro')

            ## train the model
            end = time.time()
            elapsed = end - start
            micros.append(mi)
            macros.append(ma)
            times.append(elapsed)
        outarray = {
            "percent_train": np.round(1 - j, 1),
            "micro_F": np.mean(micros),
            "macro_F": np.mean(macros),
            "setting": "PPR",
            "time": np.mean(times),
            "heuristic":heuristic
        }
        df = df.append(outarray, ignore_index=True)

print(df)

sns.lineplot(df.percent_train, df.micro_F, hue = df.heuristic)
plt.show()
