#### This is an example for the py3plex multiplex network visualization library
#### CUSTOM MULTIEDGE

import matplotlib.pyplot as plt
import networkx as nx
## REPRESENTATIVE py3plex usage example

from py3plex.multilayer import *

## read file from a simple edgelist
input_graph = nx.read_edgelist("testgraph/test.txt")

## generate arbitrary layout (can be done for individual networks also)
tmp_pos=nx.spring_layout(input_graph)
nx.set_node_attributes(input_graph,'pos',tmp_pos)

## generate some arbitrary networks from the parent network
subgraph1 = input_graph.subgraph(['n2','n4','n5','n6'])
subgraph2 = input_graph.subgraph(['n1','n3','n9'])
networks = [subgraph1,subgraph2]

## call first the multilayer method
draw_multilayer_default(networks,background_shape="circle",display=False,labels=['first network','second network'],networks_color="rainbow")

## assign some multiplex edges and draw them
multiplex_edges1 = [('n1','n4')]
draw_multiplex_default(networks,multiplex_edges1,alphachannel=0.2,linepoints="-.",linecolor="black",curve_height=2) ## curve height denotes how hight the maximal point in curve goes

multiplex_edges2 = [('n9','n5')]
draw_multiplex_default(networks,multiplex_edges2,alphachannel=0.5,linepoints="-",linecolor="orange")

## show the canvas
plt.show()
