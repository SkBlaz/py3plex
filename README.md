
# This is the *Py3plex*, a lightweight multiplex network visualization library. It is capable of visualizing complex networks in an intuitive manner. Technically, this is some form of mixture between hive plots and ordinary 2d graph layouts.

Main goals of this library are:

> speed - heavy operations are vectorized using numpy
> simplicity - there are only two main functions which extend basic Networkx syntax
> elegance - all parameters can be tweaked an optimized for the best look
> modularity - this library is built from a programatic point of view, not a mathematical one. Basic structures revolve around list-like structures and not matrices.

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
![Alt text](images/test1.jpg?raw=true "Title")

## Another simple example, this time using randomly generated networks

```{python}

from py3plex.multilayer import *

x = generate_random_networks(8)
draw_multilayer_default(x,display=False,background_shape="circle")
generate_random_multiedges(x,12,style="piramidal")
generate_random_multiedges(x,80,style="curve2_bezier")
plt.show()

```


## Or a simple tuple based edge..

```{python}

from py3plex.multilayer import *
x = generate_random_networks(3)
draw_multilayer_default(x,display=False,background_shape="circle")
mel = [((1,1),(2,12))]
draw_multiplex_default(x,mel,input_type="tuple")
plt.show()

```

![Alt text](images/test2.jpg?raw=true "Title")

##Compare with standard layouts

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


```


![Alt text](images/test9.png?raw=true "Title")

## Other examples

![Alt text](images/test4.png?raw=true "Title")
![Alt text](images/test8.png?raw=true "Title")
![Alt text](images/test11.png?raw=true "Title")