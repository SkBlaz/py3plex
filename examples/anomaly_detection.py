## Author: Blaz Skrlj of IJS. This is the code for multiplex anomaly detection algorithm.

from py3plex.algorithms import *
from collections import defaultdict
import pandas as pd ## this is for tabelaric manipulations
import multiprocessing as mp

networks = defaultdict(list)
label_dict = {}


path_edges = "../testgraph/multiplex_datasets/NYClimateMarch2014_Multiplex_Social/Dataset/NYClimateMarch2014_multiplex.edges"

path_labels = "../testgraph/multiplex_datasets/NYClimateMarch2014_Multiplex_Social/Dataset/NYClimateMarch2014_layers.txt"

path_activity = "../testgraph/multiplex_datasets/NYClimateMarch2014_Multiplex_Social/Dataset/NYClimateMarch2014_activity.txt"

with open(path_edges) as me:
    for line in me:
        layer, n1, n2, weight = line.strip().split()
        networks[layer].append((n1,n2))

## get the labels
with open(path_labels) as lx:
    for line in lx:
        lid, lname = line.strip().split()
        label_dict[lid] = lname

multilayer_network = []
labs = []

for network_id, network_data in networks.items():
    G = nx.Graph()
    G.add_edges_from(network_data)
    print(nx.info(G))
    multilayer_network.append(G)
    labs.append(label_dict[network_id])

print("Found layers:",labs)

## construct the mx object
multi_object = multiplex_network(multilayer_network,[None],labs)
multi_object.detect_communities()

comcounts = pd.DataFrame(columns=['time','count','layer'])

## iterate through the time-series
tmplc = 0
num_lines = sum(1 for line in open(path_activity))

print("Starting the temporal component analysis..")


def find_matches(nx,ny,comm):
    if nx in comm and ny in comm:
        return 1
    else:
        return 0
    
pool = mp.Pool(processes=2)

with open(path_activity) as ax:
    for line in ax:
        tmplc +=1
        if tmplc % 1000 == 0:
            print("Progress:",str(tmplc*100/num_lines),"%")
            print(comcounts.describe())
        try:
            n1,n2,time,layer = line.strip().split()
            tmpCount = 0                        
            for com in multi_object.communities[layer]:
                if n1 in com and n2 in com:
                    tmpCount +=1

            comcounts = comcounts.append({'time':time,'count':tmpCount,'layer' : layer},ignore_index=True)
            
        except:
            ## those are beginning lines
            pass

print(comcounts.describe())
comcounts.to_csv("anomaly_dataset.csv")

0


print("Finished analysis..")       


## run separate anomaly detection on time vectors
## if >2;anomaly!



