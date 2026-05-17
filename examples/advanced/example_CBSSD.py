"""
Community-Based Semantic Subgroup Discovery (CBSSD) Example

Teaches:
- Combine community detection with semantic enrichment
- Use Hedwig for rule learning on protein interaction networks
- Convert community partitions to RDF format
- Link network communities to Gene Ontology annotations

Background:
CBSSD (Skrlj et al., 2017) discovers meaningful patterns in communities
by linking them to semantic knowledge bases (e.g., Gene Ontology).

Prerequisites:
- Dataset: intact02.gpickle (protein interaction network)
- Dataset: goa_human.gaf.gz (Gene Ontology annotations)
- Dataset: go.obo.gz (Gene Ontology structure)
- Hedwig rule learner (bundled with py3plex)

SKIP_CI: slow - Takes more than 10 seconds to complete
"""

# This works for UniProt identifiers (TODO: generalize to other identifier types)

from pathlib import Path

from py3plex.core import multinet
from py3plex.algorithms import hedwig
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.utils import get_dataset_path

print("=" * 70)
print("COMMUNITY-BASED SEMANTIC SUBGROUP DISCOVERY (CBSSD)")
print("=" * 70)

# ===============================================================================
# Step 1: Load protein interaction network
# ===============================================================================

print("\n[1] Loading protein interaction network...")
print("-" * 70)
network = multinet.multi_layer_network().load_network(
    get_dataset_path("intact02.gpickle"), directed=False, input_type="gpickle")

print("Network loaded successfully!")
network.basic_stats()

# ===============================================================================
# Step 2: Detect communities using Louvain algorithm
# ===============================================================================

print("\n[2] Detecting communities...")
print("-" * 70)
partition = cw.louvain_communities(network)
print(f"Found {len(set(partition.values()))} communities")
print(f"Sample partition: {dict(list(partition.items())[:5])}")

# ===============================================================================
# Step 3: Convert community partitions to RDF format
# ===============================================================================

print("\n[3] Converting partitions to RDF format...")
print("-" * 70)
dataset_name = get_dataset_path("example_partition_inputs.n3")
print(f"Converting community partitions to RDF using Gene Ontology annotations...")
print(f"Output file: {dataset_name}")

rdf_partitions = hedwig.convert_mapping_to_rdf(
    partition,
    annotation_mapping_file=get_dataset_path("goa_human.gaf.gz"),
    layer_type="uniprotkb")
rdf_partitions.serialize(destination=dataset_name, format="n3")
print("RDF conversion complete!")

# ===============================================================================
# Step 4: Convert Gene Ontology OBO file to N3 format
# ===============================================================================

print("\n[4] Converting Gene Ontology to N3 format...")
print("-" * 70)
bk_path = get_dataset_path("bk.n3")
bk_dir = str(Path(bk_path).parent)
hedwig.obo2n3(get_dataset_path("go.obo.gz"), bk_path,
              get_dataset_path("goa_human.gaf.gz"))
print("Gene Ontology conversion complete!")

# ===============================================================================
# Step 5: Configure and run Hedwig rule learner
# ===============================================================================

print("\n[5] Configuring Hedwig rule learner...")
print("-" * 70)
print("Setting up Hedwig parameters:")
print("  - Mode: subgroups discovery")
print("  - Score: lift (significance measure)")
print("  - Support threshold: 0.01")
print("  - Max rule depth: 8")
print("  - Beam width: 300")

hedwig_input_parameters = {
    "bk_dir": bk_dir,
    "data": get_dataset_path("example_partition_inputs.n3"),
    "format": "n3",
    "output": None,
    "covered": None,
    "mode": "subgroups",
    "target": None,
    "score": "lift",
    "negations": True,
    "alpha": 0.05,
    "latex_report": False,
    "FDR": 0.05,
    "leaves": True,
    "learner": "heuristic",
    "optimalsubclass": False,
    "uris": False,
    "beam": 300,
    "support": 0.01,
    "depth": 8,
    "nocache": False,
    "verbose": False,
    "adjust": "none"
}

network.monitor("Starting rule learning")
print("\n[6] Running Hedwig rule learner (this may take a while)...")
print("-" * 70)

# Initiate the learning part - discovers semantic patterns in communities
hedwig.run(hedwig_input_parameters)

print("\n" + "=" * 70)
print("CBSSD ANALYSIS COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  [OK] Communities detected in protein interaction network")
print("  [OK] Communities linked to Gene Ontology annotations")
print("  [OK] Semantic rules learned to characterize communities")
print("  [OK] Useful for discovering biological meaning in network structure")
