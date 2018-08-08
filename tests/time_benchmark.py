from pymnet import *
from py3plex.visualization.multilayer import *
from py3plex.visualization.colors import all_color_names,colors_default
from py3plex.core import multinet
import time

def py3plex_visualization(network):

    start = time.time()
    multilayer_network = multinet.multi_layer_network().load_network("../datasets/epigenetics.gpickle",directed=False, input_type="gpickle_biomine")
    network_labels, graphs, multilinks = multilayer_network.get_layers() ## get layers for visualization
    draw_multilayer_default(graphs,display=False,background_shape="circle",labels=network_labels,layout_algorithm="force")

    enum = 1
    color_mappings = {idx : col for idx, col in enumerate(colors_default)}
    for edge_type,edges in multilinks.items():
        draw_multiedges(graphs,edges,alphachannel=0.2,linepoints="-.",linecolor="black",curve_height=5,linmod="upper",linewidth=0.4)
        enum+=1
        
    end = time.time()
    return (end - start)

def pymnet_visualization(network):
    start = time.time()    
    fig = draw(network)
    end = time.time()
    return (end - start)

if __name__ == "__main__":

    import numpy as np
    import itertools
    import pandas as pd
    
    number_of_nodes = [5,10,100,200,500,1000,5000,1000]
    number_of_edges = list(range(10))
    probabilities = np.arange(0,0.5,0.1).tolist()

    merged = [number_of_nodes,number_of_edges,probabilities]
    combinations = list(itertools.product(*merged))

    datapoints = []
    
    for combination in combinations:
        N,E,p = combination
        print("Evaluating {} {} {} setting.".format(N,E,p))
        
        net = models.er_multilayer(N,E,p)        
        t_pp = py3plex_visualization(net)
        t_pmn = pymnet_visualization(net)
        datapoints.append({"N":N,"E":E,"p":p,"Py3plex":t_pp,"Pymnet":t_pmn})

    result_frame = pd.DataFrame(datapoints)
    result_frame.to_csv("example_benchmark.csv")



