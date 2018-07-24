## set of layout wrappers and algorithms used for visualization.

import networkx as nx

try:
    from fa2 import ForceAtlas2
    forceImport = True
except:
    forceImport = False

def compute_force_directed_layout(g,layout_parameters=None):
    
    if forceImport:
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
            pos = forceatlas2.forceatlas2_networkx_layout(g, pos=None, **layout_parameters)
        else:
            pos = forceatlas2.forceatlas2_networkx_layout(g, pos=None)
                
                
    else:
        if layout_parameters is not None:
            pos = nx.spring_layout(g,**layout_parameters)
        else:
            pos = nx.spring_layout(g)
        print("Using standard layout algorithm, fa2 not present on the system.")
        
    ## return positions
    return pos

