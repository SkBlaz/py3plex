# set of supporting methods for parsers and converters

from collections import defaultdict
import itertools


def split_to_layers(input_network):

    layer_info = defaultdict(list)
    subgraph_dictionary = {}

    for node in input_network.nodes(data=True):
        try:
            layer_info[node[0][1]].append(node[0])
        except Exception:
            layer_info[node[1]['type']].append(node[0])

    for layer, nodes in layer_info.items():
        subnetwork = input_network.subgraph(nodes)
        subgraph_dictionary[
            layer] = subnetwork  # nx.relabel_nodes(subnetwork,mapping)
    del layer_info

    return subgraph_dictionary


def add_mpx_edges(input_network):

    _layerwise_nodes = split_to_layers(input_network)

    min_node_layer = {}
    for layer, network in _layerwise_nodes.items():
        min_node_layer[layer] = set(
            [n[0][0] for n in network.nodes(data=True)])

    for pair in itertools.combinations(list(min_node_layer.keys()), 2):
        layer_first = pair[0]
        layer_second = pair[1]
        pair_intersection = set.intersection(min_node_layer[layer_first],
                                             min_node_layer[layer_second])

        for node in pair_intersection:
            n1 = (node, layer_first)
            n2 = (node, layer_second)
            input_network.add_edge(n1, n2, key="mpx", type="mpx")

    return input_network


def parse_gaf_to_uniprot_GO(gaf_mappings, filter_terms=None):
    uniGO = defaultdict(list)
    with open(gaf_mappings) as im:
        for line in im:
            parts = line.split("\t")
            try:
                if "GO:" in parts[4]:
                    uniGO[parts[1]].append(parts[4])  # GO and ref both added
                if "GO:" in parts[3]:
                    uniGO[parts[1]].append(parts[3])
            except:
                pass

    all_terms = list(itertools.chain(*uniGO.values()))
    if filter_terms is not None:
        sorted_d = sorted(Counter(all_terms).items(),
                          key=operator.itemgetter(1),
                          reverse=True)
        top_100 = [x[0] for x in sorted_d[0:filter_terms]]
        new_map = defaultdict(list)
        for k, v in uniGO.items():
            v = [x for x in v if x in top_100]
            new_map[k] = v
        return new_map

    else:
        return uniGO
