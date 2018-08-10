## set of supporting methods for parsers and converters

from collections import defaultdict
import networkx as nx
import itertools
import multiprocessing as mp
import tqdm

def split_to_layers(input_network):

    layer_info = defaultdict(list)
    subgraph_dictionary = {}
    
    for node in input_network.nodes(data=True):
        try:
            layer_info[node[0][1]].append(node[0])
        except Exception as err:
            layer_info[node[1]['type']].append(node[0])
    
    for layer,nodes in layer_info.items():
        subnetwork = input_network.subgraph(nodes)
        subgraph_dictionary[layer] = subnetwork #nx.relabel_nodes(subnetwork,mapping)
    del layer_info
    
    return subgraph_dictionary


# def add_mx_edges(node):
#    layer_appearances = []
#    for layer,net in _layerwise_nodes.items():
#        layer_nodes = set([n.split(_layer_node_code)[1] for n in net.nodes()])
#        if node in layer_nodes:
#            layer_appearances.append(layer)
#    layer_appearances = set(layer_appearances)
#    if len(layer_appearances) > 1:
#        for comb in itertools.combinations(layer_appearances, 2):
#            _tmp_net.add_edge(comb[0]+_layer_node_code+node,comb[1]+_layer_node_code+node,type="mpx")


# def add_mpx_edges_parallel(input_network,layer_node_code):


# #    Ref: E. Omodei, M. De Domenico, A. Arenas. - Characterizing interactions in online social networks during exceptional events.. Front. Phys. 3, 59 (2015)
    
#     ## split network by layers
#     global _layerwise_nodes
#     global _layer_node_code
#     global _tmp_net

#     _tmp_net = input_network
#     del input_network
#     _layer_node_code = layer_node_code    
#     _layerwise_nodes = split_to_layers(_tmp_net,layer_node_code)
#     unique_nodes = [n.split(layer_node_code)[1] for n in _tmp_net.nodes()]
#     pool = mp.Pool(processes=3)
#     with mp.Pool(processes=mp.num_cpu()) as pool:
#         for _ in tqdm.tqdm(pool.imap_unordered(add_mx_edges,unique_nodes), total=len(unique_nodes)):
#             pass

#     return _tmp_net


def add_mpx_edges(input_network):
    
    _layerwise_nodes = split_to_layers(input_network)
    
    min_node_layer = {}
    for layer,network in _layerwise_nodes.items():
        min_node_layer[layer] = set([n[0][1] for n in network.nodes(data=True)])
    
    for pair in itertools.combinations(list(min_node_layer.keys()),2):
        layer_first = pair[0]
        layer_second = pair[1]
        pair_intersection = set.intersection(min_node_layer[layer_first],min_node_layer[layer_second])
        for node in pair_intersection:
            input_network.add_edge((node,layer_first),(node,layer_second),key="mpx",type="multiplex")

    return input_network
        

def parse_gaf_to_uniprot_GO(gaf_mappings,filter_terms=None):
    uniGO = defaultdict(list)    
    with open(gaf_mappings) as im:
        for line in im:
            parts = line.split("\t")
            try:
                if "GO:" in parts[4]:
                    uniGO[parts[1]].append(parts[4]) ## GO and ref both added
                if "GO:" in parts[3]:
                    uniGO[parts[1]].append(parts[3])
            except:
                pass

    all_terms = list(itertools.chain(*uniGO.values()))
    if filter_terms is not None:
        sorted_d = sorted(Counter(all_terms).items(), key=operator.itemgetter(1),reverse=True)
        top_100 = [x[0] for x in sorted_d[0:filter_terms]]
        new_map = defaultdict(list)
        for k,v in uniGO.items():
            v = [x for x in v if x in top_100]
            new_map[k] = v        
        return new_map
    
    else:
        return uniGO
