"""
Case Study: Biological Multilayer Networks
===========================================

Domain: Biology / Bioinformatics
Difficulty: Intermediate
Dataset: Synthetic protein-gene-disease network

What this shows:
- Build a synthetic multilayer network (protein, gene, disease)
- Compute layer-aware stats and centralities
- Detect communities and interpret cross-layer structure
- Save headless matplotlib visualizations to /tmp

Prerequisites: matplotlib installed; this script switches to the Agg backend
for headless environments. All randomness is seeded for reproducibility.
"""
import numpy as np
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
from py3plex.core import multinet
from py3plex.dsl import L, Q

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


DEFAULT_SEED = 42


def create_biological_network():
    """
    Create a synthetic biological multilayer network.

    Layers:
    - protein: Protein-protein interactions
    - gene: Gene regulatory network
    - disease: Disease-gene associations

    Returns:
        multi_layer_network: The constructed network
    """
    _print_header("STEP 1: DATA IMPORT - Constructing Biological Network")

    network = multinet.multi_layer_network(directed=False)

    # Protein-protein interactions (PPI layer)
    # Simulating a small protein complex
    ppi_edges = [
        ['TP53', 'protein', 'MDM2', 'protein', 1],
        ['TP53', 'protein', 'ATM', 'protein', 1],
        ['MDM2', 'protein', 'ATM', 'protein', 1],
        ['BRCA1', 'protein', 'BRCA2', 'protein', 1],
        ['BRCA1', 'protein', 'ATM', 'protein', 1],
        ['EGFR', 'protein', 'KRAS', 'protein', 1],
        ['KRAS', 'protein', 'RAF1', 'protein', 1],
        ['RAF1', 'protein', 'MEK', 'protein', 1],
    ]

    # Gene regulatory network
    # Simulating transcription regulation
    gene_edges = [
        ['TP53_gene', 'gene', 'MDM2_gene', 'gene', 1],
        ['TP53_gene', 'gene', 'BAX_gene', 'gene', 1],
        ['BRCA1_gene', 'gene', 'RAD51_gene', 'gene', 1],
        ['EGFR_gene', 'gene', 'KRAS_gene', 'gene', 1],
        ['MYC_gene', 'gene', 'CYCLIN_D1_gene', 'gene', 1],
    ]

    # Disease-gene associations
    # Linking genes to diseases
    disease_edges = [
        ['TP53_gene', 'disease', 'cancer', 'disease', 1],
        ['BRCA1_gene', 'disease', 'breast_cancer', 'disease', 1],
        ['BRCA2_gene', 'disease', 'breast_cancer', 'disease', 1],
        ['EGFR_gene', 'disease', 'lung_cancer', 'disease', 1],
        ['KRAS_gene', 'disease', 'colorectal_cancer', 'disease', 1],
        ['cancer', 'disease', 'breast_cancer', 'disease', 1],
        ['cancer', 'disease', 'lung_cancer', 'disease', 1],
    ]

    # Add all edges
    network.add_edges(ppi_edges + gene_edges + disease_edges, input_type="list")

    print(f"\nNetwork constructed:")
    print(f"  Protein layer: {len(ppi_edges)} interactions")
    print(f"  Gene layer: {len(gene_edges)} regulations")
    print(f"  Disease layer: {len(disease_edges)} associations")

    return network


def compute_basic_stats(network):
    """Display basic multilayer statistics with layer-level analysis."""
    _print_header("STEP 2: BASIC NETWORK STATS")

    network.basic_stats()

    # Use DSL to get comprehensive layer-specific statistics
    print("\nLayer-specific statistics (using DSL):")
    print("\n{:<15} {:<10} {:<12} {:<12} {:<12}".format(
        "Layer", "Nodes", "Edges", "Avg Degree", "Density"))
    print("-" * 70)

    for layer in ['protein', 'gene', 'disease']:
        # Node stats
        node_result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        node_df = node_result.to_pandas()
        node_df['degree'] = node_df['degree'].apply(_as_scalar)

        # Edge stats
        edge_result = Q.edges().from_layers(L[layer]).execute(network)
        num_edges = len(edge_result)

        # Compute density
        num_nodes = len(node_df)
        max_edges = num_nodes * (num_nodes - 1) / 2  # undirected
        density = num_edges / max_edges if max_edges > 0 else 0

        print("{:<15} {:<10} {:<12} {:<12.2f} {:<12.4f}".format(
            layer.capitalize(),
            num_nodes,
            num_edges,
            node_df['degree'].mean(),
            density
        ))

    print("\nLayer-specific degree distributions:")
    for layer in ['protein', 'gene', 'disease']:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        df['degree'] = df['degree'].apply(_as_scalar)
        print(f"\n  {layer.upper()} layer:")
        print(f"    Min degree: {df['degree'].min()}")
        print(f"    Max degree: {df['degree'].max()}")
        print(f"    Median degree: {df['degree'].median():.1f}")
        print(f"    Std degree: {df['degree'].std():.2f}")


def run_analysis_pipeline(network):
    """
    Run the complete analysis pipeline:
    1. Compute centrality measures
    2. Detect communities
    3. Identify hub nodes
    """
    _print_header("STEP 3: ANALYSIS PIPELINE")

    # 3.1 Compute centrality measures
    print("\n[3.1] Computing centrality measures...")
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "betweenness_centrality", "closeness_centrality")
         .order_by("-betweenness_centrality")
         .execute(network)
    )

    df = result.to_pandas()
    for col in ("degree", "betweenness_centrality", "closeness_centrality"):
        if col in df:
            df[col] = df[col].apply(_as_scalar)
    print("\nTop 5 nodes by betweenness centrality:")
    print(df[['id', 'layer', 'degree', 'betweenness_centrality']].head())

    # Compute layer-specific centralities
    print("\n[3.1b] Layer-specific centrality analysis:")
    for layer in ['protein', 'gene', 'disease']:
        layer_result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", "betweenness_centrality")
             .order_by("-betweenness_centrality")
             .limit(3)
             .execute(network)
        )
        layer_df = layer_result.to_pandas()
        for col in ("degree", "betweenness_centrality"):
            if col in layer_df:
                layer_df[col] = layer_df[col].apply(_as_scalar)
        print(f"\n  {layer.upper()} - Top 3 central nodes:")
        for _, row in layer_df.iterrows():
            node_id = row['id'][0] if isinstance(row['id'], tuple) else row['id']
            bc = row['betweenness_centrality']
            print(f"    {node_id}: {bc:.4f}")

    # 3.2 Community detection
    print("\n[3.2] Detecting communities...")
    partition_dict = louvain_multilayer(network, random_state=42)

    num_communities = len(set(partition_dict.values()))
    print(f"\nCommunity detection results:")
    print(f"  Communities found: {num_communities}")

    # Analyze community composition
    communities_by_layer = {}
    for layer in ['protein', 'gene', 'disease']:
        communities_by_layer[layer] = {}
        layer_nodes = [node for node in partition_dict.keys() if node[1] == layer]
        for node in layer_nodes:
            comm = partition_dict[node]
            if comm not in communities_by_layer[layer]:
                communities_by_layer[layer][comm] = []
            communities_by_layer[layer][comm].append(node[0])

    print("\nCommunity composition by layer:")
    for layer, comms in communities_by_layer.items():
        print(f"\n  {layer.upper()}:")
        for comm_id, members in sorted(comms.items()):
            print(f"    Community {comm_id}: {len(members)} nodes - {members[:3]}...")

    # 3.3 Identify hub nodes (high degree + high centrality)
    print("\n[3.3] Identifying hub nodes...")
    hubs = df[(df['degree'] >= df['degree'].quantile(0.75)) &
              (df['betweenness_centrality'] >= df['betweenness_centrality'].quantile(0.75))]

    print(f"\nHub nodes (top 25% in degree AND betweenness):")
    for _, row in hubs.iterrows():
        print(f"  {row['id']}: degree={row['degree']}, betweenness={row['betweenness_centrality']:.3f}")

    return partition_dict


def visualize_and_interpret(network, partition_dict):
    """
    Create visualizations and interpret results.
    """
    _print_header("STEP 4: VISUALIZATION & INTERPRETATION")

    if plt is None:
        print("matplotlib not available; skipping visualization. Install matplotlib to enable plots.")
        return

    np.random.seed(DEFAULT_SEED)

    # Store partition for visualization
    network.assign_partition(partition_dict)

    print("\n[4.1] Creating network visualization...")

    # Create figure with subplots
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Network structure
    plt.sca(axes[0])
    network.visualize_network(show=False, axis=axes[0])
    axes[0].set_title("Biological Multilayer Network Structure")

    # Plot 2: Degree distribution by layer
    plt.sca(axes[1])
    for layer in ['protein', 'gene', 'disease']:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        df['degree'] = df['degree'].apply(_as_scalar)
        axes[1].hist(df['degree'], alpha=0.5, label=layer, bins=10)

    axes[1].set_xlabel('Degree')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Degree Distribution by Layer')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('/tmp/biological_network_analysis.png', dpi=150)
    print("Visualization saved to /tmp/biological_network_analysis.png")

    # Interpretation
    print("\n[4.2] Interpretation:")
    print("""
    Key Findings:

    1. LAYER CHARACTERISTICS:
       - Protein layer: Shows typical PPI network properties with hub proteins
       - Gene layer: Regulatory cascades with transcription factors as hubs
       - Disease layer: Disease nodes connect to multiple genes (pleiotropy)

    2. HUB NODES:
       - TP53 (tumor suppressor): Central in protein interactions and gene regulation
       - BRCA1/BRCA2: Key players in DNA repair pathways
       - Cancer-related genes: High betweenness centrality (bridges between pathways)

    3. COMMUNITIES:
       - Communities roughly align with biological pathways
       - Cross-layer communities reveal gene-disease modules
       - Protein complexes form tight communities in PPI layer

    4. BIOLOGICAL INSIGHTS:
       - The multilayer structure captures how genetic variations (gene layer)
         affect protein interactions (protein layer) and manifest as diseases
         (disease layer)
       - Hub nodes are potential drug targets due to their central role
       - Community structure suggests functional modules that could be
         targeted therapeutically
    """)


def main():
    """Run the complete biological networks case study."""
    _print_header("CASE STUDY: BIOLOGICAL MULTILAYER NETWORKS")
    print("\nThis workflow demonstrates end-to-end analysis of biological")
    print("multilayer networks using py3plex.")

    np.random.seed(DEFAULT_SEED)

    # Step 1: Create network
    network = create_biological_network()

    # Step 2: Basic statistics
    compute_basic_stats(network)

    # Step 3: Analysis pipeline
    partition_dict = run_analysis_pipeline(network)

    # Step 4: Visualization and interpretation
    visualize_and_interpret(network, partition_dict)

    print("\n" + "="*70)
    print("CASE STUDY COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("  * Constructed protein-gene-disease network")
    print("  * Computed multilayer statistics with layer-level analysis")
    print("  * Identified hub nodes and communities")
    print("  * Generated visualizations")
    print("  * Interpreted biological significance")
    print("\nNext steps:")
    print("  - Apply this workflow to real biological data")
    print("  - Integrate with pathway databases (KEGG, Reactome)")
    print("  - Use DSL for advanced queries and filtering")


def _print_header(title: str):
    """Pretty-print section headers consistently."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def _as_scalar(value):
    """Normalize metrics that may be wrapped in dicts (e.g., mean/value)."""
    if isinstance(value, dict):
        for key in ("mean", "value"):
            if key in value:
                return value[key]
        if len(value) == 1:
            return next(iter(value.values()))
    return value


if __name__ == "__main__":
    main()
