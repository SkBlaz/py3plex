## decomposition with ground truth

from py3plex.core import multinet
from py3plex.algorithms.network_classification.PPR import *
from py3plex.visualization.benchmark_visualizations import *
from sklearn.svm import SVC
from sklearn.ensemble import ExtraTreesClassifier
#from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score
from sklearn.multiclass import OneVsRestClassifier

dataset = "../datasets/imdb.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(
    input_file=dataset, directed=True, input_type=dataset.split(".")[-1])

print("Running optimization for {}".format(dataset))
multilayer_network.basic_stats()  ## check core imports
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))
print("\n".join(triplet_set))
for decomposition in multilayer_network.get_decomposition(
        heuristic=["idf", "tf", "chi", "ig", "gr", "delta", "rf", "okapi"], cycle=triplet_set):
    print(decomposition)
