# reading different inputs
import matplotlib.image as mgimg
from py3plex.core import random_generators
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from py3plex.visualization.colors import colors_default
from py3plex.visualization.multilayer import draw_multiedges, draw_multilayer_default, hairball_plot
from py3plex.core import multinet
import logging
logger = logging.getLogger()
logger.level = logging.DEBUG


def test_imports():
    logging.info("Import tests")
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/epigenetics.gpickle",
        directed=True,
        input_type="gpickle_biomine")

    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/ecommerce_0.gml", directed=True, input_type="gml")

    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/ions.mat", directed=False, input_type="sparse")

    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/test.edgelist", directed=False, input_type="edgelist")

    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/multiedgelist.txt",
        directed=False,
        input_type="multiedgelist")

    # multilayer_network = multinet.multi_layer_network().load_network("datasets/erdos_detangler.json",directed=False, input_type="detangler_json") ## TOD
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/edgeList.txt", directed=False, input_type="multiedgelist")

    # save the network as a gpickle object
    multilayer_network.save_network(
        output_file="datasets/stored_network.gpickle", output_type="gpickle")


def test_basic_visualizatio1():
    logging.info("Import viz test 1")
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/edgeList.txt", directed=False, input_type="multiedgelist")
    multilayer_network.basic_stats()
    multilayer_network.visualize_network()


def test_basic_visualizatio2():
    logging.info("Import viz test 2")
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/multiL.txt", directed=True, input_type="multiedgelist")
    multilayer_network.basic_stats()
    multilayer_network.visualize_network(style="diagonal")


def test_basic_visualizatio3():
    logging.info("Import viz test 3")
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/multinet_k100.txt",
        directed=True,
        input_type="multiedgelist")
    multilayer_network.basic_stats()
    multilayer_network.visualize_network()


def test_basic_visualizati4():
    # multilayer -----------------------------------
    logging.info("Import viz test 4")
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/epigenetics.gpickle",
        directed=True,
        input_type="gpickle_biomine")
    multilayer_network.basic_stats()  # check core imports
    # multilayer_network.visualize_network() ## visualize
    #

    # You can also access individual graphical elements separately!

    network_labels, graphs, multilinks = multilayer_network.get_layers(
    )  # get layers for visualizat# ion
    draw_multilayer_default(graphs,
                            display=False,
                            background_shape="circle",
                            labels=network_labels)

    enum = 1
    color_mappings = {idx: col for idx, col in enumerate(colors_default)}
    for edge_type, edges in multilinks.items():

        #    network_list,multi_edge_tuple,input_type="nodes",linepoints="-.",alphachannel=0.3,linecolor="black",curve_height=1,style="curve2_bezier",linewidth=1,invert=False,linmod="both",resolution=0.1
        logging.info(edge_type)
        if edge_type == "refers_to":
            draw_multiedges(graphs,
                            edges,
                            alphachannel=0.05,
                            linepoints="--",
                            linecolor="lightblue",
                            curve_height=5,
                            linmod="upper",
                            linewidth=0.4)
        elif edge_type == "refers_to":
            draw_multiedges(graphs,
                            edges,
                            alphachannel=0.2,
                            linepoints=":",
                            linecolor="green",
                            curve_height=5,
                            linmod="upper",
                            linewidth=0.3)
        elif edge_type == "belongs_to":
            draw_multiedges(graphs,
                            edges,
                            alphachannel=0.2,
                            linepoints=":",
                            linecolor="red",
                            curve_height=5,
                            linmod="upper",
                            linewidth=0.4)
        elif edge_type == "codes_for":
            draw_multiedges(graphs,
                            edges,
                            alphachannel=0.2,
                            linepoints=":",
                            linecolor="orange",
                            curve_height=5,
                            linmod="upper",
                            linewidth=0.4)
        else:
            draw_multiedges(graphs,
                            edges,
                            alphachannel=0.2,
                            linepoints="-.",
                            linecolor="black",
                            curve_height=5,
                            linmod="both",
                            linewidth=0.4)
        enum += 1

    plt.clf()

    # monotone coloring
    draw_multilayer_default(graphs,
                            display=False,
                            background_shape="rectangle",
                            labels=network_labels,
                            networks_color="black",
                            rectanglex=2,
                            rectangley=2,
                            background_color="default")

    enum = 1
    for edge_type, edges in multilinks.items():
        draw_multiedges(graphs,
                        edges,
                        alphachannel=0.2,
                        linepoints="--",
                        linecolor="black",
                        curve_height=2,
                        linmod="upper",
                        linewidth=0.4)
        enum += 1


def test_basic_visualizatio5():
    logging.info("Import viz test 6")
    # basic string layout ----------------------------------
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/epigenetics.gpickle",
        directed=False,
        label_delimiter="---",
        input_type="gpickle_biomine")
    network_colors, graph = multilayer_network.get_layers(style="hairball")
    hairball_plot(graph,
                  network_colors,
                  legend=True,
                  layout_parameters={"iterations": 30})


def test_basic_visualizatio6():
    logging.info("Import viz test 7")
    # string layout for larger network -----------------------------------
    multilayer_network = multinet.multi_layer_network().load_network(
        "datasets/soc-Epinions1.edgelist",
        label_delimiter="---",
        input_type="edgelist",
        directed=True)
    hairball_plot(multilayer_network.core_network,
                  layout_parameters={"iterations": 30})


def test_basic_animation():
    logging.info("Import viz test 8")
    fig = plt.figure()
    folder_tmp_files = "datasets/animation"

    def animate(mnod):
        lx = np.random.randint(2, 10, 1)[0]
        ER_multilayer = random_generators.random_multilayer_ER(mnod,
                                                               lx,
                                                               0.005,
                                                               directed=False)
        fx = ER_multilayer.visualize_network(show=False)
        plt.savefig("{}{}.png".format(folder_tmp_files, mnod))

    imrange = [100, 150, 200]
    for j in imrange:
        animate(j)
    myimages = []
    for p in imrange:
        img = mgimg.imread("{}{}.png".format(folder_tmp_files, p))
        imgplot = plt.imshow(img)
        myimages.append([imgplot])
    my_anim = animation.ArtistAnimation(fig, myimages, interval=10)
