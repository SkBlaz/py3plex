## a simple FET-based partition enrichment..

## enrichment modules
from py3plex.algorithms.statistics import enrichment_modules

## community detection
from py3plex.algorithms.community_detection import community_wrapper as cw

## core data structure
from py3plex.core import multinet

## store communities
from collections import defaultdict

## load the network
network = multinet.multi_layer_network().load_network(
    input_file="../datasets/epigenetics.gpickle",
    directed=False,
    input_type="gpickle_biomine")

## identify partitions
partition = cw.louvain_communities(network.core_network)

## uniprot : node pairs are used as input! Generic example TBA
community_object = defaultdict(set)
for node, community in partition.items():
    if len(node[0].split(":")) == 2:
        db, name = node[0].split(":")
        if db == "UniProt":
            community_object[community].add(node)

## p<0.05 and fdr_bh correction for GO function -- this can take some time!
enrichment_table = enrichment_modules.fet_enrichment_uniprot(
    community_object, "../datasets/goa_human.gaf.gz")

print(enrichment_table)
