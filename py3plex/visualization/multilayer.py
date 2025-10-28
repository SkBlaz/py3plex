# This is the multiplex layer constructor class

# draw multi layered network, takes .nx object list as input

# imports first
from typing import Any, Dict, List, Optional, Union

import networkx as nx
import numpy as np

from py3plex import config
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


def _get_background_colors(background_color: str, num_networks: int, alphalevel: float) -> tuple:
    """Get background color palette for multilayer visualization.
    
    Args:
        background_color: Color scheme ("default", "rainbow", or None)
        num_networks: Number of networks/layers to color
        alphalevel: Original alpha level (modified if background_color is None)
        
    Returns:
        tuple: (color_list, modified_alphalevel)
    """
    if background_color == "default":
        color_list = colors.linear_gradient("#4286f4", n=num_networks)["hex"]
    elif background_color == "rainbow":
        color_list = colors.colors_default
    elif background_color is None:
        color_list = colors.colors_default
        alphalevel = 0
    else:
        color_list = colors.colors_default
    return color_list, alphalevel


def _get_network_colors(networks_color: str, num_networks: int) -> List[str]:
    """Get network color palette for multilayer visualization.
    
    Args:
        networks_color: Color scheme ("rainbow" or "black")
        num_networks: Number of networks/layers to color
        
    Returns:
        List[str]: List of color codes
    """
    if networks_color == "rainbow":
        return colors.colors_default
    elif networks_color == "black":
        return ["black"] * num_networks
    else:
        return colors.colors_default


def _preprocess_network(
    network: nx.Graph,
    remove_isolated_nodes: bool,
    verbose: bool
) -> tuple:
    """Preprocess a single network layer before drawing.
    
    Args:
        network: NetworkX graph to preprocess
        remove_isolated_nodes: Whether to remove isolated nodes
        verbose: Whether to log network information
        
    Returns:
        tuple: (processed_network, positions, degrees)
    """
    # Remove isolated nodes if requested
    if remove_isolated_nodes:
        isolates = list(nx.isolates(network))
        network = network.copy()
        network.remove_nodes_from(isolates)

    # Log network info if verbose
    if verbose:
        logger.info(nx_info(network))
    
    # Calculate degrees
    degrees = dict(nx.degree(nx.Graph(network)))
    
    # Remove nodes without positions
    no_position = []
    for node in network.nodes(data=True):
        if "pos" not in node[1]:
            no_position.append(node[0])

    if len(no_position) > 0:
        network = network.copy()
        network.remove_nodes_from(no_position)

    # Get positions
    positions = nx.get_node_attributes(network, "pos")
    
    return network, positions, degrees


def _compute_node_sizes(
    degrees: dict,
    node_size: int,
    scale_by_size: bool
) -> List[float]:
    """Compute node sizes based on degrees and scaling preference.
    
    Args:
        degrees: Dictionary of node degrees
        node_size: Base node size
        scale_by_size: Whether to scale by degree
        
    Returns:
        List[float]: List of node sizes
    """
    if scale_by_size:
        node_sizes = [vx * node_size for vx in degrees.values()]
    else:
        node_sizes = [node_size for _ in degrees.values()]

    # Fallback to default size if all sizes are zero
    if np.sum(node_sizes) == 0:
        node_sizes = [node_size for _ in degrees.values()]
    
    return node_sizes


def _draw_background_shape(
    shape_subplot: Any,
    background_shape: str,
    start_location: float,
    alphalevel: float,
    facecolor: str,
    rectanglex: float = 1,
    rectangley: float = 1,
) -> None:
    """Draw background shape for a single layer.
    
    Args:
        shape_subplot: Matplotlib axis to draw on
        background_shape: Shape type ("rectangle" or "circle")
        start_location: Starting position for the shape
        alphalevel: Transparency level
        facecolor: Color for the shape
        rectanglex: Rectangle width (if shape is rectangle)
        rectangley: Rectangle height (if shape is rectangle)
    """
    shadow_size = config.MULTILAYER_SHADOW_SIZE
    circle_size = config.MULTILAYER_CIRCLE_SIZE
    
    if background_shape == "rectangle":
        shape_subplot.add_patch(
            Rectangle(
                (start_location, start_location),
                rectanglex,
                rectangley,
                alpha=alphalevel,
                linestyle="dotted",
                fill=True,
                facecolor=facecolor,
            )
        )
    elif background_shape == "circle":
        shape_subplot.add_patch(
            Circle(
                (start_location + shadow_size, start_location + shadow_size),
                circle_size,
                color=facecolor,
                alpha=alphalevel,
            )
        )


def draw_multilayer_default(
    network_list: Union[List[nx.Graph], Dict[Any, nx.Graph]],
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
    """Core multilayer drawing method.

    Args:
        network_list: List of NetworkX graphs to visualize (or dict of layer_name -> graph)
        display: Whether to display the plot directly
        node_size: Base size of nodes
        alphalevel: Transparency level for background shapes
        rectanglex: Width of rectangular backgrounds
        rectangley: Height of rectangular backgrounds
        background_shape: Background shape type ("circle" or "rectangle")
        background_color: Background color scheme ("default", "rainbow", or None)
        networks_color: Network color scheme ("rainbow" or "black")
        labels: Layer labels to display
        arrowsize: Size of edge arrows
        label_position: Position offset for layer labels
        verbose: Whether to log network information
        remove_isolated_nodes: Whether to remove isolated nodes
        axis: Matplotlib axis to draw on (None for current axis)
        edge_size: Width of edges
        node_labels: Whether to display node labels
        node_font_size: Font size for node labels
        scale_by_size: Whether to scale node size by degree

    Returns:
        None
    """
    # Convert dict to list if necessary
    if isinstance(network_list, dict):
        network_list = list(network_list.values())
    
    shape_subplot = plt.gca()
    
    # Get color palettes
    facecolor_list_background, alphalevel = _get_background_colors(
        background_color, len(network_list), alphalevel
    )
    facecolor_list = _get_network_colors(networks_color, len(network_list))

    # Initialize layer positions
    start_location_network = 0
    start_location_background = 0

    # Draw each layer
    for color, network in enumerate(network_list):
        # Preprocess network
        network, positions, degrees = _preprocess_network(
            network, remove_isolated_nodes, verbose
        )
        
        # Offset positions for this layer
        for node in positions:
            positions[node] = (
                positions[node][0] + start_location_network,
                positions[node][1] + start_location_network
            )
        
        # Update the node attributes in the graph so that draw_multiedges can access the offset positions
        nx.set_node_attributes(network, positions, "pos")

        # Draw layer label if provided
        if labels:
            try:
                plt.text(
                    start_location_network + label_position,
                    start_location_network - label_position,
                    labels[color],  # type: ignore[index]
                )
            except Exception as es:
                logger.error("Error setting label: %s", es)

        # Draw background shape
        _draw_background_shape(
            shape_subplot,
            background_shape,
            start_location_background,
            alphalevel,
            facecolor_list_background[color],
            rectanglex,
            rectangley,
        )

        # Update positions for next layer
        start_location_network += config.MULTILAYER_LAYER_OFFSET  # type: ignore[assignment]
        start_location_background += config.MULTILAYER_LAYER_OFFSET  # type: ignore[assignment]

        # Compute node sizes
        node_sizes = _compute_node_sizes(degrees, node_size, scale_by_size)

        # Draw the network
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

    if display:
        plt.show()


def draw_multiedges(
    network_list: Union[List[nx.Graph], Dict[Any, nx.Graph]],
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
        network_list: List of NetworkX graphs (layers) or dict of layer_name -> graph
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
    # Convert dict to list if necessary
    if isinstance(network_list, dict):
        network_list = list(network_list.values())
    
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
    plt.imshow(matrix, interpolation="nearest", cmap="binary")
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
