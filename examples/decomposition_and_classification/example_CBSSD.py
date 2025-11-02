# community-based semantic subgroup discovery (skrlj 2017) API. Note this does not include the biomine calls

# this works for UniProt identifiers TODO:generalize!

from py3plex.core import multinet
from py3plex.algorithms import hedwig
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.utils import get_dataset_path, get_data_path, get_background_knowledge_path

# load as undirected (simplified example)
network = multinet.multi_layer_network().load_network(
    get_dataset_path("intact02.gpickle"), directed=False, input_type="gpickle")

network.basic_stats()

partition = cw.louvain_communities(network)

# convert examples to RDF mappings and check the validity, use gzipped gaf files..
dataset_name = get_dataset_path("example_partition_inputs.n3")
print(partition)

rdf_partitions = hedwig.convert_mapping_to_rdf(
    partition,
    annotation_mapping_file=get_dataset_path("goa_human.gaf.gz"),
    layer_type="uniprotkb")
rdf_partitions.serialize(destination=dataset_name, format="n3")

# convert obo file to n3
hedwig.obo2n3(get_dataset_path("go.obo.gz"), get_data_path("background_knowledge/bk.n3"),
              get_dataset_path("goa_human.gaf.gz"))

# some default input parameters
hedwig_input_parameters = {
    "bk_dir": get_background_knowledge_path(""),
    "data": get_dataset_path("example_partition_inputs.n3"),
    "format": "n3",
    "output": None,
    "covered": None,
    "mode": "subgroups",
    "target": None,
    "score": "lift",
    "negations": True,
    "alpha": 0.05,
    "latex_report": False,
    "FDR": 0.05,
    "leaves": True,
    "learner": "heuristic",
    "optimalsubclass": False,
    "uris": False,
    "beam": 300,
    "support": 0.01,
    "depth": 8,
    "nocache": False,
    "verbose": False,
    "adjust": "none"
}

network.monitor("Starting rule learning")

# initiate the learning part (TODO: export this as table of some sort)
hedwig.run(hedwig_input_parameters)
