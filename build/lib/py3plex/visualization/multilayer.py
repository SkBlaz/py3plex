## This is the multiplex layer constructor class

## draw multi layered network, takes .nx object list as input

## imports first

import networkx as nx

from matplotlib.patches import Rectangle
from matplotlib.patches import Circle

import random
import matplotlib.pyplot as plt
import numpy as np

from . import colors # those are color ranges
from . import bezier # those are bezier curves
from . import polyfit
from . layout_algorithms import *

main_figure = plt.figure()
shape_subplot = main_figure.add_subplot(111)

def draw_multilayer_default(network_list, display=True, nodesize=2,alphalevel=0.13,rectanglex = 1,rectangley = 1,background_shape="circle",background_color="rainbow",networks_color="rainbow",labels=False,layout_algorithm="force",layout_parameters=None):

    if background_color == "default":
        
        facecolor_list_background = colors.linear_gradient("#4286f4",n=len(network_list))['hex']

    elif background_color == "rainbow":
        
        facecolor_list_background = colors.colors_default

    elif background_color == "none":
        
        alphalevel=0

    else:
        pass

    if networks_color == "rainbow":
        
        facecolor_list = colors.colors_default

    elif networks_color == "black":
        
        facecolor_list = ["black"]*len(network_list)

    else:
        pass

    
    start_location_network = 0
    start_location_background = 0
    color = 0
    shadow_size = 0.5
    circle_size = 1.05
    for network in network_list:

        degrees = dict(nx.degree(nx.Graph(network)))

        if layout_algorithm == "force":
            tmp_pos = compute_force_directed_layout(network,layout_parameters)
            
        elif layout_algorithm == "random":
            tmp_pos = compute_random_layout(network)
            
        elif layout_algorithm == "custom_coordinates":
            tmp_pos = layout_parameters['pos']
            
        for node in network.nodes(data=True):
            coordinates = tmp_pos[node[0]]
            node[1]['pos'] = coordinates
            
        positions = nx.get_node_attributes(network, 'pos')
        for position in positions:
            try:
                positions[position][0] = positions[position][0] + 0.5 + start_location_network
                positions[position][1] = positions[position][1] + 0.5 + start_location_network
            except:                
                pass
                
        ## this is the default delay for matplotlib canvas
        if labels != False:
            try:
                shape_subplot.text(start_location_network+0.8,start_location_network-0.8, labels[color])
            except:
                pass
        
        if background_shape == "rectangle":
            shape_subplot.add_patch(Rectangle(
                (start_location_background, start_location_background), rectanglex, rectangley,
                alpha=alphalevel, linestyle="dotted", fill=True,facecolor=facecolor_list_background[color]
            ))

        elif background_shape == "circle":
            ## tukaj pride krogeci
            shape_subplot.add_patch(Circle((start_location_background+shadow_size, start_location_background+shadow_size), circle_size, color=facecolor_list_background[color],alpha=alphalevel))
            pass
        else:
            pass
        
        start_location_network += 1.5
        start_location_background += 1.5
        node_sizes = [np.log(v) * nodesize if v > 400 else 1 for v in degrees.values()]
        
        nx.draw(network, nx.get_node_attributes(network, 'pos'),node_color=facecolor_list[color], with_labels=False,edge_size=5,node_size=node_sizes)
        color += 1

    if display == True:
        plt.show()

def draw_multiedges(network_list,multi_edge_tuple,input_type="nodes",linepoints="-.",alphachannel=0.3,linecolor="black",curve_height=1,style="curve2_bezier",linewidth=1,invert=False,linmod="both"):

    #indices are correct network positions

    if input_type == "tuple":
        network_positions = [nx.get_node_attributes(network, 'pos') for network in network_list]
    
        for el in multi_edge_tuple:

            p1 = [network_positions[el[0][0]][el[0][1]][0],network_positions[el[1][0]][el[1][1]][1]]

            p2 = [network_positions[el[0][0]][el[0][1]][1],network_positions[el[1][0]][el[1][1]][0]]

            ## miljon enih ifelse stavkov comes here..

            if style == "line":

                plt.plot(p1,p2,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)

            elif style == "curve2_bezier":                

                x,y = bezier.draw_bezier(len(network_list),p1,p2,path_height=curve_height,linemode=linmod)
                plt.plot(x,y,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)
                
            
            elif style == "curve3_bezier":

                x,y = bezier.draw_bezier(len(network_list),p1,p2,mode="cubic")

            elif style == "curve3_fit":

                x,y = polyfit.draw_order3(len(network_list),p1,p2)

                plt.plot(x,y)

            elif style == "piramidal":
                
                x,y = polyfit.draw_piramidal(len(network_list),p1,p2)
                plt.plot(x,y,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)
                
            else:                
                pass
            

    elif input_type == "nodes":

        network_positions = [nx.get_node_attributes(network, 'pos') for network in network_list]
        global_positions = {}
        global_layers = []
        for position in network_positions:
            for k,v in position.items():
                global_positions[k]=v
                global_layers.append(k.split("_")[0])
        
        for pair in multi_edge_tuple:
            try:
                p1 = [global_positions[str(pair[0])][0],global_positions[str(pair[1])][0]]
                p2 = [global_positions[str(pair[0])][1],global_positions[str(pair[1])][1]]

                if style == "line":

                    plt.plot(p1,p2,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)
                    
                elif style == "curve2_bezier":
                    x,y = bezier.draw_bezier(len(network_list),p1,p2,path_height=curve_height,inversion=invert,linemode=linmod)
                    plt.plot(x,y,linestyle=linepoints,lw=linewidth,alpha=alphachannel,color=linecolor)
                
                elif style == "curve3_bezier":

                    x,y = bezier.draw_bezier(len(network_list),p1,p2,mode="cubic")

                elif style == "curve3_fit":

                    x,y = polyfit.draw_order3(len(network_list),p1,p2)

                    plt.plot(x,y)

                elif style == "piramidal":
                
                    x,y = polyfit.draw_piramidal(len(network_list),p1,p2)
                    plt.plot(x,y,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)
                
                else:                
                    pass
                
            except:
                pass
#                print("Failed to get global positions..")
            
        
def generate_random_multiedges(network_list,random_edges,style="line",linepoints="-.",upper_first=2,lower_first=0,lower_second=2,inverse_tag=False,pheight=1):

    edge_subplot = main_figure.add_subplot(111)
    return_list = []
    print(style)
    ## this needs to be in the form of:
    for k in range(random_edges):
        try:
            random_network1 = random.randint(0,upper_first)
            random_network2 = random.randint(lower_second,len(network_list))

            node_first = random.randint(1,3)
            node_second = random.randint(1,3)
        
            positions_first_net = nx.get_node_attributes(network_list[random_network1], 'pos')                                        
            positions_second_net = nx.get_node_attributes(network_list[random_network2], 'pos')

            p1 = [positions_first_net[node_first][0],positions_second_net[node_second][0]]
            p2 = [positions_first_net[node_first][1],positions_second_net[node_second][1]]

            if style == "line":

                plt.plot(p1, p2,'k-', lw=1,color="black",linestyle="dotted")

            elif style == "curve2_bezier":                

                x,y = bezier.draw_bezier(len(network_list),p1,p2,inversion=inverse_tag,path_height=pheight)
                plt.plot(x,y,linestyle=linepoints,lw=1,alpha=0.3)
                
            
            elif style == "curve3_bezier":

                x,y = bezier.draw_bezier(len(network_list),p1,p2,mode="cubic")

            elif style == "curve3_fit":

                x,y = polyfit.draw_order3(len(network_list),p1,p2)

                plt.plot(x,y)

            elif style == "piramidal":
                
                x,y = polyfit.draw_piramidal(len(network_list),p1,p2)
                plt.plot(x,y,color="black",alpha=0.3,linestyle="-.",lw=1)
                
            else:                
                pass
        except:
            pass
            
def generate_random_networks(number_of_networks):

    network_list = []    
    for j in range(number_of_networks):
        tmp_graph = nx.gnm_random_graph(random.randint(60,300),random.randint(5,300))
        tmp_pos=nx.spring_layout(tmp_graph)
        nx.set_node_attributes(tmp_graph,'pos',tmp_pos)
        network_list.append(tmp_graph)
    return network_list         

def hairball_plot(g,color_list=None,display=False,layered=True,nodesize=1,layout_parameters = None,legend=False,scale_by_size=True,layout_algorithm="force_default"):

    print("Beginning parsing..")
    nodes = g.nodes(data=True)
    potlabs = []

    if not layered:
        for node in g.nodes(data=True):
            node[1]['type'] = "0"
    
    for node in nodes:
        potlabs.append(node[1]['type'])

    if color_list is None:
        unique_colors = np.unique(potlabs)
        color_mapping= dict(zip(list(unique_colors), colors.colors_default))
        final_color_mapping = [color_mapping[n[1]['type']] for n in nodes]        
    else:
        print("Creating color mappings..")
        unique_colors = np.unique(color_list)
        color_mapping= dict(zip(list(unique_colors), colors.all_color_names))
        final_color_mapping = color_list
    
    print("plotting..")

    degrees = dict(nx.degree(nx.Graph(g)))
    if scale_by_size:
        nsizes = [np.log(v) * nodesize if v > 10 else v for v in degrees.values()]
    else:
        nsizes = [nodesize for x in g.nodes()]

    ## standard force -- directed layout
    if layout_algorithm == "force":
        pos = compute_force_directed_layout(g,layout_parameters)

    ## random layout -- used for initialization of more complex algorithms
    elif layout_algorithm == "random":
        pos = compute_random_layout(g)

    elif layout_algorithm == "custom_coordinates":
        pos = layout_parameters['pos']
        
    else:
        pos = compute_force_directed_layout(g,layout_parameters)

    ec = nx.draw_networkx_edges(g, pos, alpha=0.85,edge_color="black", width=0.1,arrows=False)
    nc = nx.draw_networkx_nodes(g, pos, nodelist=[n1[0] for n1 in nodes], node_color=final_color_mapping,with_labels=False, node_size=nsizes)
    plt.axis('off')

    ## add legend
    markers = [plt.Line2D([0,0],[0,0], color=color_mapping[item], marker='o', linestyle='') for item in list(unique_colors)]
    
    if legend:
        plt.legend(markers, list(unique_colors), numpoints=1,fontsize = 'medium')
    
    if display:
        plt.show()

if __name__ == "__main__":

    x = generate_random_networks(4)
    draw_multilayer_default(x,display=False,background_shape="circle")
    # generate_random_multiedges(x,12,style="piramidal")    
    generate_random_multiedges(x,12,style="curve2_bezier")    
    # network 1's 4 to network 6's 3 etc..    
    # mel = [((1,1),(5,1))]
    # draw_multiedges(x,mel,input_type="tuple")
    
    plt.show()
