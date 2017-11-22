
# This is the *Py3Plex*, a lightweight multiplex network visualization and analysis library.

> It is capable of visualizing complex networks in an intuitive manner. Technically, this is some form of mixture between hive plots and ordinary 2d graph layouts.

Main goals of this library are:

> speed - heavy operations are vectorized using numpy
> simplicity - there are only two main functions which extend basic Networkx syntax
> elegance - all parameters can be tweaked an optimized for the best look

A multiplex network can be constructed in 3 simple steps:

1. Load individual layers
2. select layouts for individual layers
3. add multiplex connections

Layout part is not necessary required, should the networks only be analized.


# What is the main goal:

![Alt text](images/merged1.png?raw=true "Title")


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

![Alt text](images/test2.jpg?raw=true "Title")

## Another simple example, this time using randomly generated networks

```{python}

from py3plex.multilayer import *

x = generate_random_networks(8)
draw_multilayer_default(x,display=False,background_shape="circle")
generate_random_multiedges(x,12,style="piramidal")
generate_random_multiedges(x,80,style="curve2_bezier")
plt.show()

```
![Alt text](images/test1.jpg?raw=true "Title")

## Or a simple tuple based edge..

```{python}

from py3plex.multilayer import *
x = generate_random_networks(3)
draw_multilayer_default(x,display=False,background_shape="circle")
mel = [((1,1),(2,12))]
draw_multiplex_default(x,mel,input_type="tuple")
plt.show()

```

## Compare with standard layouts

```{python}

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
            
        #if tmp_graph.number_of_edges() > 2:
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
    
view_by_type("testgraph/epigenetics.gpickle")

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


```

![Alt text](images/test14.png?raw=true "Title")

## Plot a generic multilayer network (Arabidopsis)

```{python}

## this example demonstrates the use of basic algorithms

import matplotlib.pyplot as plt
import networkx as nx

from py3plex.multilayer import *
from py3plex.algorithms import *

from collections import defaultdict

## this example apart from visualization demonstrates some common algorithms
## algorithms operate on multiplex object, as seen below.

networks = defaultdict(list)
label_dict = {}

## get the nodes
with open("testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_multiplex.edges") as me:
    for line in me:
        layer, n1, n2, weight = line.strip().split()
        networks[layer].append((n1,n2))

## get the labels
with open("testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_layers.txt") as lx:
    for line in lx:
        lid, lname = line.strip().split()
        label_dict[lid] = lname

## draw the network
multilayer_network = []
labs = []
for network_id,network_data in networks.items():
    G = nx.Graph()
    G.add_edges_from(network_data)
    print(nx.info(G))
    tmp_pos=nx.spring_layout(G)
    nx.set_node_attributes(G,'pos',tmp_pos)
    multilayer_network.append(G)
    labs.append(label_dict[network_id])

draw_multilayer_default(multilayer_network,background_shape="circle",display=True,labels=labs,networks_color="rainbow")


```

![Alt text](images/test13.png?raw=true "Title")

## Calculate some network statistics

```{python}

## this example demonstrates algorithm use on a multilayer network

from py3plex.algorithms import *
from collections import defaultdict

networks = defaultdict(list)
label_dict = {}

## get the nodes
with open("../testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_multiplex.edges") as me:
    for line in me:
        layer, n1, n2, weight = line.strip().split()
        networks[layer].append((n1,n2))

## get the labels
with open("../testgraph/multiplex_datasets/Arabidopsis_Multiplex_Genetic/Dataset/arabidopsis_genetic_layers.txt") as lx:
    for line in lx:
        lid, lname = line.strip().split()
        label_dict[lid] = lname

## draw the network
multilayer_network = []
labs = []

for network_id, network_data in networks.items():
    G = nx.Graph()
    G.add_edges_from(network_data)
    print(nx.info(G))
    multilayer_network.append(G)
    labs.append(label_dict[network_id])

## start the analysis with an object
multi_object = multiplex_network(multilayer_network,[],labs)

## some basic info
multi_object.print_basic_info()

## variability of degrees
print(multi_object.degree_layerwise_stats())

## k-clique based multi-community influence
print(multi_object.inter_community_influence(4))

## community percentage
print(multi_object.multilayer_community_stats(4))


```

## Other examples

![Alt text](images/test4.png?raw=true "Title")
![Alt text](images/test8.png?raw=true "Title")
![Alt text](images/test11.png?raw=true "Title")
