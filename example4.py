## this example demonstrates two possible network plots



# this python code uses in house py3plex lib for complex network visualization

import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict
from py3plex.multilayer import *


def view_by_type(inputgraph,limit=False):

    input_graph = nx.read_gpickle(inputgraph)

    print(nx.info(input_graph))
    
    type_segments = defaultdict(list)
    
    for node in input_graph.nodes(data=True):
        type_segments[node[0].split("_")[0]].append(node[0])        
    
    networks = []
    labs = []
    
    for k,v in type_segments.items():
        if limit != False:
            tmp_graph = input_graph.subgraph(v[0:limit]) 
        else:
            tmp_graph = input_graph.subgraph(v)
            
        labs.append(k)
        tmp_pos=nx.spring_layout(tmp_graph)
        nx.set_node_attributes(tmp_graph,'pos',tmp_pos)
        networks.append(tmp_graph)

    print ("Visualizing..")
    draw_multilayer_default(networks,background_shape="circle",display=False,labels=labs,networks_color="black")

    mx_edges = []

    for e in input_graph.edges():
        if e[0].split("_")[0] != e[1].split("_")[0]:

            ## we have a multiplex edge!
            layer1 = e[0].split("_")[0]
            layer2 = e[1].split("_")[0]            
            mx_edges.append((e[0],e[1]))
            
    
    draw_multiplex_default(networks,mx_edges,alphachannel=0.2,linepoints="-.",linecolor="black",curve_height=2,linmod="upper",linewidth=0.1)

    plt.show()
    
#view_by_type("testgraph/epigenetics.gpickle")

## plot using force directed layout


input_graph = nx.read_gpickle("testgraph/epigenetics.gpickle")

## node color setting:

ncols = [val[0].split("_")[0] for val in input_graph.nodes(data=True)]
uniqcols = set(ncols)
coldict = {}
for en,col in enumerate(uniqcols):
    coldict[col] = en
node_cols = [coldict[val] for val in ncols]
nx.draw_spring(input_graph,node_color=node_cols,node_size=1,alpha=0.5)
plt.show()
