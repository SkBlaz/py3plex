## set of parsers used in Py3plex.

import networkx as nx
import json
import itertools
import glob
import operator
import numpy as np
import scipy.io
from collections import defaultdict, Counter
import pandas as pd
import gzip
from .supporting import *


def parse_gml(file_name, directed):
    """ 
    parse a gml network

    Args:
        param1 (obj): file name
        param2 (obj): directed?

    Returns:
    (multigraph, possible labels)

    """

    H = nx.read_gml(file_name)

    if directed:
        A = nx.MultiDiGraph()
    else:
        A = nx.MultiGraph()

    node_type_map = {}
    ## initial type maps
    for node in H.nodes(data=True):
        node_type_map[node[0]] = node[1]

        ## read into structure
    for edge in H.edges(data=True):
        node_first = (edge[0], node_type_map[edge[0]]['type'])
        node_second = (edge[1], node_type_map[edge[1]]['type'])
        edge_props = edge[2]

        A.add_node(node_first, **node_type_map[edge[0]])
        A.add_node(node_second, **node_type_map[edge[1]])
        A.add_edge(node_first, node_second, **edge_props)

    ## add labels
    return (A, None)


def parse_nx(nx_object, directed):
    """
    Core parser for networkx objects
    :input:  a networkx graph
    """

    return (nx_object, None)


def parse_matrix(file_name, directed):
    """
    Parser for matrices
    :input: a SciPy sparse matrix
    """

    mat = scipy.io.loadmat(file_name)
    return (mat['network'], mat['group'])


def parse_gpickle(file_name, directed=False, layer_separator=None):
    """
    A parser for generic Gpickle as stored by Py3plex.    
    :input: gpickle object
    """

    print("Parsing gpickle..")
    if directed:
        A = nx.MultiDiGraph()
    else:
        A = nx.MultiGraph()

    G = nx.read_gpickle(file_name)

    if layer_separator is not None:
        for edge in G.edges():
            e1, e2 = edge
            try:
                layer1, n1 = e1.split(layer_separator)
                layer2, n2 = e2.split(layer_separator)
                A.add_edge((n1, layer1), (n2, layer2))
            except:
                pass
    else:
        A = G

    todrop = []
    for node in A.nodes(data=True):
        if "labels" in node[1]:
            if node[1]['labels'] == "":
                todrop.append(node[0])
    A.remove_nodes_from(todrop)
    return (A, None)


def parse_gpickle_biomine(file_name, directed):
    """
    Gpickle parser for biomine graphs
    :input: Gpickle containing BioMine data
    """

    ## convert the biomine
    input_graph = nx.read_gpickle(file_name)

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    for edge in input_graph.edges(data=True):

        l1, n1 = edge[0].split("_")[:2]
        l2, n2 = edge[1].split("_")[:2]
        G.add_edge((n1, l1), (n2, l2), type=edge[2]['key'])

    return (G, None)


def parse_detangler_json(file_path):
    """
    Parser for generic Detangler files
    :input: Detangler JSON
    """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    with open(file_path) as f:
        graph = json.load(f)

    id2n = {}
    for n in graph[u'nodes']:
        id2n[n[u'id']] = n
        layers = n[u'descriptors'].split(';')
        node = n[u'label']
        for l in layers:
            node_dict = {'source': node, 'type': l}
            G.add_node((node, l))
        for c in itertools.combinations(layers, 2):
            G.add_edge((node, c[0]), (node, c[1]))

    for e in graph[u'links']:
        s = id2n[e[u'source']][u'label']
        t = id2n[e[u'target']][u'label']
        layers = e[u'descriptors'].split(';')
        for l in layers:
            G.add_edge((s, l), (t, l))

    return (G, None)


def parse_multi_edgelist(input_name, directed):
    """
    A generic multiedgelist parser
    n l n l w
    :input: a text file containing multiedges
    """

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    with open(input_name) as IN:
        for line in IN:
            parts = line.strip().split()

            if len(parts) == 5:
                node_first, layer_first, node_second, layer_second, weight = parts

            else:
                node_first, layer_first, node_second, layer_second = parts
                weight = 1

            if layer_first == layer_second and node_first == node_second:

                # first case
                G.add_node((node_first, layer_first), type=layer_first)
                G.add_edge((node_first, layer_first),
                           (node_first, layer_first),
                           weight=weight)
            elif layer_first == layer_second and node_first != node_second:

                # second case
                G.add_node((node_first, layer_first), type=layer_first)
                G.add_node((node_second, layer_second), type=layer_first)
                G.add_edge((node_first, layer_first),
                           (node_second, layer_second),
                           weight=weight)
            else:
                #default case
                G.add_node((node_first, layer_first), type=layer_first)
                G.add_node((node_second, layer_second), type=layer_second)
                G.add_edge((node_first, layer_first),
                           (node_second, layer_second),
                           weight=weight)

    return (G, None)


def parse_simple_edgelist(input_name, directed):
    """
    Simple edgelist n n w
    :input: a text file
    """

    if directed:
        G = nx.DiGraph()

    else:
        G = nx.Graph()

    if ".gz" in input_name:
        handle = gzip.open(input_name, 'rt')

    else:
        handle = open(input_name)

    with handle as IN:
        for line in IN:
            if line.split()[0] != "#":
                parts = line.strip().split()
                if len(parts) == 3:
                    node_first, node_second, weight = parts
                elif len(parts) == 2:
                    node_first, node_second = parts
                    weight = 1
                else:
                    continue

                node_first = (node_first, "null")
                node_second = (node_second, "null")

                G.add_node(node_first, type="null")
                G.add_node(node_second, type="null")

                G.add_edge(node_first, node_second, weight=weight)

    return (G, None)


def parse_edgelist_multi_types(input_name, directed):
    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()

    with open(input_name) as IN:
        for line in IN:
            if line.split()[0] != "#":
                parts = line.strip().split()
                if len(parts) > 2:
                    node_first, node_second, weight = parts
                    edge_type = parts[3]
                else:
                    node_first, node_second = parts
                    weight = 1
                    edge_type = None

                G.add_node((node_first, "null"), type="null")
                G.add_node((node_second, "null"), type="null")
                G.add_edge(node_first,
                           node_second,
                           weight=weight,
                           type=edge_type)
    return (G, None)


def parse_spin_edgelist(input_name, directed):

    G = nx.Graph()
    with open(input_name) as IN:
        for line in IN:

            parts = line.strip().split()
            node_first = parts[0]
            node_second = parts[1]
            tag = parts[2]
            if len(parts) >= 4:
                weight = parts[3]
            else:
                weight = 1

            G.add_node(node_first)
            G.add_node(node_second)
            G.add_edge(node_first, node_second, weight=weight, type=tag)

    return (G, None)


def parse_embedding(input_name):
    """
    Loader for generic embedding as outputed by GenSim
    """

    meta = None
    embedding_matrix = []
    embedding_indices = []
    with open(input_name) as IN:
        for line in IN:
            line = line.strip().split()
            if len(line) == 2:
                meta = line
            else:
                embedding_matrix.append(line[1:])
                embedding_indices.append(line[0])
    embedding_matrix = np.matrix(embedding_matrix)
    embedding_indices = np.array(embedding_indices)
    return (embedding_matrix, embedding_indices)


def parse_multiedge_tuple_list(network, directed):
    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()
    for _edgetuple in network:
        #        ((str(node_first_names[enx]),str(layer_names[enx])),(str(node_second_names[enx]),str(layer_names[enx])))

        node_first, node_second, layer_first, layer_second, weight = _edgetuple

        G.add_node((node_first, layer_first))
        G.add_node((node_second, layer_second))
        G.add_edge((node_first, layer_first), (node_second, layer_second),
                   weight=weight)

        #G.add_node(node_first,type=layer_first)
        #G.add_node(node_second,type=layer_second)
        #G.add_edge(node_first,node_second,weight=weight)

    return (G, None)
    pass


def parse_multiplex_edges(input_name, directed):

    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()

    unique_layers = set()
    with open(input_name) as ef:
        for line in ef:
            parts = line.strip().split(" ")
            node_first = str(parts[1])
            node_second = str(parts[2])
            layer = parts[0]
            if len(parts) > 2:
                weight = parts[3]
            else:
                weight = 1
            G.add_node((node_first, str(layer)))
            G.add_node((node_second, str(layer)))
            unique_layers.add(str(layer[0]))
            G.add_edge((node_first, str(layer)), (node_second, str(layer)),
                       weight=float(weight),
                       type="default")

    return (G, None)


def parse_multiplex_folder(input_folder, directed):

    # 16 17 1377438155 RT -> activity n1 n2 time label
    # 1 RT -> layer name
    # 1 61450 1252 1 -> layer n1 n2 w
    # 9 9 node id, lab

    names = glob.glob(input_folder + "/*")
    edges_file = [x for x in names if ".edges" in x]
    activity_file = [x for x in names if "activity.txt" in x]
    time_series_tuples = None
    layer_file = [x for x in names if "layers.txt" in x]
    layer_dict = {}
    for lx in layer_file:
        with open(lx) as lf:
            for line in lf:
                lid, lname = line.strip().split(" ")
                layer_dict[lname] = lid

    if len(activity_file) >= 1:
        time_series_tuples = list()  #defaultdict(list)
        for ac in activity_file:
            with open(ac) as acf:
                for line in acf:
                    n1, n2, timestamp, layer_name = line.strip().split(" ")
                    time_series_tuples.append({
                        "node_first": 1,
                        "node_second": n2,
                        "layer": layer_dict[layer_name],
                        "timestamp": timestamp
                    })

    time_series_tuples = pd.DataFrame()
    time_series_tuples = time_series_tuples.append(time_series_tuples,
                                                   ignore_index=True)

    #    nodes_file = [x for x in names if "nodes.txt" in x]

    if directed:
        G = nx.MultiDiGraph()

    else:
        G = nx.MultiGraph()

    for edgefile in edges_file:
        with open(edgefile) as ef:
            for line in ef:
                parts = line.strip().split(" ")
                node_first = parts[1]
                node_second = parts[2]
                layer = parts[0]
                weight = parts[3]
                G.add_node((node_first, str(layer)))
                G.add_node((node_second, str(layer)))
                G.add_edge((node_first, str(layer)), (node_second, str(layer)),
                           key="default",
                           weight=weight,
                           type="default")

    return (G, None, time_series_tuples)


## main parser method
def parse_network(input_name,
                  f_type="gml",
                  directed=False,
                  label_delimiter=None,
                  network_type="multilayer"):
    '''
    A wrapper method for available parsers!
    '''

    time_series = None
    if f_type == "gml":
        parsed_network, labels = parse_gml(input_name, directed)

    elif f_type == "nx":
        parsed_network, labels = parse_nx(input_name, directed)

    elif f_type == "multiplex_folder":
        parsed_network, labels, time_series = parse_multiplex_folder(
            input_name, directed)

    elif f_type == "sparse":
        parsed_network, labels = parse_matrix(input_name, directed)

    elif f_type == "gpickle_biomine":
        parsed_network, labels = parse_gpickle_biomine(input_name, directed)

    elif f_type == "gpickle":
        parsed_network, labels = parse_gpickle(input_name, directed)

    elif f_type == "multiedgelist":
        parsed_network, labels = parse_multi_edgelist(input_name, directed)

    elif f_type == "detangler_json":
        parsed_network, labels = parse_detangler_json(input_name, directed)

    elif f_type == "edgelist":
        parsed_network, labels = parse_simple_edgelist(input_name, directed)

    elif f_type == "edgelist_spin":
        parsed_network, labels = parse_spin_edgelist(input_name, directed)

    elif f_type == "edgelist_with_edge_types":
        parsed_network, labels = parse_edgelist_multi_types(
            input_name, directed)

    elif f_type == "multiedge_tuple_list":
        parsed_network, labels = parse_multiedge_tuple_list(
            input_name, directed)

    elif f_type == "multiplex_edges":
        parsed_network, labels = parse_multiplex_edges(input_name, directed)

    if network_type == "multilayer":
        return (parsed_network, labels, time_series)

    elif network_type == "multiplex":
        multiplex_graph = add_mpx_edges(parsed_network)
        return (multiplex_graph, labels, time_series)

    else:
        raise Exception("Please, specify heterogeneous network type.")


def load_edge_activity_raw(activity_file, layer_mappings):
    '''
    Basic parser for loading generic activity files. Here, temporal edges are given as tuples -> this can be easily transformed for example into a pandas dataframe!
    '''

    time_series_tuples = []
    outframe = pd.DataFrame()
    with open(activity_file, "r+") as acf:
        for line in acf:
            n1, n2, timestamp, layer_name = line.strip().split(" ")

            time_series_tuples.append({
                "node_first": n1,
                "node_second": n2,
                "layer_name": layer_mappings[layer_name],
                "timestamp": timestamp
            })
    outframe = outframe.append(time_series_tuples, ignore_index=True)
    return outframe


def load_edge_activity_file(fname, layer_mapping=None):

    # Example edge looks like this: 11 11 1375695069 RE

    if layer_mapping is not None:
        lmap = {}
        with open(layer_mapping) as lm:
            for line in lm:
                code, name = line.strip().split()
                lmap[name] = code

    outframe = pd.DataFrame()
    data = []
    with open(fname) as fn:
        for line in fn:
            node1, node2, timestamp, layer = line.strip().split()
            if layer_mapping is not None:
                layer = lmap[layer]
            data.append({
                "node_first": node1,
                "node_second": node2,
                "layer": layer,
                "timestamp": timestamp
            })
    outframe = outframe.from_dict(data)
    return outframe


def load_temporal_edge_information(input_network,
                                   input_type,
                                   layer_mapping=None):

    if input_type == "edge_activity":
        return load_edge_activity_file(input_network,
                                       layer_mapping=layer_mapping)
    else:
        return None


def save_gpickle(input_network, output_file):
    nx.write_gpickle(input_network, output_file)


def save_multiedgelist(input_network,
                       output_file,
                       attributes=False,
                       encode_with_ints=False):
    """
    Save multiedgelist -- as n1, l1, n2, l2, w
    """

    if encode_with_ints:

        unique_nodes = {n[0] for n in input_network.nodes()}
        unique_node_types = {n[1] for n in input_network.nodes()}
        node_encodings = {
            real: str(enc)
            for enc, real in enumerate(unique_nodes)
        }
        type_encodings = {
            real: str(enc)
            for enc, real in enumerate(unique_node_types)
        }
        fh = open(output_file, "w+")

        for edge in input_network.edges(data=True):
            n1, l1 = edge[0]
            n2, l2 = edge[1]
            fh.write("\t".join([
                node_encodings[n1], type_encodings[l1], node_encodings[n2],
                type_encodings[l2]
            ]) + "\n")
        fh.close()

        return (node_encodings, type_encodings)

    else:
        fh = open(output_file, "w+")
        for edge in input_network.edges(data=True):
            n1, l1 = edge[0]
            n2, l2 = edge[1]
            fh.write("\t".join([n1, l1, n2, l2]) + "\n")
        fh.close()


def save_edgelist(input_network, output_file, attributes=False):
    fh = open(output_file, 'wb')
    input_network = nx.convert_node_labels_to_integers(input_network,
                                                       first_label=0,
                                                       ordering='default',
                                                       label_attribute=None)
    if attributes:
        pass
    else:
        nx.write_edgelist(input_network, fh, data=False)
    print("Finished writing the network..")


if __name__ == "__main__":
    print("Testing parser")
    #    print (nx.info(parse_gml("../../datasets/imdb_gml.gml",f_type="gml",directed=False)))
    #    print (nx.info(parse_network("../../datasets/epigenetics.gpickle",f_type="gpickle_biomine",directed=False)))
    #print (nx.info(parse_network("../../datasets/multiedgelist.txt",f_type="multiedgelist",directed=False)))

    parse_embedding("../../datasets/karate.emb")
