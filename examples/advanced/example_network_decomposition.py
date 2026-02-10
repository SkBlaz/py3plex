"""Example: Network Decomposition for Classification

This example demonstrates how to:
- Load a heterogeneous network (IMDB with actors/movies/directors)
- Decompose network into homogeneous projections
- Validate label propagation classification on each projection
- Compare classification performance across decompositions

Network decomposition extracts different views of a heterogeneous
network, each capturing specific relationship patterns. By testing
classification on each view, we can identify which relationships
are most predictive for the task.

The IMDB network is decomposed and validated using:
- Label propagation classifier
- 5-fold cross-validation
- Frequency normalization for feature vectors

Results show which meta-paths (relationship patterns) are most
informative for predicting node labels.
"""
# SKIP_CI: slow - Network decomposition and validation takes more than 10 seconds

#from py3plex.algorithms import *
from py3plex.core import multinet
from py3plex.algorithms.network_classification import *
from py3plex.visualization.benchmark_visualizations import *
import pandas as pd
from py3plex.utils import get_dataset_path

multilayer_network = multinet.multi_layer_network().load_network(
    input_file=get_dataset_path("imdb_gml.gml"), directed=True, input_type="gml")

## import status
result_frames = []
multilayer_network.basic_stats()  # check core imports
for decomposition in multilayer_network.get_decomposition():

    result_frames.append(
        validate_label_propagation(decomposition[0],
                                   decomposition[1],
                                   dataset_name="imdb_classic",
                                   repetitions=5,
                                   normalization_scheme="freq"))

    # results frame (placeholder for type consistency)
    validation_results = pd.DataFrame()

# construct a single dataframe using pd.concat
validation_results = pd.concat(result_frames, ignore_index=True)
print(validation_results)
