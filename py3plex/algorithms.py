## this file contains some of the multilayer network analysis network
## algorithms, used in the BioGrid analysis

import networkx as nx ## graph primitives
from collections import defaultdict
import numpy as np ## Lalgebra
import itertools ## combinations

class multiplex_network:

    def __init__(self,networks,edges,name,timescale=None,verbose=True):
        self.networks = networks
        self.multiedges = edges
        self.names = name
        self.verbose = verbose
        self.timescale = timescale

    def monitor(self,message):
        if self.verbose == True:
            print(message)
            
    def print_basic_info(self):
        print("MULTIPLEX OBJECT DESCRIPTION")
        print("Number of layers",len(self.networks))
        print("Number of multiedges",len(self.multiedges))

    def inter_community_influence(self,minclique):

        if self.multiedges == []:
            return {'multiplex_community_percentage' : 0}
        
        communities = {}
        for nid,network in enumerate(self.networks):
            communities[nid] = nx.k_clique_communities(network, minclique)

        partial_mpx_community = 0

        nmpx = 0
        mpx = 0
        
        for k,v in communities.items():

            ## check all communities, accross all networks
            for node in v:
                try:
                    mpx = False
                    
                    ## check individual multiedges
                    for x,y in self.multiedges:
                        if node == x or node == y:
                            mpx = True
                    if mpx:
                        mpx += 1
                    else:
                        mmpx += 1                    
                except:
                    pass

        if mpx > 0:
            return {'multiplex_community_percentage' : nmpx*100/mpx}


    def degree_layerwise_stats(self):

        ## This algorithm computes the layer-wise degree stats        
        all_degrees = [sum(nx.degree(X).values())/len(X) for X in self.networks]
        variance = np.var(all_degrees)
        sd = np.std(all_degrees)
        mean = np.mean(all_degrees)

        ## result object
        result = {'variance' : variance,'sd' : sd,'mean' : mean}
        return result        

    def multilayer_community_stats(self,minclique):

        communities = {}
        for nid,network in enumerate(self.networks):
            communities_kc = nx.k_clique_communities(network, minclique)
            unique_nodes = len(set(itertools.chain(communities_kc)))
            communities[nid] = unique_nodes*100/len(network)

        percentages = np.fromiter(iter(communities.values()), dtype=float)
        total_variability = np.var(percentages)
        total_deviance = np.std(percentages)
        total_mean = np.mean(percentages)

        return {'variability' : total_variability,'deviation' : total_deviance, 'mean' : total_mean,'data' : communities}

    def detect_communities(self):
        communities = {}
        import community
        for network,name in zip(self.networks,self.names):
            self.monitor("Finding communities for layer: "+name)
            best_partition = community.best_partition(network)
            dx = defaultdict(list)
            for k,v in best_partition.items():                
                dx[v].append(k)

            communities[name] = list(dx.values())
        self.monitor("Assigning communities..")
        self.communities = communities
