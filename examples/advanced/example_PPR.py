"""Example: Personalized PageRank for Node Classification

This example demonstrates how to:
- Load a sparse network (CORA citation network)
- Use Personalized PageRank (PPR) as feature vectors
- Train a multiclass SVM classifier
- Validate classification performance with cross-validation
- Visualize benchmark results

PPR embeddings capture local network structure around each node,
making them effective features for node classification tasks.
The CORA dataset contains scientific papers with citation links
and ground-truth topic labels.

Note: This example uses a linear SVM kernel which works well
for multiclass (not multilabel) classification problems.
"""
# SKIP_CI: slow - PPR validation takes more than 10 seconds

from py3plex.core import multinet
from py3plex.algorithms.network_classification.PPR import *
from py3plex.visualization.benchmark_visualizations import *
from sklearn.svm import SVC
from py3plex.utils import get_dataset_path

# load a sparse network
multilayer_network = multinet.multi_layer_network().load_network(
    get_dataset_path("cora.mat"), directed=False, input_type="sparse")

# this can take some time!
model = SVC(kernel='linear', C=1, probability=True)

# This setting works for multiclass classifiers, and NOT MULTILABEL.

# validate PPR embeddings
validation_results = validate_ppr(multilayer_network.core_network,
                                  multilayer_network.labels,
                                  multiclass_classifier=model,
                                  repetitions=2)

# plot the results
plot_core_macro(validation_results)
