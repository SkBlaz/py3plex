### simple plot of a larger file
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names,colors_default
from py3plex.core import multinet

## string layout for larger network -----------------------------------
multilayer_network = multinet.multi_layer_network().load_network("../datasets/intact02.gpickle",input_type="gpickle",directed=False)

color_list = multilayer_network.monoplex_nx_wrapper("connected_components")
hairball_plot(multilayer_network.core_network,layout_parameters={"iterations": 300},color_list=color_list)
plt.show()
