## converters
import networkx as nx
from collections import defaultdict
from ..visualization.layout_algorithms import *


def prepare_for_visualization(multinet,
                              compute_layouts="force",
                              layout_parameters=None,
                              verbose=True,
                              multiplex=False):
    """ 
    This functions takes a multilayer object and returns individual layers, their names, as well as multilayer edges spanning over multiple layers.

    Args:
        param1 (obj): multilayer object
        param2 (str): Layout algorithm
        param3 (dict): Optional layout parameters

    Returns:
        tuple: (names,networks,multiedges)

    """

    layers = defaultdict(list)
    for node in multinet.nodes(data=True):
        try:
            layers[node[0][1]].append(node[0])
        except Exception as err:
            print(err, "sth")

    networks = {
        layer_name: multinet.subgraph(v)
        for layer_name, v in layers.items()
    }

    if multiplex:
        if compute_layouts == "force":
            tmp_pos = compute_force_directed_layout(multinet,
                                                    layout_parameters,
                                                    verbose=verbose)

        if compute_layouts == "force_nx":
            tmp_pos = compute_force_directed_layout(multinet,
                                                    layout_parameters,
                                                    verbose=verbose,
                                                    forceImport=False)

        elif compute_layouts == "random":
            tmp_pos = compute_random_layout(multinet)

        elif compute_layouts == "custom_coordinates":
            tmp_pos = layout_parameters['pos']

        for node in multinet.nodes(data=True):
            coordinates = tmp_pos[node[0]]
            if np.abs(coordinates[0]) > 1 or np.abs(coordinates[1]) > 1:
                coordinates = np.random.rand(2)
            node[1]['pos'] = coordinates

    else:
        for layer, network in networks.items():

            if compute_layouts == "force":
                tmp_pos = compute_force_directed_layout(network,
                                                        layout_parameters,
                                                        verbose=verbose)

            elif compute_layouts == "random":
                tmp_pos = compute_random_layout(network)

            elif compute_layouts == "custom_coordinates":
                tmp_pos = layout_parameters['pos']

            else:
                break

            keys = []
            value_pairs = []
            for k, v in tmp_pos.items():
                value_pairs.append(v)
                keys.append(k)

            coordinate_matrix = np.matrix(value_pairs)
            norm_x = (coordinate_matrix[:, 0] - np.min(
                coordinate_matrix[:, 0])) / (np.max(coordinate_matrix[:, 0]) -
                                             np.min(coordinate_matrix[:, 0]))

            norm_y = (coordinate_matrix[:, 1] - np.min(
                coordinate_matrix[:, 1])) / (np.max(coordinate_matrix[:, 1]) -
                                             np.min(coordinate_matrix[:, 1]))

            coordinate_matrix[:, 0] = norm_x
            coordinate_matrix[:, 1] = norm_y

            tmp_pos = {}
            for enx, j in enumerate(keys):
                tmp_pos[j] = np.asarray(coordinate_matrix[enx])[0]

            for node in network.nodes(data=True):
                coordinates = tmp_pos[node[0]]
                if network.degree(node[0]) == 0:
                    coordinates = np.array(coordinates) / 2
                elif network.degree(node[0]) == 1:
                    coordinates = np.array(coordinates) / 2
                if np.abs(coordinates[0]) > 1 or np.abs(coordinates[1]) > 1:
                    coordinates = np.random.rand(
                        1) * coordinates / np.linalg.norm(coordinates)

                node[1]['pos'] = coordinates

    if verbose:
        print("Finished with layout..")
    inverse_mapping = {}
    layouts = []

    ## construct the inverse mapping
    for k, v in layers.items():
        for x in v:
            inverse_mapping[x] = k

    multiedges = defaultdict(list)
    for edge in multinet.edges(data=True):
        try:
            if edge[0][1] != edge[1][1]:
                multiedges[edge[2]['type']].append(edge)
        except Exception as err:
            multiedges['default_inter'].append(edge)
            print(err, "test")

    names, networks = zip(*networks.items())
    return (names, networks, multiedges)


def prepare_for_visualization_hairball(multinet, compute_layouts=False):
    """ 
    Compute layout for a hairball visualization

    Args:
        param1 (obj): multilayer object

    Returns:
        tuple: (names, prepared network)

    """

    layers = defaultdict(list)
    for node in multinet.nodes(data=True):
        try:
            layers[node[0][1]].append(node[0])

        except:
            layers[1].append(node)

    inverse_mapping = {}
    enumerated_layers = {
        name: ind
        for ind, name in enumerate(set(list(layers.keys())))
    }
    for k, v in layers.items():
        for x in v:
            inverse_mapping[x] = enumerated_layers[k]
    ordered_names = [inverse_mapping[x] for x in multinet.nodes()]
    node_types = [x[1] for x in multinet.nodes()]
    return (ordered_names, multinet)


def prepare_for_parsing(multinet):
    """ 
    Compute layout for a hairball visualization

    Args:
        param1 (obj): multilayer object

    Returns:
        tuple: (names, prepared network)

    """

    layers = defaultdict(list)
    for node in multinet.nodes(data=True):
        try:
            layers[node[0][1]].append(node[0])
        except Exception as err:
            print(err, "sth")

    networks = {
        layer_name: multinet.subgraph(v)
        for layer_name, v in layers.items()
    }

    inverse_mapping = {}
    layouts = []

    ## construct the inverse mapping
    for k, v in layers.items():
        for x in v:
            inverse_mapping[x] = k

    multiedges = defaultdict(list)
    for edge in multinet.edges(data=True):
        try:
            if edge[0][1] != edge[1][1]:
                multiedges[edge[2]['type']].append(edge)
        except Exception as err:
            multiedges['default_inter'].append(edge)
            print(err, "test")

    names, networks = zip(*networks.items())
    return (names, networks, multiedges)
