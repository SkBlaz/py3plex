# This is the multiplex layer constructor class

# draw multi layered network, takes .nx object list as input

# imports first
from typing import Any, List, Optional, Union

import networkx as nx
import numpy as np

from py3plex.core.nx_compat import nx_info
from py3plex.logging_config import get_logger

logger = get_logger(__name__)

try:
    from matplotlib.patches import Circle, Rectangle
except ImportError:
    pass

import random

import matplotlib.pyplot as plt

from . import bezier  # those are bezier curves
from . import colors  # those are color ranges
from . import drawing_machinery, polyfit
from .layout_algorithms import compute_force_directed_layout, compute_random_layout

try:
    import plotly.graph_objects as go

    plotly_import = True

except ImportError:
    plotly_import = False


def draw_multilayer_default(
    network_list: List[nx.Graph],
    display: bool = True,
    node_size: int = 10,
    alphalevel: float = 0.13,
    rectanglex: float = 1,
    rectangley: float = 1,
    background_shape: str = "circle",
    background_color: str = "rainbow",
    networks_color: str = "rainbow",
    labels: bool = False,
    arrowsize: float = 0.5,
    label_position: int = 1,
    verbose: bool = False,
    remove_isolated_nodes: bool = False,
    axis: Optional[Any] = None,
    edge_size: float = 1,
    node_labels: bool = False,
    node_font_size: int = 5,
    scale_by_size: bool = False,
) -> None:
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
    #    main_figure = plt.figure()
    #    shape_subplot = main_figure.add_subplot(111)

    shape_subplot = plt.gca()
    if background_color == "default":

        facecolor_list_background = colors.linear_gradient(
            "#4286f4", n=len(network_list)
        )["hex"]

    elif background_color == "rainbow":

        facecolor_list_background = colors.colors_default

    elif background_color is None:

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
            logger.info(nx_info(network))
        degrees = dict(nx.degree(nx.Graph(network)))
        cntr = 0
        cntr_all = 0
        no_position = []
        all_positions = []
        for node in network.nodes(data=True):
            if "pos" not in node[1]:
                no_position.append(node[0])
                cntr += 1
            else:
                all_positions.append(node[1]["pos"])
                cntr_all += 1

        if len(no_position) > 0:
            network = network.copy()
            network.remove_nodes_from(no_position)

        positions = nx.get_node_attributes(network, "pos")
        cntr = 0

        for node, position in positions.items():
            position += start_location_network

        # this is the default delay for matplotlib canvas
        if labels:
            try:
                plt.text(
                    start_location_network + label_position,
                    start_location_network - label_position,
                    labels[color],  # type: ignore[index]
                )
            except Exception as es:
                logger.error("Error setting label: %s", es)

        if background_shape == "rectangle":
            shape_subplot.add_patch(
                Rectangle(
                    (start_location_background, start_location_background),
                    rectanglex,
                    rectangley,
                    alpha=alphalevel,
                    linestyle="dotted",
                    fill=True,
                    facecolor=facecolor_list_background[color],
                )
            )

        elif background_shape == "circle":
            shape_subplot.add_patch(
                Circle(
                    (
                        start_location_background + shadow_size,
                        start_location_background + shadow_size,
                    ),
                    circle_size,
                    color=facecolor_list_background[color],
                    alpha=alphalevel,
                )
            )
        else:
            pass

        start_location_network += 1.5  # type: ignore[assignment]
        start_location_background += 1.5  # type: ignore[assignment]
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

        drawing_machinery.draw(
            network,
            positions,
            node_color=facecolor_list[color],
            with_labels=node_labels,
            edge_size=edge_size,
            node_size=node_sizes,
            arrowsize=arrowsize,
            ax=axis,
            font_size=node_font_size,
        )
        color += 1

    if display:
        plt.show()


def draw_multiedges(
    network_list: List[nx.Graph],
    multi_edge_tuple: List[Any],  # Can be various tuple types
    input_type: str = "nodes",
    linepoints: str = "-.",
    alphachannel: float = 0.3,
    linecolor: str = "black",
    curve_height: float = 1,
    style: str = "curve2_bezier",
    linewidth: float = 1,
    invert: bool = False,
    linmod: str = "both",
    resolution: float = 0.001,
) -> None:
    """Draw edges connecting multiple layers.
    
    Args:
        network_list: List of NetworkX graphs (layers)
        multi_edge_tuple: Tuple specifying edges to draw
        input_type: Type of input ("nodes" or other)
        linepoints: Line style
        alphachannel: Transparency level
        linecolor: Color of the lines
        curve_height: Height of curved edges
        style: Style of edges ("curve2_bezier", "line", etc.)
        linewidth: Width of lines
        invert: Whether to invert drawing direction
        linmod: Line modification mode
        resolution: Resolution for curve drawing
    """
    # indices are correct network positions
    #    main_figure = plt.figure()
    #    shape_subplot = main_figure.add_subplot(111)

    if input_type == "nodes":

        network_positions = [
            nx.get_node_attributes(network, "pos") for network in network_list
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
                # [coordinates_node_first[0], coordinates_node_first[1]]
                p2 = [coordinates_node_first[1], coordinates_node_second[1]]  # []

                if style == "line":

                    plt.plot(
                        p1,
                        p2,
                        linestyle=linepoints,
                        lw=1,
                        alpha=alphachannel,
                        color=linecolor,
                    )

                elif style == "curve2_bezier":

                    x, y = bezier.draw_bezier(
                        len(network_list),
                        p1,  # type: ignore[arg-type]
                        p2,  # type: ignore[arg-type]
                        path_height=curve_height,
                        inversion=invert,
                        linemode=linmod,
                        resolution=resolution,
                    )

                    plt.plot(
                        x,
                        y,
                        linestyle=linepoints,
                        lw=linewidth,
                        alpha=alphachannel,
                        color=linecolor,
                    )

                elif style == "curve3_bezier":

                    x, y = bezier.draw_bezier(
                        len(network_list), p1, p2, mode="cubic", resolution=resolution  # type: ignore[arg-type]
                    )

                elif style == "curve3_fit":

                    x, y = polyfit.draw_order3(len(network_list), p1, p2)

                    plt.plot(x, y)

                elif style == "piramidal":

                    x, y = polyfit.draw_piramidal(len(network_list), p1, p2)
                    plt.plot(
                        x,
                        y,
                        linestyle=linepoints,
                        lw=1,
                        alpha=alphachannel,
                        color=linecolor,
                    )

                else:
                    pass

            except Exception:
                pass


#                print(err,"test")


def generate_random_multiedges(
    network_list: List[nx.Graph],
    random_edges: int,
    style: str = "line",
    linepoints: str = "-.",
    upper_first: int = 2,
    lower_first: int = 0,
    lower_second: int = 2,
    inverse_tag: bool = False,
    pheight: float = 1,
) -> None:
    """Generate and draw random multi-layer edges.
    
    Args:
        network_list: List of NetworkX graphs (layers)
        random_edges: Number of random edges to generate
        style: Style of edges to draw
        linepoints: Line style
        upper_first: Upper bound for first layer
        lower_first: Lower bound for first layer
        lower_second: Lower bound for second layer
        inverse_tag: Whether to invert drawing
        pheight: Height parameter for curves
    """

    #    main_figure = plt.figure()
    #    shape_subplot = main_figure.add_subplot(111)
    #    main_figure.add_subplot(111)

    # this needs to be in the form of:
    for _k in range(random_edges):
        try:
            random_network1 = random.randint(0, upper_first)
            random_network2 = random.randint(lower_second, len(network_list))

            node_first = random.randint(1, 3)
            node_second = random.randint(1, 3)

            positions_first_net = nx.get_node_attributes(
                network_list[random_network1], "pos"
            )
            positions_second_net = nx.get_node_attributes(
                network_list[random_network2], "pos"
            )

            p1 = [
                positions_first_net[node_first][0],
                positions_second_net[node_second][0],
            ]
            p2 = [
                positions_first_net[node_first][1],
                positions_second_net[node_second][1],
            ]

            if style == "line":

                plt.plot(p1, p2, "k-", lw=1, color="black", linestyle="dotted")

            elif style == "curve2_bezier":

                x, y = bezier.draw_bezier(
                    len(network_list),
                    p1,  # type: ignore[arg-type]
                    p2,  # type: ignore[arg-type]
                    inversion=inverse_tag,
                    path_height=pheight,
                )
                plt.plot(x, y, linestyle=linepoints, lw=1, alpha=0.3)

            elif style == "curve3_bezier":

                x, y = bezier.draw_bezier(len(network_list), p1, p2, mode="cubic")  # type: ignore[arg-type]

            elif style == "curve3_fit":

                x, y = polyfit.draw_order3(len(network_list), p1, p2)

                plt.plot(x, y)

            elif style == "piramidal":

                x, y = polyfit.draw_piramidal(len(network_list), p1, p2)
                plt.plot(x, y, color="black", alpha=0.3, linestyle="-.", lw=1)

            else:
                pass
        except (IndexError, KeyError, ValueError):
            pass


def generate_random_networks(number_of_networks: int) -> List[nx.Graph]:
    """Generate random networks for testing.
    
    Args:
        number_of_networks: Number of random networks to generate
        
    Returns:
        List of NetworkX graphs with random layouts
    """

    network_list = []
    for _j in range(number_of_networks):
        tmp_graph = nx.gnm_random_graph(random.randint(60, 300), random.randint(5, 300))
        tmp_pos = nx.spring_layout(tmp_graph)
        nx.set_node_attributes(tmp_graph, "pos", tmp_pos)
        network_list.append(tmp_graph)
    return network_list


def supra_adjacency_matrix_plot(matrix: np.ndarray, display: bool = False) -> None:
    """Plot a supra-adjacency matrix.
    
    Args:
        matrix: Supra-adjacency matrix to plot
        display: Whether to display the plot immediately
    """
    plt.imshow(matrix, interpolation="nearest", cmap=plt.cm.binary)
    if display:
        plt.show()


def onclick(event: Any) -> None:
    """Handle mouse click events on plots.
    
    Args:
        event: Matplotlib event object
    """
    logger.debug(
        "%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f",
        "double" if event.dblclick else "single",
        event.button,
        event.x,
        event.y,
        event.xdata,
        event.ydata,
    )


def hairball_plot(
    g: Union[nx.Graph, Any],
    color_list: Optional[Union[List[str], List[int]]] = None,
    display: bool = False,
    node_size: float = 1,
    text_color: str = "black",
    node_sizes: Optional[List[float]] = None,  # for custom sizes
    layout_parameters: Optional[dict] = None,
    legend: Optional[Any] = None,
    scale_by_size: bool = True,
    layout_algorithm: str = "force",
    edge_width: float = 0.01,
    alpha_channel: float = 0.5,
    labels: Optional[List[str]] = None,
    draw: bool = True,
    label_font_size: int = 2,
) -> Optional[Any]:  # Returns tuple when draw=False, None otherwise
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

    #    main_figure = plt.figure()
    #    shape_subplot = main_figure.add_subplot(111)

    logger.info("Beginning parsing..")
    nodes = g.nodes(data=True)
    potlabs = []
    #    fig, ax = plt.subplots()
    for node in nodes:
        try:
            potlabs.append(node[0][1])
        except (IndexError, TypeError):
            potlabs.append("unlabeled")

    if color_list is None:
        unique_colors = np.unique(potlabs)
        color_mapping = dict(zip(list(unique_colors), colors.colors_default))
        try:
            color_list = [color_mapping[n[1]["type"]] for n in nodes]
        except (KeyError, IndexError, TypeError):
            logger.info("Assigning colors..")
            color_list = [1] * len(nodes)

    node_types = [x[1] for x in g.nodes()]
    assert len(node_types) == len(color_list)

    try:
        # Check if color_list contains actual colors or numeric IDs
        first_color = color_list[0] if color_list else None
        if isinstance(first_color, (int, float)) or (
            isinstance(first_color, str) and first_color.isdigit()
        ):
            # color_list contains numeric IDs, map them to actual colors
            cols = colors.colors_default
        else:
            # color_list contains actual color values
            cols = color_list  # type: ignore[assignment]
    except Exception:
        logger.info("Using default palette")
        cols = colors.colors_default
    id_col_map = {}
    for enx, j in enumerate(set(color_list)):
        id_col_map[j] = cols[enx]
    id_type_map = dict(zip(color_list, node_types))
    final_color_mapping = [id_col_map[j] for j in color_list]
    color_to_type_map = {}
    for k, _v in id_type_map.items():
        actual_color = id_col_map[k]
        color_to_type_map[actual_color] = id_type_map[k]

    degrees = dict(nx.degree(nx.Graph(g)))

    if scale_by_size:
        nsizes = [np.log(v) * node_size if v > 10 else v for v in degrees.values()]
    else:
        nsizes = [node_size for x in g.nodes()]

    if node_sizes is not None:
        nsizes = node_sizes

    # standard force -- directed layout
    if layout_algorithm == "force":
        pos = compute_force_directed_layout(g, layout_parameters)

    # random layout -- used for initialization of more complex algorithms
    elif layout_algorithm == "random":
        pos = compute_random_layout(g)

    elif layout_algorithm == "custom_coordinates":
        pos = layout_parameters["pos"]

    elif layout_algorithm == "custom_coordinates_initial_force":
        pos = compute_force_directed_layout(g, layout_parameters)
    else:
        raise ValueError("Uknown layout algorithm: " + str(layout_algorithm))

    if draw:
        nx.draw_networkx_edges(
            g,
            pos,
            alpha=alpha_channel,
            edge_color="black",
            width=edge_width,
            arrows=False,
        )
        nx.draw_networkx_nodes(
            g,
            pos,
            nodelist=[n1[0] for n1 in nodes],
            node_color=final_color_mapping,
            node_size=nsizes,
            alpha=alpha_channel,
        )
    if labels is not None:
        for el in labels:
            pos_el = pos[el]
            if draw:
                plt.text(
                    pos_el[0], pos_el[1], el, fontsize=label_font_size, color=text_color
                )

    #        nx.draw_networkx_labels(g, pos, font_size=label_font_size)

    plt.axis("off")

    #  add legend {"color":"string"}
    if legend is not None and legend:
        legend_colors = set(id_col_map.values())
        if len(legend_colors) > 6:
            fs = "small"
        else:
            fs = "medium"
        markers = [
            plt.Line2D([0, 0], [0, 0], color=key, marker="o", linestyle="")
            for key in legend_colors
        ]
        if draw:
            plt.legend(
                markers,
                [color_to_type_map[color] for color in legend_colors],
                numpoints=1,
                fontsize=fs,
            )

    if display:
        plt.show()

    if not draw:
        return g, nsizes, final_color_mapping, pos
    return None  # Explicit return when draw=True


def interactive_hairball_plot(
    G: nx.Graph,
    nsizes: List[float],
    final_color_mapping: dict,
    pos: dict,
    colorscale: str = "Rainbow",
) -> Union[bool, Any]:
    """Create an interactive 3D hairball plot using Plotly.
    
    Args:
        G: NetworkX graph to visualize
        nsizes: Node sizes
        final_color_mapping: Mapping of nodes to colors
        pos: Node positions
        colorscale: Color scale to use
        
    Returns:
        False if plotly not available, otherwise plotly figure object
    """

    #    main_figure = plt.figure()
    #    shape_subplot = main_figure.add_subplot(111)

    if not plotly_import:
        logger.error("Please, install plotly!")
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

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line={"width": 0.5, "color": "#888"},
        hoverinfo="text",
        mode="lines",
    )

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hovertext=list(G.nodes()),
        hoverinfo="text",
        marker={
            "showscale": True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            "colorscale": colorscale,
            "reversescale": True,
            "color": [],
            "size": 10,
            "colorbar": {
                "thickness": 15,
                "title": "Node Connections",
                "xanchor": "left",
                "titleside": "right",
            },
            "line_width": 2,
        },
    )

    node_trace.marker.color = nsizes
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Interactive relation explorer",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin={"b": 20, "l": 5, "r": 5, "t": 40},
            annotations=[
                {
                    "text": "By authors of the paper!",
                    "showarrow": False,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.005,
                    "y": -0.002,
                }
            ],
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        ),
    )
    fig.show()
    return fig  # Return the figure object


if __name__ == "__main__":

    x = generate_random_networks(4)
    draw_multilayer_default(x, display=False, background_shape="circle")
    # generate_random_multiedges(x, 12, style="piramidal")
    generate_random_multiedges(x, 12, style="curve2_bezier")
    # network 1's 4 to network 6's 3 etc..
    # mel = [((1,1),(5,1))]
    # draw_multiedges(x,mel,input_type="tuple")

    plt.show()
