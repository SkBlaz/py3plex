"""Example: Semantic Enrichment using Fisher's Exact Test

This example demonstrates how to:
- Load a biological network (epigenetics dataset)
- Detect communities using Louvain algorithm
- Extract UniProt protein nodes from communities
- Perform GO (Gene Ontology) functional enrichment using FET
- Apply FDR correction (Benjamini-Hochberg) for multiple testing

Functional enrichment identifies over-represented biological functions
in network communities, revealing biological significance of network structure.

Requirements:
- statsmodels package for statistical testing
- GO annotation file (goa_human.gaf.gz)
"""
# SKIP_CI: slow - Community detection and enrichment takes more than 10 seconds

try:
    import statsmodels
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("Warning: statsmodels not installed. Install with: pip install statsmodels")
    print("This example requires statsmodels for statistical enrichment.")
    exit(0)

# enrichment modules
from py3plex.algorithms.statistics import enrichment_modules

# community detection
from py3plex.algorithms.community_detection import community_wrapper as cw

# core data structure
from py3plex.core import multinet

# store communities
from collections import defaultdict
from py3plex.utils import get_dataset_path
from py3plex.exceptions import Py3plexIOError

# Check if dataset exists and load the network
try:
    dataset_path = get_dataset_path("epigenetics.gpickle")
    network = multinet.multi_layer_network().load_network(
        input_file=dataset_path,
        directed=False,
        input_type="gpickle_biomine")
except Py3plexIOError:
    print("Required dataset not found. Skipping example.")
    exit(0)

# identify partitions
partition = cw.louvain_communities(network.core_network)

# uniprot : node pairs are used as input! Generic example TBA
community_object = defaultdict(set)
for node, community in partition.items():
    if len(node[0].split(":")) == 2:
        db, name = node[0].split(":")
        if db == "UniProt":
            community_object[community].add(node)

# p<0.05 and fdr_bh correction for GO function -- this can take some time!
enrichment_table = enrichment_modules.fet_enrichment_uniprot(
    community_object, get_dataset_path("goa_human.gaf.gz"))

print(enrichment_table)
