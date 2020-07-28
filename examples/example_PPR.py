## personalized pagerank for node classification

from py3plex.core import multinet
from py3plex.algorithms.network_classification.PPR import *
from py3plex.visualization.benchmark_visualizations import *
from sklearn.svm import SVC

## load a sparse network
multilayer_network = multinet.multi_layer_network().load_network(
    "../datasets/cora.mat", directed=False, input_type="sparse")

## this can take some time!
model = SVC(kernel='linear', C=1, probability=True)

## This setting works for multiclass classifiers, and NOT MULTILABEL.

## validate PPR embeddings
validation_results = validate_ppr(multilayer_network.core_network,
                                  multilayer_network.labels,
                                  multiclass_classifier=model,
                                  repetitions=2)

## plot the results
plot_core_macro(validation_results)
