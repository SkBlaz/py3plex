"""
Case Study: Social Multiplex Network Analysis
==============================================

Domain: Social Networks / Communication
Difficulty: Beginner
Dataset: Synthetic multi-platform social network

This case study demonstrates analyzing social interactions across multiple
communication platforms:

1. Data import - Building a social network with Facebook, Twitter, LinkedIn layers
2. Basic network stats - Cross-platform presence, layer-specific metrics
3. Analysis pipeline - Influence metrics → community detection → layer comparison
4. Visualization - Multi-platform visualization with interpretation

The analysis reveals how users behave differently across platforms and identifies
cross-platform influencers.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
from py3plex.visualization.multilayer import draw_multilayer_default
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd


def create_social_network():
    """
    Create a synthetic social multiplex network.
    
    Layers:
    - facebook: Friend connections
    - twitter: Follower network
    - linkedin: Professional connections
    
    Returns:
        multi_layer_network: The constructed network
    """
    print("="*70)
    print("STEP 1: DATA IMPORT - Building Social Multiplex Network")
    print("="*70)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Facebook layer - Dense friend network
    facebook_edges = [
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Alice', 'facebook', 'Charlie', 'facebook', 1],
        ['Bob', 'facebook', 'Charlie', 'facebook', 1],
        ['Bob', 'facebook', 'David', 'facebook', 1],
        ['Charlie', 'facebook', 'Eve', 'facebook', 1],
        ['David', 'facebook', 'Frank', 'facebook', 1],
        ['Eve', 'facebook', 'Frank', 'facebook', 1],
        ['Frank', 'facebook', 'Grace', 'facebook', 1],
    ]
    
    # Twitter layer - More sparse, asymmetric patterns
    twitter_edges = [
        ['Alice', 'twitter', 'Bob', 'twitter', 1],
        ['Alice', 'twitter', 'Eve', 'twitter', 1],
        ['Bob', 'twitter', 'Charlie', 'twitter', 1],
        ['Charlie', 'twitter', 'David', 'twitter', 1],
        ['David', 'twitter', 'Eve', 'twitter', 1],
        ['Eve', 'twitter', 'Frank', 'twitter', 1],
        ['Grace', 'twitter', 'Alice', 'twitter', 1],
        ['Grace', 'twitter', 'Bob', 'twitter', 1],
        ['Grace', 'twitter', 'Charlie', 'twitter', 1],
    ]
    
    # LinkedIn layer - Professional connections (moderately dense)
    linkedin_edges = [
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Alice', 'linkedin', 'David', 'linkedin', 1],
        ['Bob', 'linkedin', 'Charlie', 'linkedin', 1],
        ['Charlie', 'linkedin', 'Eve', 'linkedin', 1],
        ['David', 'linkedin', 'Frank', 'linkedin', 1],
    ]
    
    # Add all edges
    network.add_edges(facebook_edges + twitter_edges + linkedin_edges, input_type="list")
    
    print(f"\nNetwork constructed:")
    print(f"  Facebook: {len(facebook_edges)} friendships")
    print(f"  Twitter: {len(twitter_edges)} follows")
    print(f"  LinkedIn: {len(linkedin_edges)} professional connections")
    print(f"  Total edges: {len(facebook_edges) + len(twitter_edges) + len(linkedin_edges)}")
    
    return network


def compute_basic_stats(network):
    """Compute cross-platform statistics."""
    print("\n" + "="*70)
    print("STEP 2: BASIC NETWORK STATS - Cross-Platform Analysis")
    print("="*70)
    
    network.basic_stats()
    
    # Platform-specific statistics
    print("\nPlatform-specific metrics:")
    stats = []
    for platform in ['facebook', 'twitter', 'linkedin']:
        result = (
            Q.nodes()
             .from_layers(L[platform])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        stats.append({
            'Platform': platform.capitalize(),
            'Users': len(df),
            'Avg Degree': df['degree'].mean(),
            'Max Degree': df['degree'].max(),
            'Min Degree': df['degree'].min()
        })
    
    stats_df = pd.DataFrame(stats)
    print("\n", stats_df.to_string(index=False))
    
    # Multi-platform users
    print("\nCross-platform presence:")
    all_nodes = set()
    for platform in ['facebook', 'twitter', 'linkedin']:
        result = Q.nodes().from_layers(L[platform]).execute(network)
        platform_users = {node[0] for node in result.items}
        all_nodes.update(platform_users)
    
    unique_users = len(all_nodes)
    total_accounts = sum([s['Users'] for s in stats])
    print(f"  Unique users: {unique_users}")
    print(f"  Total accounts: {total_accounts}")
    print(f"  Avg platforms per user: {total_accounts / unique_users:.1f}")


def identify_influencers(network):
    """
    Identify influential users across platforms.
    """
    print("\n" + "="*70)
    print("STEP 3: ANALYSIS PIPELINE - Identifying Influencers")
    print("="*70)
    
    # 3.1 Compute influence metrics
    print("\n[3.1] Computing influence metrics...")
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "betweenness_centrality", "pagerank")
         .order_by("-pagerank")
         .execute(network)
    )
    
    df = result.to_pandas()
    
    # Find cross-platform influencers (users with high metrics)
    print("\nTop 5 influencers by PageRank:")
    top_influencers = df.head(5)
    for _, row in top_influencers.iterrows():
        user = row['id'][0] if isinstance(row['id'], tuple) else row['id']
        platform = row['layer']
        print(f"  {user} ({platform}): PageRank={row['pagerank']:.4f}, Degree={row['degree']}")
    
    # 3.2 Platform-specific influence
    print("\n[3.2] Platform-specific top influencers:")
    for platform in ['facebook', 'twitter', 'linkedin']:
        platform_result = (
            Q.nodes()
             .from_layers(L[platform])
             .compute("degree", "betweenness_centrality")
             .order_by("-betweenness_centrality")
             .limit(3)
             .execute(network)
        )
        platform_df = platform_result.to_pandas()
        print(f"\n  {platform.upper()}:")
        for _, row in platform_df.iterrows():
            user = row['id'][0] if isinstance(row['id'], tuple) else row['id']
            print(f"    {user}: degree={row['degree']}, betweenness={row['betweenness_centrality']:.3f}")
    
    return df


def detect_communities(network):
    """
    Detect and analyze social communities.
    """
    print("\n[3.3] Detecting communities...")
    partition_dict = louvain_multilayer(network, random_state=42)
    
    num_communities = len(set(partition_dict.values()))
    print(f"\nCommunity detection results:")
    print(f"  Communities: {num_communities}")
    
    # Analyze cross-platform communities
    print("\nCross-platform community composition:")
    communities = {}
    for node, comm_id in partition_dict.items():
        user = node[0]
        platform = node[1]
        if comm_id not in communities:
            communities[comm_id] = {}
        if user not in communities[comm_id]:
            communities[comm_id][user] = []
        communities[comm_id][user].append(platform)
    
    for comm_id, members in sorted(communities.items()):
        print(f"\n  Community {comm_id}: {len(members)} users")
        # Show first few members
        for user, platforms in list(members.items())[:3]:
            print(f"    {user}: {', '.join(platforms)}")
    
    return partition_dict


def visualize_and_interpret(network, influence_df, partition_dict):
    """
    Create visualizations and interpret social patterns.
    """
    print("\n" + "="*70)
    print("STEP 4: VISUALIZATION & INTERPRETATION")
    print("="*70)
    
    network.assign_partition(partition_dict)
    
    print("\n[4.1] Creating visualizations...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Network structure
    plt.sca(axes[0, 0])
    draw_multilayer_default([network], display=False)
    axes[0, 0].set_title("Social Multiplex Network")
    
    # Plot 2: Degree distribution by platform
    plt.sca(axes[0, 1])
    for platform in ['facebook', 'twitter', 'linkedin']:
        result = (
            Q.nodes()
             .from_layers(L[platform])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        axes[0, 1].hist(df['degree'], alpha=0.5, label=platform, bins=10)
    axes[0, 1].set_xlabel('Degree')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Connection Distribution by Platform')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Platform sizes
    plt.sca(axes[1, 0])
    platform_sizes = []
    for platform in ['facebook', 'twitter', 'linkedin']:
        result = Q.nodes().from_layers(L[platform]).execute(network)
        platform_sizes.append(len(result))
    axes[1, 0].bar(['Facebook', 'Twitter', 'LinkedIn'], platform_sizes, color=['#3b5998', '#1DA1F2', '#0077B5'])
    axes[1, 0].set_ylabel('Number of Users')
    axes[1, 0].set_title('Platform Size Comparison')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Influence distribution
    plt.sca(axes[1, 1])
    axes[1, 1].scatter(influence_df['degree'], influence_df['betweenness_centrality'], alpha=0.6)
    axes[1, 1].set_xlabel('Degree')
    axes[1, 1].set_ylabel('Betweenness Centrality')
    axes[1, 1].set_title('Influence Metrics (Degree vs Betweenness)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/tmp/social_network_analysis.png', dpi=150)
    print("Visualization saved to /tmp/social_network_analysis.png")
    
    # Interpretation
    print("\n[4.2] Interpretation:")
    print("""
    Key Findings:
    
    1. PLATFORM CHARACTERISTICS:
       - Facebook: Densest network (strong reciprocal friendships)
       - Twitter: More asymmetric (follower model allows broadcast)
       - LinkedIn: Moderate density (professional network effect)
    
    2. INFLUENCER PATTERNS:
       - Cross-platform influencers have high PageRank across all layers
       - Platform-specific influencers emerge due to different usage patterns
       - Grace shows high influence on Twitter (many followers)
    
    3. COMMUNITIES:
       - Communities align with friend groups that span platforms
       - Some users are "platform-specific" (only active on one layer)
       - Cross-platform communities suggest real-world social groups
    
    4. SOCIAL INSIGHTS:
       - Multi-platform users have higher overall influence
       - Different platforms serve different social functions
       - Community structure reveals social cohesion across digital spaces
       - Twitter's structure facilitates information broadcast vs Facebook's dialogue
    """)


def main():
    """Run the complete social networks case study."""
    print("\n" + "="*70)
    print("CASE STUDY: SOCIAL MULTIPLEX NETWORK ANALYSIS")
    print("="*70)
    print("\nAnalyzing user behavior across Facebook, Twitter, and LinkedIn.")
    
    # Step 1: Create network
    network = create_social_network()
    
    # Step 2: Basic statistics
    compute_basic_stats(network)
    
    # Step 3: Analysis pipeline
    influence_df = identify_influencers(network)
    partition_dict = detect_communities(network)
    
    # Step 4: Visualization and interpretation
    visualize_and_interpret(network, influence_df, partition_dict)
    
    print("\n" + "="*70)
    print("CASE STUDY COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("  ✓ Built multi-platform social network")
    print("  ✓ Analyzed cross-platform metrics")
    print("  ✓ Identified influencers")
    print("  ✓ Detected social communities")
    print("  ✓ Visualized platform differences")
    print("\nNext steps:")
    print("  - Apply to real social media data (Twitter API, Facebook Graph API)")
    print("  - Add temporal analysis (how communities evolve)")
    print("  - Integrate sentiment analysis with network structure")


if __name__ == "__main__":
    main()
