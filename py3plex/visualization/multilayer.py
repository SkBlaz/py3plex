# This is the multiplex layer constructor class

# draw multi layered network, takes .nx object list as input

from typing import Any, Dict, List, Optional, Tuple, Union
import warnings

import networkx as nx
import numpy as np

from py3plex import config
from py3plex.core.nx_compat import nx_info
from py3plex.exceptions import Py3plexLayoutError, VisualizationError
from py3plex.logging_config import get_logger

logger = get_logger(__name__)

try:
    from matplotlib.patches import Circle, Rectangle
    MATPLOTLIB_PATCHES_AVAILABLE = True
except ImportError:
    MATPLOTLIB_PATCHES_AVAILABLE = False
    Circle = None
    Rectangle = None

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


def _get_background_colors(
    background_color: str, num_networks: int, alphalevel: float
) -> tuple:
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
    network: nx.Graph, remove_isolated_nodes: bool, verbose: bool
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
    degrees: dict, node_size: int, scale_by_size: bool
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
    if not MATPLOTLIB_PATCHES_AVAILABLE:
        raise ImportError(
            "matplotlib.patches is not available. "
            "Please install matplotlib to use background shapes in multilayer visualization."
        )

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
    display: bool = False,
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
    ax: Optional[Any] = None,
    edge_size: float = 1,
    node_labels: bool = False,
    node_font_size: int = 5,
    scale_by_size: bool = False,
    *,  # Force remaining args to be keyword-only
    axis: Optional[Any] = None,  # Deprecated: use ax instead
) -> Any:
    """Core multilayer drawing method.

    Draws a diagonal multilayer network visualization where each layer is
    offset to create a 3D-like effect. Nodes within each layer are drawn
    with their positions, and background shapes indicate layer boundaries.

    Args:
        network_list: List of NetworkX graphs to visualize (or dict of layer_name -> graph)
        display: If True, calls plt.show() after drawing. Default is False
            to let the caller control rendering.
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
        ax: Matplotlib Axes to draw on. If None, uses current axes (plt.gca())
        edge_size: Width of edges
        node_labels: Whether to display node labels
        node_font_size: Font size for node labels
        scale_by_size: Whether to scale node size by degree
        axis: Deprecated. Use ax instead.

    Returns:
        Matplotlib Axes object containing the visualization.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from py3plex.visualization import draw_multilayer_default
        >>> # Create figure and get axes
        >>> fig, ax = plt.subplots(figsize=(10, 10))
        >>> # Draw on the axes (returns the axes)
        >>> ax = draw_multilayer_default(graphs, ax=ax)
        >>> # Caller controls when to display
        >>> plt.savefig("multilayer.png")  # or plt.show()
    """
    # Handle deprecated 'axis' parameter with warning
    if axis is not None:
        warnings.warn(
            "The 'axis' parameter is deprecated. Use 'ax' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if ax is None:
            ax = axis
    
    # Convert dict to list if necessary
    if isinstance(network_list, dict):
        network_list = list(network_list.values())

    # Use provided axes or get current axes
    if ax is None:
        shape_subplot = plt.gca()
    else:
        shape_subplot = ax

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
                positions[node][1] + start_location_network,
            )

        # Update node attributes so draw_multiedges can access offset positions
        nx.set_node_attributes(network, positions, "pos")

        # Draw layer label if provided
        if labels:
            try:
                shape_subplot.text(
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
            ax=shape_subplot,
            font_size=node_font_size,
        )

    if display:
        plt.show()

    return shape_subplot


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
    ax: Optional[Any] = None,
) -> Any:
    """Draw edges connecting multiple layers.

    Draws curved or straight edges that connect nodes across different layers
    in a multilayer network visualization. Typically used after draw_multilayer_default
    to add inter-layer connections.

    Args:
        network_list: List of NetworkX graphs (layers) or dict of layer_name -> graph
        multi_edge_tuple: List of tuples specifying edges to draw, e.g. [(node1, node2), ...]
        input_type: Type of input ("nodes" or other)
        linepoints: Line style (e.g., "-.", "--", "-")
        alphachannel: Transparency level (0.0 to 1.0)
        linecolor: Color of the lines
        curve_height: Height of curved edges
        style: Style of edges ("curve2_bezier", "line", "curve3_bezier", "curve3_fit", "piramidal")
        linewidth: Width of lines
        invert: Whether to invert drawing direction
        linmod: Line modification mode
        resolution: Resolution for curve drawing
        ax: Matplotlib Axes to draw on. If None, uses current axes (plt.gca())

    Returns:
        Matplotlib Axes object containing the visualization.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from py3plex.visualization import draw_multilayer_default, draw_multiedges
        >>> fig, ax = plt.subplots(figsize=(10, 10))
        >>> ax = draw_multilayer_default(graphs, ax=ax)
        >>> ax = draw_multiedges(graphs, edges, ax=ax)
        >>> plt.savefig("multilayer_with_edges.png")
    """
    # Convert dict to list if necessary
    if isinstance(network_list, dict):
        network_list = list(network_list.values())

    # Use provided axes or get current axes
    if ax is None:
        ax = plt.gca()

    # indices are correct network positions

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

                    ax.plot(
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

                    ax.plot(
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

                    ax.plot(x, y)

                elif style == "piramidal":

                    x, y = polyfit.draw_piramidal(len(network_list), p1, p2)
                    ax.plot(
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

    return ax


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


def supra_adjacency_matrix_plot(
    matrix: np.ndarray,
    display: bool = False,
    ax: Optional[Any] = None,
    cmap: str = "binary",
) -> Any:
    """Plot a supra-adjacency matrix as a heatmap.

    Visualizes the supra-adjacency matrix of a multilayer network, where the
    matrix shows both intra-layer and inter-layer connections. The matrix is
    displayed as a heatmap with configurable colormap.

    Args:
        matrix: Supra-adjacency matrix to plot (numpy ndarray or scipy sparse matrix)
        display: If True, calls plt.show() after drawing. Default is False
            to let the caller control rendering.
        ax: Matplotlib Axes to draw on. If None, uses current axes (plt.gca())
        cmap: Colormap to use for the heatmap (default: "binary")

    Returns:
        Matplotlib Axes object containing the visualization.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from py3plex.visualization import supra_adjacency_matrix_plot
        >>> fig, ax = plt.subplots(figsize=(8, 8))
        >>> ax = supra_adjacency_matrix_plot(supra_matrix, ax=ax, cmap="viridis")
        >>> plt.colorbar(ax.images[0])
        >>> plt.savefig("supra_matrix.png")
    """
    if ax is None:
        ax = plt.gca()
    
    ax.imshow(matrix, interpolation="nearest", cmap=cmap)
    
    if display:
        plt.show()
    
    return ax


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
    ax: Optional[Any] = None,
) -> Optional[Any]:
    """Draw a force-directed "hairball" visualization of a network.

    Creates a force-directed layout visualization where nodes are colored by
    type/layer and sized by degree. This is a common visualization for showing
    the overall structure of a network.

    Args:
        g: NetworkX graph to visualize
        color_list: List of colors for nodes. If None, colors are assigned
            based on node types.
        display: If True, calls plt.show() after drawing. Default is False
            to let the caller control rendering.
        node_size: Base size of nodes
        text_color: Color for node labels
        node_sizes: Custom list of node sizes (overrides node_size and scale_by_size)
        layout_parameters: Parameters for the layout algorithm (e.g., {"pos": {...}})
        legend: If True, display a legend mapping colors to node types
        scale_by_size: If True, scale node sizes by log(degree)
        layout_algorithm: Layout algorithm to use. Options:
            - "force": Force-directed layout (spring layout)
            - "random": Random layout
            - "custom_coordinates": Use positions from layout_parameters["pos"]
            - "custom_coordinates_initial_force": Use custom positions as initial layout
        edge_width: Width of edges
        alpha_channel: Transparency level (0.0 to 1.0)
        labels: List of node labels to display (None for no labels)
        draw: If True, draw the network. If False, only compute layout and return data.
        label_font_size: Font size for node labels
        ax: Matplotlib Axes to draw on. If None, uses current axes (plt.gca())

    Returns:
        - If draw=True: Matplotlib Axes object containing the visualization
        - If draw=False: Tuple of (graph, node_sizes, color_mapping, positions)

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from py3plex.visualization import hairball_plot
        >>> fig, ax = plt.subplots(figsize=(10, 10))
        >>> ax = hairball_plot(network.core_network, ax=ax, legend=True)
        >>> plt.savefig("hairball.png")
    """

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
        raise Py3plexLayoutError(
            f"Unknown layout algorithm: '{layout_algorithm}'. "
            f"Supported algorithms: 'force', 'spring', 'circular', 'kamada_kawai', 'spectral', "
            f"'custom_coordinates', 'custom_coordinates_initial_force'. "
            f"Please choose a valid layout algorithm."
        )

    # Use provided axes or get current axes
    if ax is None:
        ax = plt.gca()

    if draw:
        nx.draw_networkx_edges(
            g,
            pos,
            ax=ax,
            alpha=alpha_channel,
            edge_color="black",
            width=edge_width,
            arrows=False,
        )
        nx.draw_networkx_nodes(
            g,
            pos,
            ax=ax,
            nodelist=[n1[0] for n1 in nodes],
            node_color=final_color_mapping,
            node_size=nsizes,
            alpha=alpha_channel,
        )
    if labels is not None:
        for el in labels:
            pos_el = pos[el]
            if draw:
                ax.text(
                    pos_el[0], pos_el[1], el, fontsize=label_font_size, color=text_color
                )

    #        nx.draw_networkx_labels(g, pos, font_size=label_font_size)

    ax.axis("off")

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
            ax.legend(
                markers,
                [color_to_type_map[color] for color in legend_colors],
                numpoints=1,
                fontsize=fs,
            )

    if display:
        plt.show()

    if not draw:
        return g, nsizes, final_color_mapping, pos
    return ax  # Return the axes when draw=True


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
                "title": {
                    "text": "Node Connections",
                    "side": "right"
                },
                "xanchor": "left",
            },
            "line_width": 2,
        },
    )

    node_trace.marker.color = nsizes
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title={
                "text": "Interactive relation explorer",
                "font": {"size": 16}
            },
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


def interactive_diagonal_plot(
    network_list: Union[List[nx.Graph], Dict[Any, nx.Graph]],
    layer_labels: Optional[List[str]] = None,
    layout_algorithm: str = "force",
    layer_gap: float = 4.0,
    node_size_base: int = 8,
    layer_colors: Optional[List[str]] = None,
    show_interlayer_edges: bool = True,
    interlayer_edges: Optional[List[Tuple[Any, Any]]] = None,
) -> Union[bool, Any]:
    """Create an interactive 2.5D diagonal multilayer plot using Plotly.

    This function creates an interactive version of the diagonal multilayer
    visualization, mimicking the traditional 2D diagonal layout but in an
    interactive 3D environment. Each layer is positioned diagonally with
    clear visual separation, similar to the static diagonal visualization.

    Args:
        network_list: List of NetworkX graphs (layers) or dict of layer_name -> graph
        layer_labels: Optional labels for each layer
        layout_algorithm: Layout algorithm for nodes ("force", "circular", "random")
        layer_gap: Distance between layers in diagonal direction (default: 2.5)
        node_size_base: Base size for nodes (default: 8)
        layer_colors: Optional list of colors for each layer (HTML color names or hex)
        show_interlayer_edges: Whether to show inter-layer edges
        interlayer_edges: List of tuples (node1, node2) for inter-layer connections

    Returns:
        False if plotly not available, otherwise plotly figure object

    Examples:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.load_network("network.txt", input_type="multiedgelist")
        >>> labels, graphs, multilinks = net.get_layers("diagonal")
        >>> fig = interactive_diagonal_plot(graphs, layer_labels=labels)
    """
    if not plotly_import:
        logger.error("Please install plotly! Use: pip install plotly")
        return False

    # Convert dict to list if necessary
    if isinstance(network_list, dict):
        if layer_labels is None:
            layer_labels = list(network_list.keys())
        network_list = list(network_list.values())

    if layer_labels is None:
        layer_labels = [f"Layer {i+1}" for i in range(len(network_list))]

    # Define default layer colors if not provided
    if layer_colors is None:
        # Use distinct colors for each layer
        default_colors = [
            '#FF6B6B',  # Coral red
            '#4ECDC4',  # Turquoise
            '#FFD93D',  # Yellow
            '#95E1D3',  # Mint
            '#F38181',  # Light coral
            '#AA96DA',  # Lavender
            '#FCBAD3',  # Pink
            '#A8D8EA',  # Light blue
        ]
        layer_colors = [default_colors[i % len(default_colors)] for i in range(len(network_list))]

    # Prepare data structures
    all_traces = []
    layer_positions = {}

    # Calculate layer spacing based on the traditional diagonal offset
    # In the original, each layer is offset by MULTILAYER_LAYER_OFFSET (1.5) in both x and y
    layer_offset = layer_gap

    # Process each layer
    for layer_idx, (layer_graph, layer_label) in enumerate(zip(network_list, layer_labels)):
        if layer_graph.number_of_nodes() == 0:
            continue

        # Compute 2D layout for this layer independently
        # Adjust parameters based on network size for better node dispersion
        num_nodes = layer_graph.number_of_nodes()

        if layout_algorithm == "force":
            # Use adaptive k parameter based on network size to prevent overlap
            # Larger k = more spacing between nodes
            k_param = None  # Let NetworkX auto-calculate for better spacing
            if num_nodes > 10:
                k_param = 1.0 / (num_nodes ** 0.5)  # Adaptive spacing

            pos_2d = nx.spring_layout(
                layer_graph,
                k=k_param,
                iterations=100,  # More iterations for better convergence
                seed=42
            )
        elif layout_algorithm == "circular":
            pos_2d = nx.circular_layout(layer_graph)
        elif layout_algorithm == "random":
            pos_2d = nx.random_layout(layer_graph, seed=42)
        else:
            # Default to force with adaptive parameters
            k_param = None
            if num_nodes > 10:
                k_param = 1.0 / (num_nodes ** 0.5)
            pos_2d = nx.spring_layout(
                layer_graph,
                k=k_param,
                iterations=100,
                seed=42
            )

        # Convert to 3D positions with proper diagonal offset
        # Each layer gets its own "plane" offset diagonally
        diagonal_offset = layer_idx * layer_offset
        z_offset = layer_idx * 1.2  # Increased Z separation for better depth perception

        pos_3d = {}
        for node, (x, y) in pos_2d.items():
            # Scale the layout to better fill the viewport
            # Larger networks need more scaling to maintain spacing
            scale_factor = 2.5 if num_nodes > 10 else 2.0
            scaled_x = x * scale_factor
            scaled_y = y * scale_factor
            # Apply diagonal offset (mimicking the 2D diagonal layout)
            pos_3d[node] = (
                scaled_x + diagonal_offset,
                scaled_y + diagonal_offset,
                z_offset
            )

        layer_positions[layer_idx] = pos_3d
        layer_color = layer_colors[layer_idx]

        # Create edge traces for this layer with layer-specific color
        edge_x, edge_y, edge_z = [], [], []
        for edge in layer_graph.edges():
            x0, y0, z0 = pos_3d[edge[0]]
            x1, y1, z1 = pos_3d[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])

        if edge_x:
            # Convert hex color to rgba with alpha
            edge_trace = go.Scatter3d(
                x=edge_x,
                y=edge_y,
                z=edge_z,
                mode='lines',
                line=dict(color=layer_color, width=1.5),
                opacity=0.4,
                hoverinfo='none',
                name=f'{layer_label} edges',
                showlegend=False,
                legendgroup=layer_label
            )
            all_traces.append(edge_trace)

        # Create node trace for this layer with distinct layer color
        node_x, node_y, node_z = [], [], []
        node_text = []
        node_sizes = []

        for node in layer_graph.nodes():
            x, y, z = pos_3d[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            degree = layer_graph.degree(node)
            node_sizes.append(node_size_base + degree * 3)
            node_text.append(f"<b>{node}</b><br>Layer: {layer_label}<br>Degree: {degree}")

        # Color all nodes in this layer with the same distinct color
        node_trace = go.Scatter3d(
            x=node_x,
            y=node_y,
            z=node_z,
            mode='markers',
            marker=dict(
                size=node_sizes,
                color=layer_color,
                line=dict(color='white', width=1),
                opacity=0.9
            ),
            text=node_text,
            hoverinfo='text',
            name=layer_label,
            showlegend=True,
            legendgroup=layer_label
        )
        all_traces.append(node_trace)

    # Add inter-layer edges if requested
    if show_interlayer_edges and interlayer_edges:
        inter_edge_x, inter_edge_y, inter_edge_z = [], [], []

        for node1, node2 in interlayer_edges:
            # Find which layers these nodes belong to
            found = False
            for idx1, pos_dict1 in layer_positions.items():
                if node1 in pos_dict1:
                    for idx2, pos_dict2 in layer_positions.items():
                        if idx2 != idx1 and node2 in pos_dict2:
                            x0, y0, z0 = pos_dict1[node1]
                            x1, y1, z1 = pos_dict2[node2]
                            inter_edge_x.extend([x0, x1, None])
                            inter_edge_y.extend([y0, y1, None])
                            inter_edge_z.extend([z0, z1, None])
                            found = True
                            break
                if found:
                    break

        if inter_edge_x:
            inter_edge_trace = go.Scatter3d(
                x=inter_edge_x,
                y=inter_edge_y,
                z=inter_edge_z,
                mode='lines',
                line=dict(color='rgba(100, 100, 100, 0.4)', width=2, dash='dash'),
                hoverinfo='none',
                name='Inter-layer',
                showlegend=True
            )
            all_traces.append(inter_edge_trace)

    # Create figure
    fig = go.Figure(data=all_traces)

    # Update layout for optimal 2.5D diagonal view
    fig.update_layout(
        title=dict(
            text='<b>Interactive Diagonal Multilayer Network</b><br><sub>Rotate • Zoom • Hover for details</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#2C3E50')
        ),
        scene=dict(
            xaxis=dict(
                showgrid=True,
                zeroline=False,
                showticklabels=False,
                title='',
                gridcolor='rgba(200, 200, 200, 0.2)',
                showbackground=False
            ),
            yaxis=dict(
                showgrid=True,
                zeroline=False,
                showticklabels=False,
                title='',
                gridcolor='rgba(200, 200, 200, 0.2)',
                showbackground=False
            ),
            zaxis=dict(
                showgrid=True,
                zeroline=False,
                showticklabels=False,
                title='',
                gridcolor='rgba(200, 200, 200, 0.2)',
                showbackground=False
            ),
            bgcolor='rgba(250, 250, 250, 1)',
            camera=dict(
                eye=dict(x=1.1, y=1.1, z=0.9),  # Closer camera for better viewport utilization
                center=dict(x=0, y=0, z=0),
                up=dict(x=0, y=0, z=1)
            ),
            aspectmode='data'  # Changed from 'cube' to 'data' for better scaling
        ),
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1,
            font=dict(size=11)
        ),
        hovermode='closest',
        margin=dict(l=0, r=0, t=80, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    fig.show()
    return fig


def visualize_multilayer_network(
    multilayer_network,
    visualization_type: str = "diagonal",
    **kwargs
):
    """High-level function to visualize multilayer networks with multiple visualization modes.

    This function provides a unified interface for various multilayer network visualization
    techniques, making it easy to switch between different visual representations.

    Args:
        multilayer_network: A MultiLayerNetwork instance from py3plex.core.multinet
        visualization_type: Type of visualization to use. Options:
            - "diagonal": Default layer-centric diagonal layout (existing behavior)
            - "small_multiples": One subplot per layer with shared or independent layouts
            - "edge_colored_projection": Aggregate projection with edge colors by layer
            - "supra_adjacency_heatmap": Matrix representation of multilayer structure
            - "radial_layers": Concentric circles for layers with radial inter-layer edges
            - "ego_multilayer": Ego-centric view focused on a specific node
        **kwargs: Additional keyword arguments specific to each visualization type.
            See individual plot functions for details.

    Returns:
        matplotlib.figure.Figure: The created figure object

    Raises:
        ValueError: If visualization_type is not recognized

    Examples:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.load_network("network.txt", input_type="multiedgelist")
        >>>
        >>> # Use default diagonal visualization
        >>> fig = visualize_multilayer_network(net)
        >>>
        >>> # Use small multiples view
        >>> fig = visualize_multilayer_network(net, visualization_type="small_multiples")
        >>>
        >>> # Use edge-colored projection
        >>> fig = visualize_multilayer_network(net, visualization_type="edge_colored_projection")
    """
    if visualization_type == "diagonal":
        # Use existing visualization method for backward compatibility
        fig = plt.gcf()
        multilayer_network.visualize_network(style="diagonal", **kwargs)
        return fig
    elif visualization_type == "small_multiples":
        return plot_small_multiples(multilayer_network, **kwargs)
    elif visualization_type == "edge_colored_projection":
        return plot_edge_colored_projection(multilayer_network, **kwargs)
    elif visualization_type == "supra_adjacency_heatmap":
        return plot_supra_adjacency_heatmap(multilayer_network, **kwargs)
    elif visualization_type == "radial_layers":
        return plot_radial_layers(multilayer_network, **kwargs)
    elif visualization_type == "ego_multilayer":
        return plot_ego_multilayer(multilayer_network, **kwargs)
    else:
        raise VisualizationError(
            f"Unknown visualization_type: '{visualization_type}'. "
            f"Valid options are: 'diagonal', 'small_multiples', "
            f"'edge_colored_projection', 'supra_adjacency_heatmap', "
            f"'radial_layers', 'ego_multilayer'. "
            f"Please choose a valid visualization type."
        )


def plot_small_multiples(
    multilayer_network,
    layout: str = "spring",
    max_cols: int = 3,
    node_size: int = 50,
    shared_layout: bool = True,
    show_layer_titles: bool = True,
    figsize: Optional[Tuple[float, float]] = None,
    **kwargs
):
    """Create a small multiples visualization with one subplot per layer.

    This visualization shows each layer as a separate subplot in a grid layout,
    making it easy to compare the structure of different layers side-by-side.

    Args:
        multilayer_network: A MultiLayerNetwork instance
        layout: Layout algorithm to use ("spring", "circular", "random", "kamada_kawai")
        max_cols: Maximum number of columns in the subplot grid
        node_size: Size of nodes in each subplot
        shared_layout: If True, compute one layout and reuse for all layers;
                       if False, compute independent layouts per layer
        show_layer_titles: If True, show layer names as subplot titles
        figsize: Optional figure size as (width, height) tuple
        **kwargs: Additional arguments passed to nx.draw_networkx

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Get layers as separate networkx graphs
    layers_dict = {}
    if hasattr(multilayer_network, 'core_network') and multilayer_network.core_network is not None:
        # Extract individual layers from the multilayer network
        for node in multilayer_network.core_network.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                layer_id = node[1]
                if layer_id not in layers_dict:
                    layers_dict[layer_id] = nx.Graph() if not multilayer_network.directed else nx.DiGraph()
                layers_dict[layer_id].add_node(node[0])

        # Add edges to corresponding layers
        for u, v, data in multilayer_network.core_network.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
                # Only add intra-layer edges
                if u[1] == v[1]:
                    layer_id = u[1]
                    layers_dict[layer_id].add_edge(u[0], v[0], **data)
    else:
        raise VisualizationError(
            "Multilayer network must have a core_network attribute. "
            "Please ensure the network is properly constructed."
        )

    if not layers_dict:
        raise VisualizationError(
            "No layers found in the multilayer network. "
            "Please ensure the network contains at least one layer."
        )

    layer_names = sorted(layers_dict.keys())
    num_layers = len(layer_names)

    # Calculate grid dimensions
    num_cols = min(max_cols, num_layers)
    num_rows = (num_layers + num_cols - 1) // num_cols

    # Create figure with improved aesthetics
    if figsize is None:
        figsize = (5 * num_cols, 4 * num_rows)
    fig, axes = plt.subplots(num_rows, num_cols, figsize=figsize,
                             facecolor='white')
    fig.patch.set_facecolor('white')

    if num_layers == 1:
        axes = np.array([axes])
    axes = axes.flatten() if num_layers > 1 else axes

    # Use a professional color palette
    try:
        color_palette = plt.colormaps.get_cmap('Set2')
    except (AttributeError, KeyError):
        try:
            import matplotlib.cm as cm
            color_palette = cm.get_cmap('Set2')
        except:
            color_palette = None

    # Compute shared layout if requested
    if shared_layout:
        # Create union graph of all layers
        union_graph = nx.Graph()
        for layer_graph in layers_dict.values():
            union_graph.add_nodes_from(layer_graph.nodes())
            union_graph.add_edges_from(layer_graph.edges())

        # Compute layout on union graph with better parameters
        if layout == "spring":
            pos = nx.spring_layout(union_graph, k=0.5, iterations=50)
        elif layout == "circular":
            pos = nx.circular_layout(union_graph)
        elif layout == "random":
            pos = nx.random_layout(union_graph, seed=42)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(union_graph)
        else:
            pos = nx.spring_layout(union_graph, k=0.5, iterations=50)

    # Draw each layer with improved aesthetics
    for idx, layer_name in enumerate(layer_names):
        ax = axes[idx]
        layer_graph = layers_dict[layer_name]

        # Set subplot background
        ax.set_facecolor('#f8f9fa')

        # Compute per-layer layout if not shared
        if not shared_layout:
            if layout == "spring":
                pos = nx.spring_layout(layer_graph, k=0.5, iterations=50)
            elif layout == "circular":
                pos = nx.circular_layout(layer_graph)
            elif layout == "random":
                pos = nx.random_layout(layer_graph, seed=42)
            elif layout == "kamada_kawai":
                pos = nx.kamada_kawai_layout(layer_graph)
            else:
                pos = nx.spring_layout(layer_graph, k=0.5, iterations=50)

        # Get color for this layer
        if color_palette:
            layer_color = color_palette(idx / max(num_layers - 1, 1))
        else:
            layer_color = colors.colors_default[idx % len(colors.colors_default)]

        # Draw edges with better styling
        nx.draw_networkx_edges(
            layer_graph,
            pos=pos,
            ax=ax,
            edge_color='#666666',
            width=1.5,
            alpha=0.6,
            style='solid'
        )

        # Draw nodes with better styling
        nx.draw_networkx_nodes(
            layer_graph,
            pos=pos,
            ax=ax,
            node_size=node_size,
            node_color=[layer_color],
            edgecolors='white',
            linewidths=2,
            alpha=0.9
        )

        # Draw labels if requested
        if kwargs.get('with_labels', False):
            nx.draw_networkx_labels(
                layer_graph,
                pos=pos,
                ax=ax,
                font_size=8,
                font_weight='bold',
                font_color='#2c3e50'
            )

        # Add title with improved styling
        if show_layer_titles:
            ax.set_title(f"Layer {layer_name}",
                        fontsize=12,
                        fontweight='bold',
                        pad=10,
                        color='#2c3e50')

        ax.axis('off')

    # Hide unused subplots
    for idx in range(num_layers, len(axes)):
        axes[idx].axis('off')
        axes[idx].set_facecolor('white')

    plt.tight_layout(pad=2.0)
    return fig


def plot_edge_colored_projection(
    multilayer_network,
    layout: str = "spring",
    node_size: int = 50,
    layer_colors: Optional[Dict[Any, str]] = None,
    aggregate_multilayer_edges: bool = True,
    figsize: Tuple[float, float] = (12, 9),
    edge_alpha: float = 0.7,
    **kwargs
):
    """Create an aggregated projection where edge colors indicate layer membership.

    This visualization projects all layers onto a single 2D graph, using edge colors
    to distinguish which layer each edge belongs to. Useful for seeing the overall
    structure while maintaining layer information.

    Args:
        multilayer_network: A MultiLayerNetwork instance
        layout: Layout algorithm to use ("spring", "circular", "random", "kamada_kawai")
        node_size: Size of nodes
        layer_colors: Optional dict mapping layer names to colors; if None, auto-generated
        aggregate_multilayer_edges: If True, show edges from all layers with distinct colors
        figsize: Figure size as (width, height) tuple
        edge_alpha: Transparency level for edges (0-1)
        **kwargs: Additional arguments for customization

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Extract layers and build aggregated graph
    layers_dict = {}
    aggregated_graph = nx.Graph()

    if hasattr(multilayer_network, 'core_network') and multilayer_network.core_network is not None:
        # Extract nodes and edges per layer
        for node in multilayer_network.core_network.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                layer_id = node[1]
                if layer_id not in layers_dict:
                    layers_dict[layer_id] = []
                aggregated_graph.add_node(node[0])

        # Collect edges by layer
        for u, v, data in multilayer_network.core_network.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
                if u[1] == v[1]:  # Intra-layer edge
                    layer_id = u[1]
                    if layer_id not in layers_dict:
                        layers_dict[layer_id] = []
                    layers_dict[layer_id].append((u[0], v[0], data))
                    aggregated_graph.add_edge(u[0], v[0])
    else:
        raise VisualizationError(
            "Multilayer network must have a core_network attribute. "
            "Please ensure the network is properly constructed."
        )

    if not layers_dict:
        raise VisualizationError(
            "No layers found in the multilayer network. "
            "Please ensure the network contains at least one layer."
        )

    # Generate professional color palette if not provided
    layer_names = sorted(layers_dict.keys())
    if layer_colors is None:
        try:
            cmap = plt.colormaps.get_cmap('tab10')
        except (AttributeError, KeyError):
            try:
                import matplotlib.cm as cm
                cmap = cm.get_cmap('tab10')
            except:
                cmap = None

        if cmap:
            layer_colors = {}
            for idx, layer_name in enumerate(layer_names):
                layer_colors[layer_name] = cmap(idx / max(len(layer_names) - 1, 1))
        else:
            layer_colors = {}
            for idx, layer_name in enumerate(layer_names):
                layer_colors[layer_name] = colors.colors_default[idx % len(colors.colors_default)]

    # Compute layout on aggregated graph with better parameters
    if layout == "spring":
        pos = nx.spring_layout(aggregated_graph, k=0.5, iterations=50)
    elif layout == "circular":
        pos = nx.circular_layout(aggregated_graph)
    elif layout == "random":
        pos = nx.random_layout(aggregated_graph, seed=42)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(aggregated_graph)
    else:
        pos = nx.spring_layout(aggregated_graph, k=0.5, iterations=50)

    # Create figure with improved styling
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')

    # Draw edges per layer with improved styling and proper ordering
    for idx, layer_name in enumerate(layer_names):
        edge_list = [(u, v) for u, v, _ in layers_dict[layer_name]]
        if edge_list:
            nx.draw_networkx_edges(
                aggregated_graph,
                pos,
                edgelist=edge_list,
                edge_color=layer_colors[layer_name],
                alpha=edge_alpha,
                width=2.5,
                ax=ax,
                label=f"Layer {layer_name}"
            )

    # Draw nodes with improved styling
    nx.draw_networkx_nodes(
        aggregated_graph,
        pos,
        node_size=node_size * 2,
        node_color='#ffffff',
        edgecolors='#2c3e50',
        linewidths=2,
        alpha=0.95,
        ax=ax
    )

    # Add labels if requested
    if kwargs.get('with_labels', False):
        nx.draw_networkx_labels(
            aggregated_graph,
            pos,
            ax=ax,
            font_size=9,
            font_weight='bold',
            font_color='#2c3e50'
        )

    # Add professional legend
    legend = ax.legend(
        loc='upper right',
        frameon=True,
        fancybox=True,
        shadow=True,
        fontsize=10,
        title='Network Layers',
        title_fontsize=11
    )
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_alpha(0.95)
    legend.get_frame().set_edgecolor('#cccccc')

    # Add title with improved styling
    ax.set_title(
        "Multilayer Network Projection",
        fontsize=14,
        fontweight='bold',
        pad=20,
        color='#2c3e50'
    )
    ax.axis('off')

    plt.tight_layout()
    return fig
    # Draw nodes once
    nx.draw_networkx_nodes(
        aggregated_graph,
        pos,
        node_size=node_size,
        node_color=kwargs.get('node_color', 'lightblue'),
        ax=ax
    )

    # Draw edges per layer with different colors
    for layer_name in layer_names:
        edge_list = [(u, v) for u, v, _ in layers_dict[layer_name]]
        if edge_list:
            nx.draw_networkx_edges(
                aggregated_graph,
                pos,
                edgelist=edge_list,
                edge_color=layer_colors[layer_name],
                alpha=edge_alpha,
                width=2,
                ax=ax,
                label=f"Layer {layer_name}"
            )

    # Add labels if requested
    if kwargs.get('with_labels', False):
        nx.draw_networkx_labels(aggregated_graph, pos, ax=ax)

    # Add legend
    ax.legend(loc='best')
    ax.set_title("Edge-Colored Multilayer Projection")
    ax.axis('off')

    plt.tight_layout()
    return fig


def plot_supra_adjacency_heatmap(
    multilayer_network,
    include_inter_layer: bool = False,
    inter_layer_weight: float = 1.0,
    node_order: Optional[List[Any]] = None,
    cmap: str = "viridis",
    figsize: Tuple[float, float] = (10, 10),
    **kwargs
):
    """Create a supra-adjacency matrix heatmap visualization.

    This visualization shows the multilayer network as a block matrix where each
    block represents the adjacency matrix of one layer. Optionally includes
    inter-layer connections.

    Args:
        multilayer_network: A MultiLayerNetwork instance
        include_inter_layer: If True, include inter-layer edges/couplings
        inter_layer_weight: Default weight for inter-layer connections
        node_order: Optional list specifying node ordering; if None, uses sorted order
        cmap: Colormap name for the heatmap
        figsize: Figure size as (width, height) tuple
        **kwargs: Additional arguments for imshow

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Extract layer structure
    layers_dict = {}
    nodes_per_layer = {}

    if hasattr(multilayer_network, 'core_network') and multilayer_network.core_network is not None:
        # Collect nodes per layer
        for node in multilayer_network.core_network.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                node_id, layer_id = node[0], node[1]
                if layer_id not in nodes_per_layer:
                    nodes_per_layer[layer_id] = set()
                nodes_per_layer[layer_id].add(node_id)

        # Build adjacency info per layer
        for layer_id in nodes_per_layer:
            layers_dict[layer_id] = {}

        for u, v, data in multilayer_network.core_network.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
                u_node, u_layer = u[0], u[1]
                v_node, v_layer = v[0], v[1]
                weight = data.get('weight', 1.0)

                if u_layer == v_layer:  # Intra-layer
                    if (u_node, v_node) not in layers_dict[u_layer]:
                        layers_dict[u_layer][(u_node, v_node)] = 0
                    layers_dict[u_layer][(u_node, v_node)] += weight
                elif include_inter_layer:  # Inter-layer
                    # Store inter-layer edges separately
                    pass
    else:
        raise VisualizationError(
            "Multilayer network must have a core_network attribute. "
            "Please ensure the network is properly constructed."
        )

    if not layers_dict:
        raise VisualizationError(
            "No layers found in the multilayer network. "
            "Please ensure the network contains at least one layer."
        )

    # Determine global node ordering
    all_nodes = set()
    for nodes in nodes_per_layer.values():
        all_nodes.update(nodes)

    if node_order is None:
        node_order = sorted(all_nodes)

    node_to_idx = {node: idx for idx, node in enumerate(node_order)}
    n_nodes = len(node_order)

    # Build supra-adjacency matrix
    layer_names = sorted(layers_dict.keys())
    n_layers = len(layer_names)
    supra_size = n_nodes * n_layers
    supra_matrix = np.zeros((supra_size, supra_size))

    # Fill in layer blocks
    for layer_idx, layer_name in enumerate(layer_names):
        offset = layer_idx * n_nodes
        for (u, v), weight in layers_dict[layer_name].items():
            if u in node_to_idx and v in node_to_idx:
                i, j = node_to_idx[u], node_to_idx[v]
                supra_matrix[offset + i, offset + j] = weight
                if not multilayer_network.directed:
                    supra_matrix[offset + j, offset + i] = weight

    # Add inter-layer connections if requested
    if include_inter_layer:
        for layer_idx in range(n_layers - 1):
            offset1 = layer_idx * n_nodes
            offset2 = (layer_idx + 1) * n_nodes
            # Add diagonal coupling for nodes that exist in both layers
            layer1_nodes = nodes_per_layer[layer_names[layer_idx]]
            layer2_nodes = nodes_per_layer[layer_names[layer_idx + 1]]
            common_nodes = layer1_nodes.intersection(layer2_nodes)
            for node in common_nodes:
                if node in node_to_idx:
                    i = node_to_idx[node]
                    supra_matrix[offset1 + i, offset2 + i] = inter_layer_weight
                    supra_matrix[offset2 + i, offset1 + i] = inter_layer_weight

    # Create visualization with improved aesthetics
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    fig.patch.set_facecolor('white')

    # Use a better colormap for heatmaps
    im = ax.imshow(supra_matrix, cmap=cmap, interpolation='nearest',
                   aspect='auto', **kwargs)

    # Add grid lines to show block boundaries with improved styling
    for i in range(1, n_layers):
        ax.axhline(y=i * n_nodes - 0.5, color='#ffffff', linewidth=3, alpha=0.9)
        ax.axvline(x=i * n_nodes - 0.5, color='#ffffff', linewidth=3, alpha=0.9)

    # Add layer labels with improved styling
    for layer_idx, layer_name in enumerate(layer_names):
        pos = layer_idx * n_nodes + n_nodes / 2
        ax.text(-n_nodes * 0.08, pos, f"Layer {layer_name}",
                ha='right', va='center', fontsize=11,
                fontweight='bold', color='#2c3e50')
        ax.text(pos, -n_nodes * 0.08, f"Layer {layer_name}",
                ha='center', va='bottom', fontsize=11,
                fontweight='bold', color='#2c3e50', rotation=0)

    # Add title with improved styling
    ax.set_title("Supra-Adjacency Matrix Heatmap",
                fontsize=14, fontweight='bold', pad=20, color='#2c3e50')

    # Add colorbar with improved styling
    cbar = plt.colorbar(im, ax=ax, label="Edge Weight", fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=10)
    cbar.set_label("Edge Weight", size=11, weight='bold')

    plt.tight_layout()
    return fig


def plot_radial_layers(
    multilayer_network,
    base_radius: float = 1.0,
    radius_step: float = 1.0,
    node_size: int = 500,
    draw_inter_layer_edges: bool = True,
    figsize: Tuple[float, float] = (12, 12),
    edge_alpha: float = 0.5,
    draw_layer_bands: bool = True,
    band_alpha: float = 0.25,
    **kwargs
):
    """Create a radial/concentric visualization with layers as rings.

    This visualization arranges layers as concentric circles, with nodes positioned
    on rings based on their layer. Inter-layer edges appear as radial connections.

    Args:
        multilayer_network: A MultiLayerNetwork instance
        base_radius: Radius of the innermost layer
        radius_step: Distance between consecutive layer rings
        node_size: Size of nodes (default: 500 for better visibility)
        draw_inter_layer_edges: If True, draw edges between layers
        figsize: Figure size as (width, height) tuple
        edge_alpha: Transparency for edges
        draw_layer_bands: If True, draw semi-transparent circular bands around layers
        band_alpha: Transparency for layer bands (default: 0.25)
        **kwargs: Additional drawing parameters

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Extract layer structure
    layers_dict = {}
    nodes_per_layer = {}
    inter_layer_edges = []

    if hasattr(multilayer_network, 'core_network') and multilayer_network.core_network is not None:
        # Collect nodes per layer
        for node in multilayer_network.core_network.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                node_id, layer_id = node[0], node[1]
                if layer_id not in nodes_per_layer:
                    nodes_per_layer[layer_id] = []
                if node_id not in nodes_per_layer[layer_id]:
                    nodes_per_layer[layer_id].append(node_id)

        # Collect edges
        for layer_id in nodes_per_layer:
            layers_dict[layer_id] = []

        for u, v, data in multilayer_network.core_network.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
                if u[1] == v[1]:  # Intra-layer
                    layers_dict[u[1]].append((u[0], v[0]))
                else:  # Inter-layer
                    inter_layer_edges.append((u, v))
    else:
        raise VisualizationError(
            "Multilayer network must have a core_network attribute. "
            "Please ensure the network is properly constructed."
        )

    if not layers_dict:
        raise VisualizationError(
            "No layers found in the multilayer network. "
            "Please ensure the network contains at least one layer."
        )

    # Assign global angles to nodes
    all_nodes = set()
    for nodes in nodes_per_layer.values():
        all_nodes.update(nodes)
    all_nodes = sorted(all_nodes)

    node_angles = {}
    for idx, node in enumerate(all_nodes):
        node_angles[node] = 2 * np.pi * idx / len(all_nodes)

    # Create positions for nodes
    layer_names = sorted(layers_dict.keys())
    positions = {}

    for layer_idx, layer_name in enumerate(layer_names):
        radius = base_radius + layer_idx * radius_step
        for node in nodes_per_layer[layer_name]:
            angle = node_angles[node]
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            positions[(node, layer_name)] = (x, y)

    # Create figure with improved aesthetics
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#f8f9fa')

    # Use professional color palette with improved color handling
    try:
        color_palette = plt.colormaps.get_cmap('Set2')
    except (AttributeError, KeyError):
        try:
            import matplotlib.cm as cm
            color_palette = cm.get_cmap('Set2')
        except:
            color_palette = None

    # Draw semi-transparent circular bands around each layer for visual grouping
    if draw_layer_bands and MATPLOTLIB_PATCHES_AVAILABLE:
        for layer_idx, layer_name in enumerate(layer_names):
            radius = base_radius + layer_idx * radius_step
            band_width = radius_step * 0.6  # Band extends ±60% of step for better visibility

            if color_palette:
                layer_color = color_palette(layer_idx / max(len(layer_names) - 1, 1))
            else:
                layer_color = colors.colors_default[layer_idx % len(colors.colors_default)]

            # Create a circular band around this layer
            circle = Circle((0, 0), radius + band_width,
                          fill=True, facecolor=layer_color,
                          edgecolor='none', alpha=band_alpha, zorder=0)
            ax.add_patch(circle)

            # Add inner circle to create ring effect
            if radius > band_width:
                inner_circle = Circle((0, 0), radius - band_width,
                                    fill=True, facecolor=ax.get_facecolor(),
                                    edgecolor='none', zorder=0.5)
                ax.add_patch(inner_circle)


    # Draw intra-layer edges with improved styling
    for layer_idx, layer_name in enumerate(layer_names):
        edge_list = layers_dict[layer_name]
        if color_palette:
            layer_color = color_palette(layer_idx / max(len(layer_names) - 1, 1))
        else:
            layer_color = colors.colors_default[layer_idx % len(colors.colors_default)]

        for u, v in edge_list:
            if (u, layer_name) in positions and (v, layer_name) in positions:
                x_coords = [positions[(u, layer_name)][0], positions[(v, layer_name)][0]]
                y_coords = [positions[(u, layer_name)][1], positions[(v, layer_name)][1]]
                ax.plot(x_coords, y_coords, color=layer_color,
                       alpha=edge_alpha, linewidth=2.5, zorder=1)

    # Draw inter-layer edges if requested with improved styling
    if draw_inter_layer_edges:
        for u, v in inter_layer_edges:
            if u in positions and v in positions:
                x_coords = [positions[u][0], positions[v][0]]
                y_coords = [positions[u][1], positions[v][1]]
                ax.plot(x_coords, y_coords, color='#95a5a6',
                       alpha=edge_alpha * 0.4, linewidth=1,
                       linestyle='--', zorder=0)

    # Draw nodes with improved styling and bigger sizes
    for layer_idx, layer_name in enumerate(layer_names):
        if color_palette:
            layer_color = color_palette(layer_idx / max(len(layer_names) - 1, 1))
        else:
            layer_color = colors.colors_default[layer_idx % len(colors.colors_default)]

        for node in nodes_per_layer[layer_name]:
            if (node, layer_name) in positions:
                x, y = positions[(node, layer_name)]
                # Draw node with white border for better visibility
                ax.scatter(x, y, s=node_size, c=[layer_color],
                          alpha=0.9, edgecolors='white',
                          linewidths=3, zorder=3)

    # Add layer labels with improved styling
    for layer_idx, layer_name in enumerate(layer_names):
        radius = base_radius + layer_idx * radius_step
        ax.text(0, radius + 0.5, f"Layer {layer_name}",
               ha='center', va='bottom', fontsize=12,
               weight='bold', color='#2c3e50',
               bbox=dict(boxstyle='round,pad=0.6',
                        facecolor='white',
                        edgecolor='#bdc3c7',
                        alpha=0.95,
                        linewidth=1.5))

    # Add title with improved styling
    ax.set_title("Radial Multilayer Network",
                fontsize=16, fontweight='bold',
                pad=20, color='#2c3e50')

    ax.set_aspect('equal')
    ax.axis('off')

    plt.tight_layout()
    return fig


def plot_ego_multilayer(
    multilayer_network,
    ego,
    layers: Optional[List[Any]] = None,
    max_depth: int = 1,
    layout: str = "spring",
    figsize: Optional[Tuple[float, float]] = None,
    max_cols: int = 3,
    node_size: int = 500,
    ego_node_size: int = 1200,
    **kwargs
):
    """Create an ego-centric multilayer visualization.

    This visualization focuses on a single node (ego) and shows its neighborhood
    across different layers, highlighting the ego node's position in each layer.

    Args:
        multilayer_network: A MultiLayerNetwork instance
        ego: The ego node to focus on
        layers: Optional list of specific layers to visualize; if None, uses all layers
        max_depth: Maximum depth of neighborhood to include (number of hops)
        layout: Layout algorithm for each ego graph
        figsize: Optional figure size; if None, auto-calculated
        max_cols: Maximum columns in subplot grid
        node_size: Size of regular nodes
        ego_node_size: Size of the ego node (highlighted)
        **kwargs: Additional drawing parameters

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Extract layers
    layers_dict = {}

    if hasattr(multilayer_network, 'core_network') and multilayer_network.core_network is not None:
        # Find all layers containing the ego node or extract all layers if layers is None
        ego_layers = set()
        for node in multilayer_network.core_network.nodes():
            if isinstance(node, tuple) and len(node) >= 2:
                node_id, layer_id = node[0], node[1]
                if layers is None or layer_id in layers:
                    if layer_id not in layers_dict:
                        layers_dict[layer_id] = nx.Graph() if not multilayer_network.directed else nx.DiGraph()
                    layers_dict[layer_id].add_node(node_id)
                    if node_id == ego:
                        ego_layers.add(layer_id)

        # Add edges
        for u, v, data in multilayer_network.core_network.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
                if u[1] == v[1] and (layers is None or u[1] in layers):
                    layers_dict[u[1]].add_edge(u[0], v[0], **data)
    else:
        raise VisualizationError(
            "Multilayer network must have a core_network attribute. "
            "Please ensure the network is properly constructed."
        )

    if not layers_dict:
        raise VisualizationError(
            "No layers found in the specified multilayer network. "
            "Please ensure the network contains at least one layer."
        )

    # Extract ego graphs for each layer
    layer_names = sorted(layers_dict.keys())
    ego_graphs = {}

    for layer_name in layer_names:
        layer_graph = layers_dict[layer_name]
        if ego in layer_graph:
            # Extract ego graph up to max_depth hops
            ego_graphs[layer_name] = nx.ego_graph(layer_graph, ego, radius=max_depth)

    if not ego_graphs:
        raise ValueError(f"Ego node '{ego}' not found in any layer")

    num_layers = len(ego_graphs)
    num_cols = min(max_cols, num_layers)
    num_rows = (num_layers + num_cols - 1) // num_cols

    if figsize is None:
        figsize = (5 * num_cols, 4 * num_rows)

    # Create figure with improved aesthetics
    fig, axes = plt.subplots(num_rows, num_cols, figsize=figsize, facecolor='white')
    fig.patch.set_facecolor('white')

    if num_layers == 1:
        axes = np.array([axes])
    axes = axes.flatten() if num_layers > 1 else axes

    # Use professional color for ego node
    ego_color = '#e74c3c'  # Professional red
    neighbor_color = '#3498db'  # Professional blue

    # Draw each ego graph with improved aesthetics
    for idx, layer_name in enumerate(sorted(ego_graphs.keys())):
        ax = axes[idx]
        ax.set_facecolor('#f8f9fa')
        ego_graph = ego_graphs[layer_name]

        # Compute layout with better parameters
        if layout == "spring":
            pos = nx.spring_layout(ego_graph, k=1.2, iterations=100, seed=42)
        elif layout == "circular":
            # For circular layout, position ego at center and neighbors in a circle
            if len(ego_graph.nodes()) > 1:
                pos = {}
                neighbors = [n for n in ego_graph.nodes() if n != ego]
                # Place ego at center
                pos[ego] = np.array([0.5, 0.5])
                # Place neighbors in circle around ego
                n_neighbors = len(neighbors)
                radius = 0.35  # Circle radius
                for i, node in enumerate(neighbors):
                    angle = 2 * np.pi * i / n_neighbors
                    pos[node] = np.array([
                        0.5 + radius * np.cos(angle),
                        0.5 + radius * np.sin(angle)
                    ])
            else:
                pos = {ego: np.array([0.5, 0.5])}
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(ego_graph)
        else:
            pos = nx.spring_layout(ego_graph, k=1.2, iterations=100, seed=42)

        # Draw edges with improved styling
        nx.draw_networkx_edges(
            ego_graph, pos, ax=ax,
            alpha=0.4, width=3,
            edge_color='#34495e'
        )

        # Draw regular nodes with improved styling
        non_ego_nodes = [n for n in ego_graph.nodes() if n != ego]
        if non_ego_nodes:
            nx.draw_networkx_nodes(
                ego_graph, pos, nodelist=non_ego_nodes,
                node_size=node_size, node_color=neighbor_color,
                edgecolors='white', linewidths=3,
                alpha=0.95, ax=ax
            )

        # Draw ego node with emphasis and improved styling
        nx.draw_networkx_nodes(
            ego_graph, pos, nodelist=[ego],
            node_size=ego_node_size, node_color=ego_color,
            edgecolors='white', linewidths=4,
            alpha=1.0, ax=ax
        )

        # Add labels if requested with improved styling
        if kwargs.get('with_labels', True):
            # Label ego node specially
            nx.draw_networkx_labels(
                ego_graph, pos,
                labels={ego: str(ego)},
                ax=ax, font_size=14,
                font_weight='bold',
                font_color='white'
            )
            # Label other nodes
            other_labels = {n: str(n) for n in non_ego_nodes}
            if other_labels:
                nx.draw_networkx_labels(
                    ego_graph, pos,
                    labels=other_labels,
                    ax=ax, font_size=11,
                    font_weight='bold',
                    font_color='white'
                )

        # Add title with improved styling
        ax.set_title(f"Layer {layer_name}\nEgo Node: {ego}",
                    fontsize=14, fontweight='bold',
                    pad=15, color='#2c3e50')
        ax.axis('off')

    # Hide unused subplots
    for idx in range(num_layers, len(axes)):
        axes[idx].axis('off')
        axes[idx].set_facecolor('white')

    # Add overall title
    fig.suptitle(f"Ego-Centric Network View ({max_depth}-hop neighborhood)",
                fontsize=16, fontweight='bold', y=0.98, color='#2c3e50')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


def draw_multilayer_flow(
    graphs: List[nx.Graph],
    multilinks: Dict[str, List[Tuple]],
    labels: Optional[List[str]] = None,
    node_activity: Optional[Dict[Any, float]] = None,
    ax: Optional[Any] = None,
    display: bool = True,
    layer_gap: float = 3.0,
    node_size: float = 30,
    node_cmap: str = "viridis",
    flow_alpha: float = 0.3,
    flow_min_width: float = 0.2,
    flow_max_width: float = 4.0,
    aggregate_by: Tuple[str, ...] = ("u", "v", "layer_u", "layer_v"),
    **kwargs
) -> Any:
    """Draw multilayer network as layered flow visualization (alluvial-style).

    Shows each layer as a horizontal band with nodes positioned along the x-axis.
    Intra-layer activity is encoded as node color/size, and inter-layer edges are
    shown as thick flow ribbons (Bezier curves) where width encodes edge weight.

    Args:
        graphs: List of NetworkX graphs, one per layer (from multi_layer_network.get_layers())
        multilinks: Dictionary mapping edge_type -> list of multi-layer edges
        labels: Optional list of layer labels. If None, uses layer indices
        node_activity: Optional dict mapping node_id -> activity value.
            If None, computes intra-layer degree
        ax: Matplotlib axes to draw on. If None, creates new figure
        display: If True, calls plt.show() at the end
        layer_gap: Vertical distance between layer bands
        node_size: Base marker size for nodes
        node_cmap: Matplotlib colormap name for node activity coloring
        flow_alpha: Base transparency for flow ribbons
        flow_min_width: Minimum line width for flows
        flow_max_width: Maximum line width for flows
        aggregate_by: Tuple of keys for aggregating flows (currently not used, for future extension)
        **kwargs: Reserved for future extensions

    Returns:
        Matplotlib axes object

    Examples:
        >>> network = multi_layer_network()
        >>> network.load_network("data.txt", input_type="multiedgelist")
        >>> labels, graphs, multilinks = network.get_layers()
        >>> draw_multilayer_flow(graphs, multilinks, labels=labels)
    """
    # Get or create axes
    if ax is None:
        _fig, ax = plt.subplots(figsize=(12, 8))

    n_layers = len(graphs)
    if n_layers == 0:
        logger.warning("No layers to visualize")
        return ax

    # Determine layer y-positions
    y_positions = {layer_idx: layer_idx * layer_gap for layer_idx in range(n_layers)}

    # Build node positions and compute activity per layer
    node_positions = {}  # (layer_idx, node_id) -> (x, y)
    node_activities = {}  # (layer_idx, node_id) -> activity_value

    for layer_idx, graph in enumerate(graphs):
        nodes = list(graph.nodes())
        if len(nodes) == 0:
            continue

        # Compute or get activity values for this layer
        layer_activities = {}
        for node in nodes:
            if node_activity is not None and node in node_activity:
                activity = node_activity[node]
            else:
                # Default: use degree (with weight if available)
                if graph.has_node(node):
                    activity = graph.degree(node, weight="weight")
                else:
                    activity = 0
            layer_activities[node] = activity

        # Sort nodes by activity (descending) for better visual layout
        sorted_nodes = sorted(layer_activities.keys(),
                            key=lambda n: layer_activities[n],
                            reverse=True)

        # Assign x positions (evenly spaced)
        y_layer = y_positions[layer_idx]
        for x_idx, node in enumerate(sorted_nodes):
            x_pos = x_idx
            node_positions[(layer_idx, node)] = (x_pos, y_layer)
            node_activities[(layer_idx, node)] = layer_activities[node]

    # Normalize activities per layer for color mapping
    try:
        # Modern matplotlib API (>= 3.7)
        import matplotlib
        cmap = matplotlib.colormaps.get_cmap(node_cmap)
    except AttributeError:
        # Fallback for older matplotlib versions
        cmap = plt.cm.get_cmap(node_cmap)

    for layer_idx in range(n_layers):
        layer_acts = [node_activities.get((layer_idx, node), 0)
                     for node in graphs[layer_idx].nodes()]
        if len(layer_acts) > 0 and max(layer_acts) > 0:
            # Normalize to [0, 1]
            min_act = min(layer_acts)
            max_act = max(layer_acts)
            if max_act > min_act:
                for node in graphs[layer_idx].nodes():
                    key = (layer_idx, node)
                    if key in node_activities:
                        old_val = node_activities[key]
                        node_activities[key] = (old_val - min_act) / (max_act - min_act)

    # Plot nodes with activity-based coloring and sizing
    for layer_idx, graph in enumerate(graphs):
        nodes = list(graph.nodes())
        if len(nodes) == 0:
            continue

        xs = []
        ys = []
        colors_list = []
        sizes = []
        node_list = []  # Keep track of node objects for labeling

        for node in nodes:
            key = (layer_idx, node)
            if key in node_positions:
                x, y = node_positions[key]
                xs.append(x)
                ys.append(y)
                node_list.append(node)

                activity_norm = node_activities.get(key, 0)
                colors_list.append(cmap(activity_norm))

                # Scale size by activity
                size = node_size * (0.5 + activity_norm)
                sizes.append(size)

        if len(xs) > 0:
            ax.scatter(xs, ys, s=sizes, c=colors_list,
                      edgecolors='white', linewidths=1,
                      alpha=0.9, zorder=3)

            # Add node labels next to each node
            for x, y, node in zip(xs, ys, node_list):
                ax.text(x + 0.15, y, str(node),
                       fontsize=8,
                       ha='left', va='center',
                       color='#333333',
                       zorder=4)

    # Draw layer labels
    if labels is not None:
        for layer_idx in range(n_layers):
            y_layer = y_positions[layer_idx]
            label_text = labels[layer_idx] if layer_idx < len(labels) else f"Layer {layer_idx}"
            ax.text(-1, y_layer, label_text,
                   ha='right', va='center',
                   fontsize=10, fontweight='bold')

    # Aggregate inter-layer flows
    # Build flow aggregation: (layer_u, node_u, layer_v, node_v) -> weight
    flow_weights = {}

    # Build a mapping from node_id to list of layers it appears in
    node_to_layers = {}
    for layer_idx, graph in enumerate(graphs):
        for node in graph.nodes():
            if node not in node_to_layers:
                node_to_layers[node] = []
            node_to_layers[node].append(layer_idx)

    # Process multilinks - these represent inter-layer connections
    # The edges in multilinks connect nodes that may exist in different layers
    for edge_type, edges in multilinks.items():
        for edge in edges:
            # Edges from multilinks are typically tuples like (node_u, node_v)
            if len(edge) >= 2:
                node_u = edge[0]
                node_v = edge[1]

                # Get all layer combinations where these nodes appear
                layers_u = node_to_layers.get(node_u, [])
                layers_v = node_to_layers.get(node_v, [])

                # Check if nodes are in different layers (inter-layer edge)
                # In typical multilayer networks, if node_u and node_v are the same node ID
                # appearing in different layers, this is an inter-layer coupling
                for layer_u in layers_u:
                    for layer_v in layers_v:
                        if layer_u != layer_v:
                            flow_key = (layer_u, node_u, layer_v, node_v)
                            flow_weights[flow_key] = flow_weights.get(flow_key, 0) + 1

    # Draw flows as Bezier curves
    if len(flow_weights) > 0:
        # Normalize flow weights to line widths
        min_weight = min(flow_weights.values())
        max_weight = max(flow_weights.values())

        for flow_key, weight in flow_weights.items():
            layer_u, node_u, layer_v, node_v = flow_key

            # Get positions
            pos_u = node_positions.get((layer_u, node_u))
            pos_v = node_positions.get((layer_v, node_v))

            if pos_u is not None and pos_v is not None:
                x_u, y_u = pos_u
                x_v, y_v = pos_v

                # Normalize weight to linewidth
                if max_weight > min_weight:
                    norm_weight = (weight - min_weight) / (max_weight - min_weight)
                else:
                    norm_weight = 1.0
                linewidth = flow_min_width + norm_weight * (flow_max_width - flow_min_width)

                # Draw Bezier curve
                try:
                    p1 = [x_u, x_v]
                    p2 = [y_u, y_v]

                    # Calculate appropriate curve height based on layer distance
                    layer_distance = abs(y_v - y_u)
                    # Use smaller curve height to prevent excessive overlap
                    curve_height = min(0.5, layer_distance * 0.3)

                    x_curve, y_curve = bezier.draw_bezier(
                        n_layers,
                        p1,
                        p2,
                        path_height=curve_height,
                        inversion=False,
                        linemode="both",
                        resolution=0.01
                    )

                    ax.plot(x_curve, y_curve,
                           color='gray',
                           alpha=flow_alpha,
                           linewidth=linewidth,
                           zorder=1)
                except Exception as e:
                    logger.debug(f"Could not draw flow between {node_u} and {node_v}: {e}")

    # Cosmetics
    ax.set_axis_off()

    # Add some padding
    ax.margins(0.1)

    if display:
        plt.show()

    return ax


if __name__ == "__main__":

    x = generate_random_networks(4)
    draw_multilayer_default(x, display=False, background_shape="circle")
    # generate_random_multiedges(x, 12, style="piramidal")
    generate_random_multiedges(x, 12, style="curve2_bezier")
    # network 1's 4 to network 6's 3 etc..
    # draw_multiedges(x,mel,input_type="tuple")

    plt.show()
