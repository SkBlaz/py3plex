# This is the multiplex layer constructor class

## draw multi layered network, takes .nx object list as input

## imports first

import networkx as nx
try:
    from matplotlib.patches import Rectangle
    from matplotlib.patches import Circle
except:
    pass

import random

import matplotlib.pyplot as plt

from . import colors # those are color ranges
from . import bezier # those are bezier curves
from . import polyfit
from . layout_algorithms import *
from . import drawing_machinery

main_figure = plt.figure()
shape_subplot = main_figure.add_subplot(111)
import numpy as np

def draw_multilayer_default(network_list, display=True, node_size=10,alphalevel=0.13,rectanglex = 1,rectangley = 1,background_shape="circle",background_color="rainbow",networks_color="rainbow",labels=False,arrowsize=0.5,label_position=1,verbose=False,remove_isolated_nodes=False,axis=None,edge_size=1,node_labels=False,node_font_size=5, scale_by_size=True):

    if background_color == "default":
        
        facecolor_list_background = colors.linear_gradient("#4286f4",n=len(network_list))['hex']

    elif background_color == "rainbow":
        
        facecolor_list_background = colors.colors_default

    elif background_color == None:
        
        facecolor_list_background = colors.colors_default
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
    circle_size = 1.04

    for network in network_list:
        if remove_isolated_nodes:
            isolates = list(nx.isolates(network))
            network = network.copy()
            network.remove_nodes_from(isolates)
        
        if verbose:
            print(nx.info(network))
        degrees = dict(nx.degree(nx.Graph(network)))
        cntr = 0
        cntr_all = 0
        no_position = []
        all_positions = []
        for node in network.nodes(data=True):
            if 'pos' not in node[1]:
                no_position.append(node[0])
                cntr+=1
            else:
                all_positions.append(node[1]['pos'])
                cntr_all+=1

        if len(no_position) > 0:
            network = network.copy()
            network.remove_nodes_from(no_position)
            
       # print("No position for {}. Found position for {}.".format(cntr,cntr_all))
        
        positions = nx.get_node_attributes(network, 'pos')
        cntr = 0

        for position in positions:
            if np.abs(positions[position][0]) > 0.5 or np.abs(positions[position][1]) > 0.5:
                positions[position] = positions[position]/np.linalg.norm(positions[position])
            try:
                positions[position][0] = positions[position][0] + 0.5 + start_location_network
                positions[position][1] = positions[position][1] + 0.5 + start_location_network
            except Exception as es:
                print(es,"err")

        ## this is the default delay for matplotlib canvas
        if labels != False:
            try:
                shape_subplot.text(start_location_network+label_position,start_location_network-label_position, labels[color])
            except Exception as es:
                print(es)
        
        if background_shape == "rectangle":
            shape_subplot.add_patch(Rectangle(
                (start_location_background, start_location_background), rectanglex, rectangley,
                alpha=alphalevel, linestyle="dotted", fill=True,facecolor=facecolor_list_background[color]))

        elif background_shape == "circle":
            shape_subplot.add_patch(Circle((start_location_background+shadow_size, start_location_background+shadow_size), circle_size, color=facecolor_list_background[color],alpha=alphalevel))
        else:
            pass
        
        start_location_network += 1.5
        start_location_background += 1.5
        if len(network.nodes()) > 10000:
            correction=10
        else:
            correction = 1

        if scale_by_size:
            node_sizes = [vx*node_size for vx in degrees.values()]
        else:
            node_sizes = [node_size for vx in degrees.values()]

        if np.sum(node_sizes) == 0:
            node_sizes = [node_size for vx in degrees.values()]

#        node_sizes = [(np.log(v) * node_size)/correction if v > 400 else node_size/correction for v in degrees.values()]

        # cntr+=1
        # for position in positions:
        #     if cntr<15:
        #         print(positions[position][0], positions[position][1])

        drawing_machinery.draw(network, positions, node_color=facecolor_list[color], with_labels=node_labels,edge_size=edge_size,node_size=node_sizes,arrowsize=arrowsize,ax=axis,font_size=node_font_size)
        color += 1

    if display == True:
        plt.show()


def draw_multiedges(network_list,multi_edge_tuple,input_type="nodes",linepoints="-.",alphachannel=0.3,linecolor="black",curve_height=1,style="curve2_bezier",linewidth=1,invert=False,linmod="both",resolution=0.1):
    # indices are correct network positions
    if input_type == "nodes":

        network_positions = [nx.get_node_attributes(network, 'pos') for network in network_list]
        global_positions = {}
        for position in network_positions:
            for k,v in position.items():
                global_positions[k]=v

        for pair in multi_edge_tuple:
            try:

                ## x0 x1, y0 y1

                p1 = [global_positions[pair[0]][0],global_positions[pair[1]][0]]
                p2 = [global_positions[pair[0]][1],global_positions[pair[1]][1]]
                if style == "line":

                    plt.plot(p1,p2,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)
                    
                elif style == "curve2_bezier":

                    x,y = bezier.draw_bezier(len(network_list),p1,p2,path_height=curve_height,inversion=invert,linemode=linmod,resolution=resolution)

                    plt.plot(x,y,linestyle=linepoints,lw=linewidth,alpha=alphachannel,color=linecolor)
                
                elif style == "curve3_bezier":

                    x,y = bezier.draw_bezier(len(network_list),p1,p2,mode="cubic",resolution=resolution)

                elif style == "curve3_fit":

                    x,y = polyfit.draw_order3(len(network_list),p1,p2)

                    plt.plot(x,y)

                elif style == "piramidal":
                
                    x,y = polyfit.draw_piramidal(len(network_list),p1,p2)
                    plt.plot(x,y,linestyle=linepoints,lw=1,alpha=alphachannel,color=linecolor)
                
                else:                
                    pass
                
            except Exception as err:
                pass
#                print(err,"test")
            
        
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


def supra_adjacency_matrix_plot(matrix,display=False):
    plt.imshow(matrix, interpolation='nearest', cmap=plt.cm.binary)
    if display:
        plt.show()
    

def hairball_plot(g, color_list=None,
                  display=False,
                  node_size=1,
                  text_color="black",
                  node_sizes = None, ## for custom sizes
                  layout_parameters=None,
                  legend=None,
                  scale_by_size=True,
                  layout_algorithm="force",
                  edge_width=0.01,
                  alpha_channel=0.5,
                  labels=None,
                  label_font_size=2):
    
    print("Beginning parsing..")
    nodes = g.nodes(data=True)
    potlabs = []
    
    for node in nodes:
        try:
            potlabs.append(node[0][1])
        except:
            potlabs.append("unlabeled")

    if color_list is None:
        unique_colors = np.unique(potlabs)
        color_mapping= dict(zip(list(unique_colors), colors.colors_default))
        try:
            final_color_mapping = [color_mapping[n[1]['type']] for n in nodes]
        except:
            print("Assigning colors..")
            final_color_mapping = [1]*len(nodes)
    else:
        print("Creating color mappings..")
        unique_colors = np.unique(color_list)
        color_mapping= dict(zip(list(unique_colors), colors.all_color_names))
        final_color_mapping = color_list
        # final_color_mapping = ["black"]*len(nodes)
    
    print("plotting..")

    degrees = dict(nx.degree(nx.Graph(g)))
    
    if scale_by_size:
        nsizes = [np.log(v) * node_size if v > 10 else v for v in degrees.values()]
    else:
        nsizes = [node_size for x in g.nodes()]

    if not node_sizes is None:
        nsizes = node_sizes
        
    # standard force -- directed layout
    if layout_algorithm == "force":
        pos = compute_force_directed_layout(g,layout_parameters)

    # random layout -- used for initialization of more complex algorithms
    elif layout_algorithm == "random":
        pos = compute_random_layout(g)

    elif layout_algorithm == "custom_coordinates":
        pos = layout_parameters['pos']
        
    elif layout_algorithm == "custom_coordinates_initial_force":
        pos = compute_force_directed_layout(g, layout_parameters)
    else:
        raise ValueError('Uknown layout algorithm: ' + str(layout_algorithm))

    nx.draw_networkx_edges(g, pos, alpha=alpha_channel, edge_color="black", width=edge_width, arrows=False)
    nx.draw_networkx_nodes(g, pos, nodelist=[n1[0] for n1 in nodes], node_color=final_color_mapping, node_size=nsizes,alpha=alpha_channel)
    if labels is not None:
        for el in labels:
            pos_el = pos[el]
            plt.text(pos_el[0],pos_el[1],el,fontsize=label_font_size,color=text_color)
            
#        nx.draw_networkx_labels(g, pos, font_size=label_font_size)

    plt.axis('off')

    #  add legend
    if legend is not None and legend:
        # TODO: legacy code - to je stara legenda, ko bodo testi bi js to zbrisal.
        if type(legend) == bool:
            markers = [plt.Line2D([0, 0], [0, 0], color=color_mapping[item], marker='o', linestyle='') for item in
                       list(unique_colors)]
            plt.legend(markers, range(len(list(unique_colors))), numpoints=1,fontsize = 'medium')
        # in bi ostal samo tale del:
        else:
            # the assumption is that legend[color] is the name of the group, represented by the color
            legend_colors = list(legend.keys())
            markers = [plt.Line2D([0, 0], [0, 0], color=key, marker='o', linestyle='') for key in legend_colors]
            plt.legend(markers, [legend[color] for color in legend_colors], numpoints=1, fontsize='medium')
    if display:
        plt.show()


if __name__ == "__main__":

    x = generate_random_networks(4)
    draw_multilayer_default(x, display=False, background_shape="circle")
    # generate_random_multiedges(x, 12, style="piramidal")
    generate_random_multiedges(x, 12, style="curve2_bezier")
    # network 1's 4 to network 6's 3 etc..    
    # mel = [((1,1),(5,1))]
    # draw_multiedges(x,mel,input_type="tuple")
    
    plt.show()
