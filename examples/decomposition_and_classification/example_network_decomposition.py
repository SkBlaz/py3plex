# decompose a complex network into a simple, homogeneous network according to a heuristic

#from py3plex.algorithms import *
from py3plex.core import multinet
from py3plex.algorithms.network_classification import *
from py3plex.visualization.benchmark_visualizations import *
import pandas as pd

multilayer_network = multinet.multi_layer_network().load_network(
    input_file="../datasets/imdb_gml.gml", directed=True, input_type="gml")

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

    # results frame
    validation_results = pd.DataFrame()

# construct a single dataframe
for x in result_frames:
    validation_results = validation_results.append(x, ignore_index=True)
print(validation_results)
