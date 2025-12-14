"""
Case Study: Transportation Multilayer Network
==============================================

Domain: Transportation / Urban Planning
Difficulty: Intermediate
Dataset: Synthetic multi-modal transport network

This case study demonstrates analyzing urban transportation networks with
multiple modes of transit:

1. Data import - Building bus, metro, and bike-share layers
2. Basic network stats - Modal connectivity, transfer points
3. Analysis pipeline - Accessibility → centrality → route optimization
4. Visualization - Multi-modal network with transfer hubs

The analysis reveals how different transport modes complement each other and
identifies critical transfer points.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, UQ
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd


def create_transport_network():
    """
    Create a synthetic multi-modal transportation network.
    
    Layers:
    - bus: Bus route connections
    - metro: Metro/subway lines
    - bike: Bike-sharing stations
    
    Returns:
        multi_layer_network: The constructed network
    """
    print("="*70)
    print("STEP 1: DATA IMPORT - Building Multi-Modal Transport Network")
    print("="*70)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Bus network - Dense coverage, many stops
    bus_edges = [
        ['CityHall', 'bus', 'Library', 'bus', 1],
        ['Library', 'bus', 'Park', 'bus', 1],
        ['Park', 'bus', 'Mall', 'bus', 1],
        ['Mall', 'bus', 'Hospital', 'bus', 1],
        ['Hospital', 'bus', 'University', 'bus', 1],
        ['CityHall', 'bus', 'Train_Station', 'bus', 1],
        ['Train_Station', 'bus', 'Airport', 'bus', 1],
        ['Park', 'bus', 'Zoo', 'bus', 1],
        ['Mall', 'bus', 'Stadium', 'bus', 1],
    ]
    
    # Metro network - Fast backbone, fewer stops
    metro_edges = [
        ['CityHall', 'metro', 'Train_Station', 'metro', 1],
        ['Train_Station', 'metro', 'University', 'metro', 1],
        ['University', 'metro', 'Airport', 'metro', 1],
        ['CityHall', 'metro', 'Mall', 'metro', 1],
        ['Mall', 'metro', 'Stadium', 'metro', 1],
    ]
    
    # Bike-share network - Short distances, recreational
    bike_edges = [
        ['CityHall', 'bike', 'Library', 'bike', 1],
        ['Library', 'bike', 'Park', 'bike', 1],
        ['Park', 'bike', 'Zoo', 'bike', 1],
        ['CityHall', 'bike', 'Museum', 'bike', 1],
        ['Museum', 'bike', 'Park', 'bike', 1],
        ['Mall', 'bike', 'Stadium', 'bike', 1],
    ]
    
    # Add all edges
    network.add_edges(bus_edges + metro_edges + bike_edges, input_type="list")
    
    print(f"\nNetwork constructed:")
    print(f"  Bus routes: {len(bus_edges)} connections")
    print(f"  Metro lines: {len(metro_edges)} connections")
    print(f"  Bike stations: {len(bike_edges)} connections")
    print(f"  Total connections: {len(bus_edges) + len(metro_edges) + len(bike_edges)}")
    
    return network


def compute_basic_stats(network):
    """Compute multi-modal transport statistics with detailed layer-level analysis."""
    print("\n" + "="*70)
    print("STEP 2: BASIC NETWORK STATS - Modal Analysis")
    print("="*70)
    
    network.basic_stats()
    
    # Comprehensive mode-specific statistics
    print("\nTransport mode metrics:")
    print("\n{:<10} {:<10} {:<12} {:<15} {:<15} {:<15} {:<12}".format(
        "Mode", "Stations", "Connections", "Avg Degree", "Min Degree", "Max Degree", "Density"))
    print("-" * 95)
    
    stats = []
    for mode in ['bus', 'metro', 'bike']:
        # Node stats
        node_result = (
            Q.nodes()
             .from_layers(L[mode])
             .compute("degree")
             .execute(network)
        )
        node_df = node_result.to_pandas()
        
        # Edge stats
        edge_result = Q.edges().from_layers(L[mode]).execute(network)
        num_edges = len(edge_result)
        
        # Compute density
        num_nodes = len(node_df)
        max_edges = num_nodes * (num_nodes - 1) / 2
        density = num_edges / max_edges if max_edges > 0 else 0
        
        print("{:<10} {:<10} {:<12} {:<15.2f} {:<15} {:<15} {:<12.4f}".format(
            mode.capitalize(),
            num_nodes,
            num_edges,
            node_df['degree'].mean(),
            int(node_df['degree'].min()),
            int(node_df['degree'].max()),
            density
        ))
        
        stats.append({
            'Mode': mode.capitalize(),
            'Stations': num_nodes,
            'Connections': num_edges,
            'Density': density
        })
    
    # Identify transfer hubs (locations served by multiple modes)
    print("\nTransfer hub analysis:")
    all_locations = set()
    location_modes = {}
    
    for mode in ['bus', 'metro', 'bike']:
        result = Q.nodes().from_layers(L[mode]).execute(network)
        mode_locations = {node[0] for node in result.items}
        all_locations.update(mode_locations)
        for loc in mode_locations:
            if loc not in location_modes:
                location_modes[loc] = []
            location_modes[loc].append(mode)
    
    # Find transfer hubs (2+ modes)
    transfer_hubs = {loc: modes for loc, modes in location_modes.items() if len(modes) >= 2}
    print(f"  Total locations: {len(all_locations)}")
    print(f"  Transfer hubs (2+ modes): {len(transfer_hubs)}")
    print("\n  Major transfer hubs:")
    for loc, modes in sorted(transfer_hubs.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"    {loc}: {', '.join(modes)}")


def analyze_accessibility(network):
    """
    Analyze network accessibility and identify key nodes with confidence bounds.
    """
    print("\n" + "="*70)
    print("STEP 3: ANALYSIS PIPELINE - Accessibility Analysis")
    print("="*70)
    
    # 3.1 Compute accessibility metrics with uncertainty quantification
    print("\n[3.1] Computing accessibility metrics with confidence bounds...")
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .uq(method="perturbation", n_samples=50, ci=0.95, seed=42)
         .compute("degree", "betweenness_centrality", "closeness_centrality")
         .order_by("-betweenness_centrality__mean")
         .execute(network)
    )
    
    df = result.to_pandas(expand_uncertainty=True)
    
    print("\nTop 5 most accessible locations (by betweenness with 95% confidence intervals):")
    for _, row in df.head(5).iterrows():
        location = row['id'][0] if isinstance(row['id'], tuple) else row['id']
        mode = row['layer']
        bc = row['betweenness_centrality']
        bc_low = row['betweenness_centrality_ci95_low']
        bc_high = row['betweenness_centrality_ci95_high']
        print(f"  {location} ({mode}): betweenness={bc:.4f} (95% CI: [{bc_low:.4f}, {bc_high:.4f}]), degree={row['degree']}")
    
    # 3.2 Mode-specific accessibility with confidence bounds
    print("\n[3.2] Mode-specific accessibility with confidence bounds:")
    for mode in ['bus', 'metro', 'bike']:
        mode_result = (
            Q.nodes()
             .from_layers(L[mode])
             .uq(method="perturbation", n_samples=50, ci=0.95, seed=42)
             .compute("betweenness_centrality", "closeness_centrality")
             .order_by("-betweenness_centrality__mean")
             .limit(3)
             .execute(network)
        )
        mode_df = mode_result.to_pandas(expand_uncertainty=True)
        print(f"\n  {mode.upper()} - Most critical stations:")
        for _, row in mode_df.iterrows():
            location = row['id'][0] if isinstance(row['id'], tuple) else row['id']
            bc = row['betweenness_centrality']
            bc_low = row['betweenness_centrality_ci95_low']
            bc_high = row['betweenness_centrality_ci95_high']
            print(f"    {location}: betweenness={bc:.4f} (95% CI: [{bc_low:.4f}, {bc_high:.4f}])")
    
    return df


def detect_service_zones(network):
    """
    Detect service zones (communities) in the transport network.
    """
    print("\n[3.3] Detecting service zones...")
    partition_dict = louvain_multilayer(network, random_state=42)
    
    num_zones = len(set(partition_dict.values()))
    print(f"\nService zone detection:")
    print(f"  Zones identified: {num_zones}")
    
    # Analyze zone composition
    zones = {}
    for node, zone_id in partition_dict.items():
        location = node[0]
        mode = node[1]
        if zone_id not in zones:
            zones[zone_id] = {}
        if location not in zones[zone_id]:
            zones[zone_id][location] = []
        zones[zone_id][location].append(mode)
    
    print("\nService zone composition:")
    for zone_id, locations in sorted(zones.items()):
        print(f"\n  Zone {zone_id}: {len(locations)} locations")
        for loc, modes in list(locations.items())[:4]:
            print(f"    {loc}: {', '.join(modes)}")
    
    return partition_dict


def visualize_and_interpret(network, accessibility_df, partition_dict):
    """
    Create visualizations and interpret transport patterns.
    """
    print("\n" + "="*70)
    print("STEP 4: VISUALIZATION & INTERPRETATION")
    print("="*70)
    
    network.assign_partition(partition_dict)
    
    print("\n[4.1] Creating visualizations...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Network structure
    plt.sca(axes[0, 0])
    network.visualize_network(show=False, axis=axes[0, 0])
    axes[0, 0].set_title("Multi-Modal Transport Network")
    
    # Plot 2: Connectivity by mode
    plt.sca(axes[0, 1])
    for mode in ['bus', 'metro', 'bike']:
        result = (
            Q.nodes()
             .from_layers(L[mode])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        axes[0, 1].hist(df['degree'], alpha=0.5, label=mode, bins=8)
    axes[0, 1].set_xlabel('Connections')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Connectivity Distribution by Mode')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Mode coverage
    plt.sca(axes[1, 0])
    mode_coverage = []
    for mode in ['bus', 'metro', 'bike']:
        result = Q.nodes().from_layers(L[mode]).execute(network)
        mode_coverage.append(len(result))
    axes[1, 0].bar(['Bus', 'Metro', 'Bike'], mode_coverage, color=['#FFA500', '#4169E1', '#32CD32'])
    axes[1, 0].set_ylabel('Number of Stations')
    axes[1, 0].set_title('Network Coverage by Mode')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Accessibility metrics
    plt.sca(axes[1, 1])
    axes[1, 1].scatter(accessibility_df['degree'], 
                      accessibility_df['betweenness_centrality'], 
                      c=accessibility_df['closeness_centrality'],
                      cmap='viridis', alpha=0.6, s=100)
    axes[1, 1].set_xlabel('Degree (Direct Connections)')
    axes[1, 1].set_ylabel('Betweenness Centrality')
    axes[1, 1].set_title('Station Accessibility (color = closeness)')
    cbar = plt.colorbar(axes[1, 1].collections[0], ax=axes[1, 1])
    cbar.set_label('Closeness Centrality')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/tmp/transport_network_analysis.png', dpi=150)
    print("Visualization saved to /tmp/transport_network_analysis.png")
    
    # Interpretation
    print("\n[4.2] Interpretation:")
    print("""
    Key Findings:
    
    1. MODAL CHARACTERISTICS:
       - Bus: High coverage, dense network (last-mile connectivity)
       - Metro: Sparse but fast backbone (long-distance travel)
       - Bike: Recreational/short trips (complements public transit)
    
    2. TRANSFER HUBS:
       - CityHall, Mall, Train_Station serve as major transfer points
       - High betweenness centrality indicates critical role in network
       - These locations enable seamless multi-modal journeys
    
    3. SERVICE ZONES:
       - Communities align with geographic neighborhoods
       - Each zone is well-served by complementary modes
       - Zone structure suggests natural service boundaries
    
    4. TRANSPORT INSIGHTS:
       - Multi-modal integration is key to network efficiency
       - Critical nodes (transfer hubs) require extra capacity
       - Bus network provides essential coverage gaps
       - Metro serves as high-capacity backbone
       - Bike-share complements fixed-route transit
    
    5. PLANNING IMPLICATIONS:
       - Invest in transfer hub infrastructure
       - Ensure multi-modal integration at key points
       - Consider service zone boundaries for planning
       - Protect critical nodes from disruption
    """)


def main():
    """Run the complete transportation networks case study."""
    print("\n" + "="*70)
    print("CASE STUDY: TRANSPORTATION MULTILAYER NETWORK")
    print("="*70)
    print("\nAnalyzing multi-modal urban transportation network.")
    
    # Step 1: Create network
    network = create_transport_network()
    
    # Step 2: Basic statistics
    compute_basic_stats(network)
    
    # Step 3: Analysis pipeline
    accessibility_df = analyze_accessibility(network)
    partition_dict = detect_service_zones(network)
    
    # Step 4: Visualization and interpretation
    visualize_and_interpret(network, accessibility_df, partition_dict)
    
    print("\n" + "="*70)
    print("CASE STUDY COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("  * Built multi-modal transport network")
    print("  * Identified transfer hubs with layer-level statistics")
    print("  * Computed accessibility metrics with confidence intervals")
    print("  * Detected service zones")
    print("  * Generated planning insights")
    print("\nNext steps:")
    print("  - Add real GTFS (General Transit Feed Specification) data")
    print("  - Include temporal scheduling and frequencies")
    print("  - Analyze disruption scenarios (what if a hub fails?)")
    print("  - Optimize routes based on centrality metrics")


if __name__ == "__main__":
    main()
