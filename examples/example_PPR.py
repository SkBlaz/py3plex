## personalized pagerank for node classification

from py3plex.core import multinet
from py3plex.algorithms.network_classification.PPR import *
from py3plex.visualization.benchmark_visualizations import *
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

## load a sparse network
multilayer_network = multinet.multi_layer_network().load_network("../datasets/cora.mat",directed=False, input_type="sparse")

## select the classifier and hypertune it..
param_grid = [
  {'C': [1, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']},
 ]

## this can take some time!
svc = SVC(kernel = 'linear', C = 1,probability=True)
core_classifier = GridSearchCV(estimator=svc, param_grid=param_grid,n_jobs=1)
model= OneVsRestClassifier(core_classifier,n_jobs=4)

## validate PPR embeddings
validation_results = validate_ppr(multilayer_network.core_network,multilayer_network.labels,multiclass_classifier=model)

## plot the results
plot_core_macro(validation_results)

