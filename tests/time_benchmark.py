#from pymnet import *
from py3plex.visualization.multilayer import draw, draw_multiedges, draw_multilayer_default, models
from py3plex.visualization.colors import colors_default
from py3plex.core import multinet
import time
import matplotlib.pyplot as plt


def py3plex_visualization(network):

    start = time.time()
    multilayer_network = multinet.multi_layer_network(
        verbose=False).load_network(network,
                                    directed=False,
                                    input_type="multiedge_tuple_list")
    network_labels, graphs, multilinks = multilayer_network.get_layers(
    )  # get layers for visualization

    draw_multilayer_default(graphs,
                            display=False,
                            background_shape="circle",
                            labels=network_labels,
                            layout_algorithm="force",
                            verbose=False)

    enum = 1
    color_mappings = {idx: col for idx, col in enumerate(colors_default)}
    for edge_type, edges in multilinks.items():
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.2,
                        linepoints="-.",
                        linecolor="black",
                        curve_height=5,
                        linmod="upper",
                        linewidth=0.4)
        enum += 1

    end = time.time()
    plt.show()
    plt.clf()
    return (end - start)


def pymnet_visualization(network):
    start = time.time()
    draw(network)
    plt.show()
    end = time.time()
    plt.clf()
    return (end - start)


if __name__ == "__main__":

    import numpy as np
    import itertools
    import pandas as pd

    number_of_nodes = np.arange(5, 200, 15).tolist()
    number_of_edges = reversed([x + 1 for x in list(range(8))])
    probabilities = np.arange(0.05, 0.5, 0.02).tolist()

    merged = [number_of_nodes, number_of_edges, probabilities]
    combinations = list(itertools.product(*merged))

    datapoints = []

    for combination in combinations:
        N, L, p = combination
        print("Evaluating {} {} {} setting.".format(N, L, p))
        net = models.er_multilayer(N, L, p)
        try:
            t_pp = py3plex_visualization(net.edges)
            t_pmn = 0
#            t_pmn = pymnet_visualization(net)

        except Exception as err:
            print(err)

        datapoint = {"N": N, "E": L, "p": p, "Py3plex": t_pp, "Pymnet": t_pmn}
        datapoints.append(datapoint)

    result_frame = pd.DataFrame(datapoints)
    result_frame.to_csv("example_benchmark2.csv")
