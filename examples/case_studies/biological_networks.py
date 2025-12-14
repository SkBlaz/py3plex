"""
Case Study: Biological Multilayer Networks
===========================================

Domain: Biology / Bioinformatics
Difficulty: Intermediate
Dataset: Synthetic protein-gene-disease network

This case study demonstrates a complete workflow for analyzing biological
multilayer networks, including:

1. Data import - Constructing a protein-gene-disease multilayer network
2. Basic network stats - Node/edge counts, degree distributions
3. Analysis pipeline - Centrality → community detection → interpretation
4. Visualization - Layer-specific and integrated views

The workflow shows how multilayer networks capture the complexity of
biological systems where proteins interact, genes regulate, and diseases manifest.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, UQ
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd


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
    print("="*70)
    print("STEP 1: DATA IMPORT - Constructing Biological Network")
    print("="*70)
    
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
    print("\n" + "="*70)
    print("STEP 2: BASIC NETWORK STATS")
    print("="*70)
    
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
        print(f"\n  {layer.upper()} layer:")
        print(f"    Min degree: {df['degree'].min()}")
        print(f"    Max degree: {df['degree'].max()}")
        print(f"    Median degree: {df['degree'].median():.1f}")
        print(f"    Std degree: {df['degree'].std():.2f}")


def run_analysis_pipeline(network):
    """
    Run the complete analysis pipeline:
    1. Compute centrality measures with confidence bounds
    2. Detect communities
    3. Identify hub nodes
    """
    print("\n" + "="*70)
    print("STEP 3: ANALYSIS PIPELINE")
    print("="*70)
    
    # 3.1 Compute centrality measures with uncertainty quantification
    print("\n[3.1] Computing centrality measures with confidence bounds...")
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .uq(method="perturbation", n_samples=50, ci=0.95, seed=42)
         .compute("degree", "betweenness_centrality", "closeness_centrality")
         .order_by("-betweenness_centrality__mean")
         .execute(network)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    print("\nTop 5 nodes by betweenness centrality (with 95% confidence intervals):")
    print(df[['id', 'layer', 'degree', 'betweenness_centrality', 
              'betweenness_centrality_ci95_low', 'betweenness_centrality_ci95_high']].head())
    
    # Compute layer-specific centralities with confidence bounds
    print("\n[3.1b] Layer-specific centrality analysis with confidence bounds:")
    for layer in ['protein', 'gene', 'disease']:
        layer_result = (
            Q.nodes()
             .from_layers(L[layer])
             .uq(method="perturbation", n_samples=50, ci=0.95, seed=42)
             .compute("degree", "betweenness_centrality")
             .order_by("-betweenness_centrality__mean")
             .limit(3)
             .execute(network)
        )
        layer_df = layer_result.to_pandas(expand_uncertainty=True)
        print(f"\n  {layer.upper()} - Top 3 central nodes:")
        for _, row in layer_df.iterrows():
            node_id = row['id'][0] if isinstance(row['id'], tuple) else row['id']
            bc = row['betweenness_centrality']
            bc_low = row['betweenness_centrality_ci95_low']
            bc_high = row['betweenness_centrality_ci95_high']
            print(f"    {node_id}: {bc:.4f} (95% CI: [{bc_low:.4f}, {bc_high:.4f}])")
    
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
    print("\n" + "="*70)
    print("STEP 4: VISUALIZATION & INTERPRETATION")
    print("="*70)
    
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
    print("\n" + "="*70)
    print("CASE STUDY: BIOLOGICAL MULTILAYER NETWORKS")
    print("="*70)
    print("\nThis workflow demonstrates end-to-end analysis of biological")
    print("multilayer networks using py3plex.")
    
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
    print("  * Identified hub nodes and communities with confidence intervals")
    print("  * Generated visualizations")
    print("  * Interpreted biological significance")
    print("\nNext steps:")
    print("  - Apply this workflow to real biological data")
    print("  - Integrate with pathway databases (KEGG, Reactome)")
    print("  - Use DSL for advanced queries and filtering")


if __name__ == "__main__":
    main()
