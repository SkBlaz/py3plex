## community-based semantic subgroup discovery (skrlj 2017) API. Note this does not include the biomine calls

## this works for UniProt identifiers TODO:generalize!

from py3plex.core import multinet
from py3plex.algorithms import hedwig
from py3plex.algorithms.community_detection import community_wrapper as cw

## load as undirected (simplified example)
network = multinet.multi_layer_network().load_network("../datasets/epigenetics.gpickle",directed=False, input_type="gpickle_biomine")

partition = cw.louvain_communities(network)

## convert examples to RDF mappings and check the validity, use gzipped gaf files..
dataset_name = "../datasets/example_partition_inputs.n3"
rdf_partitions = hedwig.convert_mapping_to_rdf(partition,annotation_mapping_file="../datasets/goa_human.gaf.gz")
rdf_partitions.serialize(destination = dataset_name, format="n3")

## convert obo file to n3
hedwig.obo2n3("../datasets/goslim_generic.obo", "../datasets/bk.n3", "../datasets/goa_human.gaf.gz")

## some default input parameters
hedwig_input_parameters = {"bk_dir": "../datasets", "data": "../datasets/example_partition_inputs.n3", "format": "n3", "output": None, "covered": None, "mode": "subgroups", "target": None, "score": "lift", "negations": True, "alpha": 0.05, "latex_report": False, "adjust": "fwer", "FDR": 0.05, "leaves": False, "learner": "heuristic", "optimalsubclass": False, "uris": False, "beam": 20, "support": 0.1, "depth": 5, "nocache": False, "verbose": False,"adjust":"none"}

hedwig.run(hedwig_input_parameters)


