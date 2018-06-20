# *Py3Plex* - a library for analysis and visualization of heterogeneous networks

Heterogeneous networks are complex networks with additional information assigned to nodes or edges (or both). This library includes
some of the state-of-the-art algorithms for decomposition, visualization and analysis of such algorithms.

![Multilayer networks](example_images/biomine_community.png)
![Single layer network](example_images/snps_data.png)

## Getting Started

To get started, please view **examples** folder.
### Prerequisites

1. Networkx (2.1)
2. Numpy (0.8)
3. Scipy  (1.1.0)
4. RDFlib (for ontology-based tasks) (any)

### Installing

To install, simply:

```
python3 setup.py install
```

### Examples

Here are some showcase examples!

**Some simple statistics**
```python
from py3plex.core import multinet
from py3plex.algorithms.statistics import *

multilayer_network = multinet.multi_layer_network().load_network("../datasets/imdb_gml.gml",directed=True,input_type="gml")

stats_frame = core_network_statistics(multilayer_network.core_network)
print(stats_frame)
```


**Network decomposition**
```python
from py3plex.core import multinet
from py3plex.algorithms.node_ranking import sparse_page_rank, stochastic_normalization_hin
from py3plex.algorithms.benchmark_classification import *

dataset = "../datasets/labeled_epigenetics.gpickle"

multilayer_network = multinet.multi_layer_network().load_network(input_file=dataset,directed=True,input_type=dataset.split(".")[-1])

print ("Running optimization for {}".format(dataset))
multilayer_network.basic_stats() ## check core imports        
triplet_set = list(set(multilayer_network.get_decomposition_cycles()))
print(triplet_set)
for decomposition in multilayer_network.get_decomposition(heuristic=["idf","rf"], cycle=triplet_set, parallel=True):
    print(decomposition)
```

**Multilayer visualization**


```python
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names
from py3plex.core import multinet

## multilayer
multilayer_network = multinet.multi_layer_network().load_network("../datasets/epigenetics.gpickle",directed=False, input_type="gpickle_biomine")
multilayer_network.basic_stats() ## check core imports
network_labels, graphs, multilinks = multilayer_network.get_layers() ## get layers for visualization
#print(network_labels,graphs)
draw_multilayer_default(graphs,display=False,background_shape="circle",labels=network_labels)

enum = 1
color_mappings = {idx : col for idx, col in enumerate(list(all_color_names.keys()))}
for edge_type,edges in multilinks.items():
    draw_multiedges(graphs,edges,alphachannel=0.7,linepoints="-.",linecolor=color_mappings[enum],curve_height=5,linmod="upper",linewidth=0.4)
    enum+=1
plt.show()
```

# Citation

```
@InProceedings{10.1007/978-3-319-78680-3_13,
author="{\v{S}}krlj, Bla{\v{z}}
and Kralj, Jan
and Vavpeti{\v{c}}, An{\v{z}}e
and Lavra{\v{c}}, Nada",
editor="Appice, Annalisa
and Loglisci, Corrado
and Manco, Giuseppe
and Masciari, Elio
and Ras, Zbigniew W.",
title="Community-Based Semantic Subgroup Discovery",
booktitle="New Frontiers in Mining Complex Patterns",
year="2018",
publisher="Springer International Publishing",
address="Cham",
pages="182--196",
abstract="Modern data mining algorithms frequently need to address learning from heterogeneous data and knowledge sources, including ontologies. A data mining task in which ontologies are used as background knowledge is referred to as semantic data mining. A special form of semantic data mining is semantic subgroup discovery, where ontology terms are used in subgroup describing rules. We propose to enhance ontology-based subgroup identification by Community-Based Semantic Subgroup Discovery (CBSSD), taking into account also the structural properties of complex networks related to the studied phenomenon. The application of the developed CBSSD approach is demonstrated on two use cases from the field of molecular biology.",
isbn="978-3-319-78680-3"
}

@article{kralj2018hinmine,
  title={HINMINE: heterogeneous information network mining with information retrieval heuristics},
  author={Kralj, Jan and Robnik-{\v{S}}ikonja, Marko and Lavra{\v{c}}, Nada},
  journal={Journal of Intelligent Information Systems},
  volume={50},
  number={1},
  pages={29--61},
  year={2018},
  publisher={Springer}
}

```
