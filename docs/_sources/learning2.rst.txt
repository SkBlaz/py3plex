Learning - label propagation
=====================

Learning propagation is one of the simplest learning processes one can conduct on labeled networks. Py3plex offers off-the-shelf validation procedures for evaluating multiple variants of LP!

.. code-block:: python
   :linenos:

	from py3plex.core import multinet
	from py3plex.algorithms.network_classification import *
	from py3plex.visualization.benchmark_visualizations import *
	import scipy
	import pandas as pd

	multilayer_network = multinet.multi_layer_network().load_network("../datasets/cora.mat",directed=False, input_type="sparse")

	## WARNING: sparse matrices are meant for efficiency. Many operations with standard px objects are hence not possible, e.g., basic_stats()...

	## different heuristic-based target weights..
	normalization_schemes = ["freq","basic","freq_amplify","exp"]
	result_frames = []

	for scheme in normalization_schemes:
		result_frames.append(validate_label_propagation(multilayer_network.core_network,multilayer_network.labels,dataset_name="cora_classic",repetitions=5,normalization_scheme=scheme))

	## results frame
	validation_results = pd.DataFrame()

	## construct a single dataframe
	for x in result_frames:
		validation_results = validation_results.append(x,ignore_index=True)

	validation_results.reset_index()

	## plot results
	plot_core_macro(validation_results)

.. image:: ../example_images/learning_lp.png
   :width: 500
