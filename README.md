
#This is the py3plex, a lightweight multiplex network visualization library. It is caoable of visualizing complex networks in an intuitive manner.

Main goals of this library are:

> speed - heavy operations are vectorized using numpy
> simplicity - there are only two main functions which extend basic Networkx syntax
> elegance - all parameters can be tweaked an optimized for the best look
> modularity - this library is built from a programatic point of view, not a mathematical one. Basic structures revolve around list-like structures and not matrices.

```python

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
draw_multiplex_default(networks,multiplex_edges1,alphachannel=0.2,linepoints="-.")
multiplex_edges2 = [('n9','n5')]
draw_multiplex_default(networks,multiplex_edges2,alphachannel=0.5,linepoints="-",linecolor="orange")

## show the canvas
plt.show()



```

##Another simple example, this time using randomly generated networks

```{python}

from py3plex.multilayer import *

x = generate_random_networks(8)
draw_multilayer_default(x,display=False,background_shape="circle")
generate_random_multiedges(x,12,style="piramidal")
generate_random_multiedges(x,80,style="curve2_bezier")
plt.show()

```

##Or a simple tuple based edge..

```{python}

from py3plex.multilayer import *
x = generate_random_networks(3)
draw_multilayer_default(x,display=False,background_shape="circle")
mel = [((1,1),(2,12))]
draw_multiplex_default(x,mel,input_type="tuple")
plt.show()

```