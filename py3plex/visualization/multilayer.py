# This is the multiplex layer constructor class

# draw multi layered network, takes .nx object list as input

# imports first

import numpy as np
import networkx as nx
try:
    from matplotlib.patches import Rectangle
    from matplotlib.patches import Circle
except:
    pass

import random

import matplotlib.pyplot as plt

from . import colors  # those are color ranges
from . import bezier  # those are bezier curves
from . import polyfit
from .layout_algorithms import compute_force_directed_layout, compute_random_layout
from . import drawing_machinery

main_figure = plt.figure()
shape_subplot = main_figure.add_subplot(111)

try:
    import plotly.graph_objects as go
    plotly_import = True
except:
    plotly_import = False


def draw_multilayer_default(network_list,
                            display=True,
                            node_size=10,
                            alphalevel=0.13,
                            rectanglex=1,
                            rectangley=1,
                            background_shape="circle",
                            background_color="rainbow",
                            networks_color="rainbow",
                            labels=False,
                            arrowsize=0.5,
                            label_position=1,
                            verbose=False,
                            remove_isolated_nodes=False,
                            axis=None,
                            edge_size=1,
                            node_labels=False,
                            node_font_size=5,
                            scale_by_size=False):
    """Core multilayer drawing method

    Args:
    network_list (list): a list of networks
    display (bool): Whether to display or not (directly)
    node_size (int): size of the nodes
    alphalevel (float): transparency level
    rectanglex (float): size of rectangles (background) (horizontal part)
    rectangley (float): size of vertical parts of rectangles
    background_shape (string): Background shape, either circle or rectangle
    background_color (string): Background color
    networks_color (string): Color of individual networks
    labels (bool): Display labels?
    arrowsize (float): Sizes of individual arrows
    label_position (int): position of labels  (diagonal right)
    verbose (bool): Verbose printout?
    remove_isolated_nodes (bool): Remove isolated nodes?
    axis (bools): axis are displayed
    edge_size (float): Size of edges
    node_labels (bool): Display node labels?
    node_font_size (int): Size of the font
    scale_by_size (bool): Scale nodes according to their degrees?

    Returns:
        None
    """

    if background_color == "default":

        facecolor_list_background = colors.linear_gradient(
            "#4286f4", n=len(network_list))['hex']

    elif background_color == "rainbow":

        facecolor_list_background = colors.colors_default

    elif background_color == None:

        facecolor_list_background = colors.colors_default
        alphalevel = 0

    else:
        pass

    if networks_color == "rainbow":

        facecolor_list = colors.colors_default

    elif networks_color == "black":

        facecolor_list = ["black"] * len(network_list)

    else:
        pass

    start_location_network = 0
    start_location_background = 0
    color = 0
    shadow_size = 0.5
    circle_size = 1.05

    for network in network_list:
        if remove_isolated_nodes:
            isolates = list(nx.isolates(network))
            network = network.copy()
            network.remove_nodes_from(isolates)

        if verbose:
            print(nx.info(network))
        degrees = dict(nx.degree(nx.Graph(network)))
        cntr = 0
        cntr_all = 0
        no_position = []
        all_positions = []
        for node in network.nodes(data=True):
            if 'pos' not in node[1]:
                no_position.append(node[0])
                cntr += 1
            else:
                all_positions.append(node[1]['pos'])
                cntr_all += 1

        if len(no_position) > 0:
            network = network.copy()
            network.remove_nodes_from(no_position)

        positions = nx.get_node_attributes(network, 'pos')
        cntr = 0

        for node, position in positions.items():
            position += start_location_network

        # this is the default delay for matplotlib canvas
        if labels != False:
            try:
                shape_subplot.text(start_location_network + label_position,
                                   start_location_network - label_position,
                                   labels[color])
            except Exception as es:
                print(es)

        if background_shape == "rectangle":
            shape_subplot.add_patch(
                Rectangle(
                    (start_location_background, start_location_background),
                    rectanglex,
                    rectangley,
                    alpha=alphalevel,
                    linestyle="dotted",
                    fill=True,
                    facecolor=facecolor_list_background[color]))

        elif background_shape == "circle":
            shape_subplot.add_patch(
                Circle((start_location_background + shadow_size,
                        start_location_background + shadow_size),
                       circle_size,
                       color=facecolor_list_background[color],
                       alpha=alphalevel))
        else:
            pass

        start_location_network += 1.5
        start_location_background += 1.5
        # if len(network.nodes()) > 10000:
        #     correction=10
        # else:
        #     correction = 1

        if scale_by_size:
            node_sizes = [vx * node_size for vx in degrees.values()]
        else:
            node_sizes = [node_size for vx in degrees.values()]

        if np.sum(node_sizes) == 0:
            node_sizes = [node_size for vx in degrees.values()]


#        node_sizes = [(np.log(v) * node_size)/correction if v > 400 else node_size/correction for v in degrees.values()]

# cntr+=1
# for position in positions:
#     if cntr<15:
#         print(positions[position][0], positions[position][1])

        drawing_machinery.draw(network,
                               positions,
                               node_color=facecolor_list[color],
                               with_labels=node_labels,
                               edge_size=edge_size,
                               node_size=node_sizes,
                               arrowsize=arrowsize,
                               ax=axis,
                               font_size=node_font_size)
        color += 1

    if display == True:
        plt.show()


def draw_multiedges(network_list,
                    multi_edge_tuple,
                    input_type="nodes",
                    linepoints="-.",
                    alphachannel=0.3,
                    linecolor="black",
                    curve_height=1,
                    style="curve2_bezier",
                    linewidth=1,
                    invert=False,
                    linmod="both",
                    resolution=0.001):
    # indices are correct network positions
    if input_type == "nodes":

        network_positions = [
            nx.get_node_attributes(network, 'pos') for network in network_list
        ]

        global_positions = {}
        for position in network_positions:
            for k, v in position.items():
                global_positions[k] = v

        for pair in multi_edge_tuple:
            try:

                coordinates_node_first = global_positions[pair[0]]
                coordinates_node_second = global_positions[pair[1]]

                p1 = [coordinates_node_first[0], coordinates_node_second[0]]
                #[coordinates_node_first[0], coordinates_node_first[1]]
                p2 = [coordinates_node_first[1],
                      coordinates_node_second[1]]  # []

                if style == "line":

                    plt.plot(p1,
                             p2,
                             linestyle=linepoints,
                             lw=1,
                             alpha=alphachannel,
                             color=linecolor)

                elif style == "curve2_bezier":

                    x, y = bezier.draw_bezier(len(network_list),
                                              p1,
                                              p2,
                                              path_height=curve_height,
                                              inversion=invert,
                                              linemode=linmod,
                                              resolution=resolution)

                    plt.plot(x,
                             y,
                             linestyle=linepoints,
                             lw=linewidth,
                             alpha=alphachannel,
                             color=linecolor)

                elif style == "curve3_bezier":

                    x, y = bezier.draw_bezier(len(network_list),
                                              p1,
                                              p2,
                                              mode="cubic",
                                              resolution=resolution)

                elif style == "curve3_fit":

                    x, y = polyfit.draw_order3(len(network_list), p1, p2)

                    plt.plot(x, y)

                elif style == "piramidal":

                    x, y = polyfit.draw_piramidal(len(network_list), p1, p2)
                    plt.plot(x,
                             y,
                             linestyle=linepoints,
                             lw=1,
                             alpha=alphachannel,
                             color=linecolor)

                else:
                    pass

            except Exception as err:
                print(err)


#                print(err,"test")


def generate_random_multiedges(network_list,
                               random_edges,
                               style="line",
                               linepoints="-.",
                               upper_first=2,
                               lower_first=0,
                               lower_second=2,
                               inverse_tag=False,
                               pheight=1):

    main_figure.add_subplot(111)

    # this needs to be in the form of:
    for k in range(random_edges):
        try:
            random_network1 = random.randint(0, upper_first)
            random_network2 = random.randint(lower_second, len(network_list))

            node_first = random.randint(1, 3)
            node_second = random.randint(1, 3)

            positions_first_net = nx.get_node_attributes(
                network_list[random_network1], 'pos')
            positions_second_net = nx.get_node_attributes(
                network_list[random_network2], 'pos')

            p1 = [
                positions_first_net[node_first][0],
                positions_second_net[node_second][0]
            ]
            p2 = [
                positions_first_net[node_first][1],
                positions_second_net[node_second][1]
            ]

            if style == "line":

                plt.plot(p1, p2, 'k-', lw=1, color="black", linestyle="dotted")

            elif style == "curve2_bezier":

                x, y = bezier.draw_bezier(len(network_list),
                                          p1,
                                          p2,
                                          inversion=inverse_tag,
                                          path_height=pheight)
                plt.plot(x, y, linestyle=linepoints, lw=1, alpha=0.3)

            elif style == "curve3_bezier":

                x, y = bezier.draw_bezier(len(network_list),
                                          p1,
                                          p2,
                                          mode="cubic")

            elif style == "curve3_fit":

                x, y = polyfit.draw_order3(len(network_list), p1, p2)

                plt.plot(x, y)

            elif style == "piramidal":

                x, y = polyfit.draw_piramidal(len(network_list), p1, p2)
                plt.plot(x, y, color="black", alpha=0.3, linestyle="-.", lw=1)

            else:
                pass
        except:
            pass


def generate_random_networks(number_of_networks):

    network_list = []
    for j in range(number_of_networks):
        tmp_graph = nx.gnm_random_graph(random.randint(60, 300),
                                        random.randint(5, 300))
        tmp_pos = nx.spring_layout(tmp_graph)
        nx.set_node_attributes(tmp_graph, 'pos', tmp_pos)
        network_list.append(tmp_graph)
    return network_list


def supra_adjacency_matrix_plot(matrix, display=False):
    plt.imshow(matrix, interpolation='nearest', cmap=plt.cm.binary)
    if display:
        plt.show()


def onclick(event):
    print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          ('double' if event.dblclick else 'single', event.button, event.x,
           event.y, event.xdata, event.ydata))


def hairball_plot(
        g,
        color_list=None,
        display=False,
        node_size=1,
        text_color="black",
        node_sizes=None,  # for custom sizes
        layout_parameters=None,
        legend=None,
        scale_by_size=True,
        layout_algorithm="force",
        edge_width=0.01,
        alpha_channel=0.5,
        labels=None,
        draw=True,
        label_font_size=2):
    """A method for drawing force-directed plots
    Args:
    network (networkx): A network to be visualized
    color_list (list): A list of colors for nodes
    node_size (float): Size of nodes
    layout_parameters (dict): A dictionary of label parameters
    legend (bool): Display legend?
    scale_by_size (bool): Rescale nodes?
    layout_algorithm (string): What type of layout algorithm is to be used?
    edge_width (float): Width of edges
    alpha_channel (float): Transparency level.
    labels (bool): Display labels?
    label_font_size (int): Sizes of labels
    Returns:
        None
    """

    print("Beginning parsing..")
    nodes = g.nodes(data=True)
    potlabs = []
    #    fig, ax = plt.subplots()
    for node in nodes:
        try:
            potlabs.append(node[0][1])
        except:
            potlabs.append("unlabeled")

    if color_list is None:
        unique_colors = np.unique(potlabs)
        color_mapping = dict(zip(list(unique_colors), colors.colors_default))
        try:
            final_color_mapping = [color_mapping[n[1]['type']] for n in nodes]
        except:
            print("Assigning colors..")
            final_color_mapping = [1] * len(nodes)
    else:
        node_types = [x[1] for x in g.nodes()]
        assert len(node_types) == len(color_list)
        try:
            cols = color_list            
        except:
            cols = colors.colors_default            
        id_col_map = {}
        for enx, j in enumerate(set(color_list)):
            id_col_map[j] = cols[enx]
        id_type_map = dict(zip(color_list, node_types))
        final_color_mapping = [id_col_map[j] for j in color_list]
        color_to_type_map = {}
        for k, v in id_type_map.items():
            actual_color = id_col_map[k]
            color_to_type_map[actual_color] = id_type_map[k]

    degrees = dict(nx.degree(nx.Graph(g)))

    if scale_by_size:
        nsizes = [
            np.log(v) * node_size if v > 10 else v for v in degrees.values()
        ]
    else:
        nsizes = [node_size for x in g.nodes()]

    if not node_sizes is None:
        nsizes = node_sizes

    # standard force -- directed layout
    if layout_algorithm == "force":
        pos = compute_force_directed_layout(g, layout_parameters)

    # random layout -- used for initialization of more complex algorithms
    elif layout_algorithm == "random":
        pos = compute_random_layout(g)

    elif layout_algorithm == "custom_coordinates":
        pos = layout_parameters['pos']

    elif layout_algorithm == "custom_coordinates_initial_force":
        pos = compute_force_directed_layout(g, layout_parameters)
    else:
        raise ValueError('Uknown layout algorithm: ' + str(layout_algorithm))

    if draw:
        nx.draw_networkx_edges(g,
                               pos,
                               alpha=alpha_channel,
                               edge_color="black",
                               width=edge_width,
                               arrows=False)
        scatter = nx.draw_networkx_nodes(g,
                                         pos,
                                         nodelist=[n1[0] for n1 in nodes],
                                         node_color=final_color_mapping,
                                         node_size=nsizes,
                                         alpha=alpha_channel)
    if labels is not None:
        for el in labels:
            pos_el = pos[el]
            if draw:
                plt.text(pos_el[0],
                         pos_el[1],
                         el,
                         fontsize=label_font_size,
                         color=text_color)


#        nx.draw_networkx_labels(g, pos, font_size=label_font_size)

    plt.axis('off')

    #  add legend {"color":"string"}
    if legend is not None and legend:
        legend_colors = set(id_col_map.values())
        if len(legend_colors) > 6:
            fs = "small"
        else:
            fs = "medium"
        markers = [
            plt.Line2D([0, 0], [0, 0], color=key, marker='o', linestyle='')
            for key in legend_colors
        ]
        if draw:
            plt.legend(markers,
                       [color_to_type_map[color] for color in legend_colors],
                       numpoints=1,
                       fontsize=fs)

    if display:
        plt.show()

    if not draw:
        return g, nsizes, final_color_mapping, pos


def interactive_hairball_plot(G,
                              nsizes,
                              final_color_mapping,
                              pos,
                              colorscale="Rainbow"):

    if not plotly_import:
        print("Please, install plotly!")
        return False

    edge_x = []
    edge_y = []
    for edge in G.edges():

        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(x=edge_x,
                            y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='text',
                            mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        hovertext=list(G.nodes()),
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale=colorscale,
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(thickness=15,
                          title='Node Connections',
                          xanchor='left',
                          titleside='right'),
            line_width=2))

    node_trace.marker.color = nsizes
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(title='Interactive relation explorer',
                                     titlefont_size=16,
                                     showlegend=False,
                                     hovermode='closest',
                                     margin=dict(b=20, l=5, r=5, t=40),
                                     annotations=[
                                         dict(text="By authors of the paper!",
                                              showarrow=False,
                                              xref="paper",
                                              yref="paper",
                                              x=0.005,
                                              y=-0.002)
                                     ],
                                     xaxis=dict(showgrid=False,
                                                zeroline=False,
                                                showticklabels=False),
                                     yaxis=dict(showgrid=False,
                                                zeroline=False,
                                                showticklabels=False)))
    fig.show()


if __name__ == "__main__":

    x = generate_random_networks(4)
    draw_multilayer_default(x, display=False, background_shape="circle")
    # generate_random_multiedges(x, 12, style="piramidal")
    generate_random_multiedges(x, 12, style="curve2_bezier")
    # network 1's 4 to network 6's 3 etc..
    # mel = [((1,1),(5,1))]
    # draw_multiedges(x,mel,input_type="tuple")

    plt.show()
