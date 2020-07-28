## a simple visualization module useful for ad-hoc tasks

from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names, colors_default
from py3plex.core import multinet


def visualize_network(input_file, input_type, directed, visualization_type):
    multilayer_network = multinet.multi_layer_network().load_network(
        input_file, directed=directed, input_type=input_type)
    multilayer_network.basic_stats()  ## check core imports
    multilayer_network.visualize_network(
        style=visualization_type)  ## visualize
    plt.show()


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--network_file", default="")
    parser.add_argument("--network_type", default="")
    parser.add_argument("--directed", default="")
    parser.add_argument("--visualization_type", default="")
    args = parser.parse_args()
    visualize_network(args.network_file, args.network_type, args.directed,
                      args.visualization_type)
