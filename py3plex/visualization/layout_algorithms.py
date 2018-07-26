## set of layout wrappers and algorithms used for visualization.

import networkx as nx
import numpy as np
import itertools

try:
    from fa2 import ForceAtlas2
    forceImport = True
except:
    forceImport = False

def compute_force_directed_layout(g,layout_parameters=None,initial_positions=None):
    
    if forceImport:
        try:
            forceatlas2 = ForceAtlas2(
                # Behavior alternatives
                outboundAttractionDistribution=False,  # Dissuade hubs
                linLogMode=False,  # NOT IMPLEMENTED
                adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
                edgeWeightInfluence=1.0,

                # Performance
                jitterTolerance=1.0,  # Tolerance
                barnesHutOptimize=True,
                barnesHutTheta=1.2,
                multiThreaded=False,  # NOT IMPLEMENTED

                # Tuning
                scalingRatio=2.0,
                strongGravityMode=False,
                gravity=1.0,

                # Log
                verbose=True)

            if layout_parameters != None:
                pos = forceatlas2.forceatlas2_networkx_layout(g, pos=initial_positions,**layout_parameters)
            else:
                pos = forceatlas2.forceatlas2_networkx_layout(g, pos=initial_positions)

            norm = np.max(itertools.chain(zip(*pos)))
            pos = [(a/norm,b/norm) for a,b in pos]
            print(pos)
            
        except:
            print("Too few nodes for BH approximation, standard algorithm is being used..")
            if layout_parameters is not None:
                pos = nx.spring_layout(g,**layout_parameters)
            else:
                pos = nx.spring_layout(g)
            print("Using standard layout algorithm, fa2 not present on the system.")
                            
    else:
        if layout_parameters is not None:
            pos = nx.spring_layout(g,**layout_parameters)
        else:
            pos = nx.spring_layout(g)
        print("Using standard layout algorithm, fa2 not present on the system.")
        
    ## return positions
    return pos

def compute_random_layout(g):
    coordinates = tuple(np.random.rand(1,2))
    pos = {n : tuple(np.random.rand(1,2).tolist()[0]) for n in g.nodes()}
    return pos
