.. _case_studies:

Use Cases & Case Studies
========================

This chapter provides complete, end-to-end case studies demonstrating py3plex in different research domains. Each case study includes:

1. **Problem context** — What real-world question are we answering?
2. **Data modeling decisions** — How do we represent this problem as a multilayer network?
3. **Complete code** — Working examples you can adapt
4. **Interpretation** — What do the results mean?
5. **Adaptation guide** — How to apply this template to your own data

.. contents:: Case Studies
   :local:
   :depth: 2

Case Study 1: Biological Network Analysis
------------------------------------------

Multilayer Protein-Protein Interaction Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem Context:**

You're a computational biologist studying protein interactions in yeast. You have PPI data from three experimental sources with different reliability levels:

* **Yeast two-hybrid (Y2H):** High-throughput but many false positives
* **Affinity purification mass spectrometry (AP-MS):** More reliable but biased toward stable complexes
* **Literature curated:** Highly reliable but incomplete

You want to:

1. Find functional modules (groups of proteins that work together)
2. Identify proteins that are central across evidence types (likely real interactions)
3. Discover proteins that bridge different functional modules

**Data Modeling Decisions:**

* **Node type:** Proteins (same set across layers for multiplex analysis)
* **Layers:** One per evidence type (Y2H, AP-MS, Literature)
* **Edges:** Physical protein-protein interactions
* **Network type:** Multiplex (same proteins, different interaction evidence)

**Complete Code:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import Counter
    import numpy as np
    
    # === 1. Create the network ===
    # In practice, you'd load from files; here we create a toy example
    network = multinet.multi_layer_network(network_type='multiplex')
    
    # Simulated PPI data (protein pairs by evidence type)
    # Replace with your actual data loading
    ppi_data = {
        'Y2H': [
            ('CDC28', 'CLB2'), ('CDC28', 'CLB5'), ('CLB2', 'SIC1'),
            ('ACT1', 'MYO2'), ('ACT1', 'TPM1'), ('MYO2', 'TPM1'),
            ('CDC28', 'CDC6'), ('CDC6', 'ORC1'),  # cell cycle proteins
        ],
        'APMS': [
            ('CDC28', 'CLB2'), ('CDC28', 'CKS1'), ('CLB2', 'CKS1'),
            ('ACT1', 'ABP1'), ('ACT1', 'TPM1'),
            ('CDC6', 'ORC1'), ('ORC1', 'ORC2'), ('ORC2', 'ORC3'),  # origin recognition complex
        ],
        'Literature': [
            ('CDC28', 'CLB2'), ('CDC28', 'CLB5'), ('CDC28', 'CKS1'),
            ('ACT1', 'MYO2'), ('MYO2', 'TPM1'),
            ('CDC6', 'ORC1'),  # well-established interaction
        ],
    }
    
    # Add edges to network
    for layer, interactions in ppi_data.items():
        for protein1, protein2 in interactions:
            network.add_edges([
                [protein1, layer, protein2, layer, 1.0]
            ], input_type="list")
    
    # === 2. Basic exploration ===
    print("=== Network Overview ===")
    network.basic_stats()
    
    # === 3. Identify high-confidence interactions ===
    # Interactions that appear in multiple evidence types are more reliable
    print("\n=== Evidence Overlap Analysis ===")
    
    # Get edges from each layer
    edges_by_layer = {}
    for layer in network.get_layers():
        layer_subnet = network.subnetwork([layer], subset_by="layers")
        # Extract edge pairs (ignoring layer info)
        edges = set()
        for edge in layer_subnet.get_edges():
            # Normalize edge representation (sorted tuple)
            pair = tuple(sorted([edge[0][0], edge[1][0]]))
            edges.add(pair)
        edges_by_layer[layer] = edges
    
    # Find edges in multiple layers
    all_edges = set()
    for edges in edges_by_layer.values():
        all_edges.update(edges)
    
    edge_evidence_counts = {}
    for edge in all_edges:
        count = sum(1 for layer_edges in edges_by_layer.values() if edge in layer_edges)
        edge_evidence_counts[edge] = count
    
    print("High-confidence interactions (in 3/3 evidence types):")
    for edge, count in sorted(edge_evidence_counts.items(), key=lambda x: x[1], reverse=True):
        if count == 3:
            print(f"  {edge[0]} -- {edge[1]}: {count} evidence types")
    
    print("\nMedium-confidence interactions (in 2/3 evidence types):")
    for edge, count in sorted(edge_evidence_counts.items(), key=lambda x: x[1], reverse=True):
        if count == 2:
            print(f"  {edge[0]} -- {edge[1]}: {count} evidence types")
    
    # === 4. Node activity analysis ===
    print("\n=== Protein Activity Across Evidence Types ===")
    unique_proteins = set()
    for node in network.get_nodes():
        unique_proteins.add(node[0])  # Extract protein name
    
    protein_activity = {}
    for protein in unique_proteins:
        activity = mls.node_activity(network, protein)
        protein_activity[protein] = activity
    
    print("Proteins present in all evidence types (activity = 1.0):")
    for protein, activity in sorted(protein_activity.items(), key=lambda x: x[1], reverse=True):
        if activity == 1.0:
            print(f"  {protein}")
    
    # === 5. Community detection (functional modules) ===
    print("\n=== Functional Module Detection ===")
    
    # Lower coupling (omega=0.5) because different evidence types 
    # may reveal different aspects of the interactome
    partition = louvain_multilayer(
        network, 
        gamma=1.0,      # Standard resolution
        omega=0.5,      # Moderate coupling
        random_state=42
    )
    
    # Analyze communities
    num_communities = len(set(partition.values()))
    print(f"Detected {num_communities} functional modules")
    
    # Group proteins by community
    communities = {}
    for node, comm in partition.items():
        protein = node[0]  # Extract protein name
        if comm not in communities:
            communities[comm] = set()
        communities[comm].add(protein)
    
    print("\nFunctional modules found:")
    for comm_id, proteins in sorted(communities.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  Module {comm_id}: {proteins}")
    
    # === 6. Versatility analysis (cross-module bridging) ===
    print("\n=== Bridge Proteins (High Versatility) ===")
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    top_versatile = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]
    for node, score in top_versatile:
        print(f"  {node}: versatility = {score:.4f}")

**Interpretation:**

The analysis reveals several insights:

1. **High-confidence interactions** (CDC28-CLB2, ACT1-TPM1) appear in all three evidence types, making them likely true interactions suitable for downstream analysis.

2. **Functional modules** correspond to known protein complexes:
   
   * Cell cycle regulators (CDC28, CLB2, CLB5, CKS1, SIC1)
   * Actin cytoskeleton (ACT1, MYO2, TPM1, ABP1)
   * DNA replication origin complex (CDC6, ORC1, ORC2, ORC3)

3. **Bridge proteins** with high versatility may connect different functional modules and could be interesting drug targets or key regulators.

**Adapting to Your Data:**

1. Replace the ``ppi_data`` dictionary with your actual data loading code
2. Adjust ``omega`` based on your domain: lower for diverse evidence types, higher if you expect consistency
3. Add Gene Ontology enrichment analysis to validate that communities match known functional annotations
4. Consider edge weights based on evidence quality (e.g., literature = 3.0, APMS = 2.0, Y2H = 1.0)


Case Study 2: Multi-Platform Social Network Analysis
----------------------------------------------------

Cross-Platform Influence Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem Context:**

You're a social media researcher studying how influencers operate across platforms. You have data from three platforms:

* **Twitter/X:** Public follower/following relationships
* **YouTube:** Subscription relationships
* **Instagram:** Follow relationships

You want to:

1. Identify influencers who are successful across platforms (vs. platform-specific)
2. Understand how different platforms are related (do the same people follow each other?)
3. Find communities that span platforms

**Data Modeling Decisions:**

* **Node type:** Users (mapped across platforms using verified identities)
* **Layers:** One per platform (Twitter, YouTube, Instagram)
* **Edges:** Follow/subscribe relationships (directed in reality, undirected for this analysis)
* **Network type:** Multiplex (same users, different platforms)

**Complete Code:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    from collections import Counter
    import networkx as nx
    
    # === 1. Create the network ===
    network = multinet.multi_layer_network(network_type='multiplex')
    
    # Simulated social network data
    # In practice: load from APIs or datasets with user ID mapping
    social_data = {
        'Twitter': [
            ('influencer_A', 'user_1'), ('influencer_A', 'user_2'),
            ('influencer_A', 'user_3'), ('influencer_B', 'user_2'),
            ('influencer_B', 'user_4'), ('user_1', 'user_2'),
            ('user_3', 'user_5'), ('influencer_C', 'user_6'),
        ],
        'YouTube': [
            ('influencer_A', 'user_1'), ('influencer_A', 'user_3'),
            ('influencer_B', 'user_2'), ('influencer_B', 'user_3'),
            ('influencer_B', 'user_4'), ('influencer_C', 'user_6'),
            ('influencer_C', 'user_7'),
        ],
        'Instagram': [
            ('influencer_A', 'user_1'), ('influencer_A', 'user_2'),
            ('influencer_A', 'user_4'), ('influencer_B', 'user_5'),
            ('user_1', 'user_2'), ('user_2', 'user_3'),
            ('influencer_C', 'user_6'), ('influencer_C', 'user_8'),
        ],
    }
    
    for layer, connections in social_data.items():
        for user1, user2 in connections:
            network.add_edges([
                [user1, layer, user2, layer, 1.0]
            ], input_type="list")
    
    # === 2. Basic statistics ===
    print("=== Network Overview ===")
    network.basic_stats()
    
    # === 3. Cross-platform presence ===
    print("\n=== Cross-Platform Presence ===")
    unique_users = set()
    for node in network.get_nodes():
        unique_users.add(node[0])
    
    for user in sorted(unique_users):
        activity = mls.node_activity(network, user)
        platforms = activity * len(network.get_layers())
        if activity == 1.0:
            print(f"  {user}: present on ALL platforms")
        elif activity > 0.5:
            print(f"  {user}: present on {platforms:.0f}/3 platforms")
    
    # === 4. Platform-specific centrality ===
    print("\n=== Centrality by Platform ===")
    
    for platform in network.get_layers():
        layer_subnet = network.subnetwork([platform], subset_by="layers")
        G = layer_subnet.core_network
        
        # Compute degree centrality
        degree_cent = nx.degree_centrality(G)
        top_users = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:3]
        
        print(f"\n{platform} - Top 3 by degree:")
        for node, score in top_users:
            print(f"  {node[0]}: {score:.3f}")
    
    # === 5. Cross-platform influence (versatility) ===
    print("\n=== Cross-Platform Influencers (High Versatility) ===")
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    top_versatile = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for node, score in top_versatile:
        print(f"  {node}: {score:.4f}")
    
    # === 6. Layer similarity ===
    print("\n=== Platform Similarity ===")
    layers = list(network.get_layers())
    for i in range(len(layers)):
        for j in range(i+1, len(layers)):
            layer1, layer2 = str(layers[i]), str(layers[j])
            
            # Edge overlap
            overlap = mls.edge_overlap(network, layer1, layer2)
            
            # Jaccard similarity
            similarity = mls.layer_similarity(network, layer1, layer2, method='jaccard')
            
            print(f"  {layer1} vs {layer2}:")
            print(f"    Edge overlap: {overlap:.3f}")
            print(f"    Jaccard similarity: {similarity:.3f}")
    
    # === 7. Cross-platform community detection ===
    print("\n=== Cross-Platform Communities ===")
    
    # High coupling because we expect influencers to attract similar audiences
    partition = louvain_multilayer(
        network,
        gamma=1.0,
        omega=1.5,      # High coupling for cross-platform consistency
        random_state=42
    )
    
    num_communities = len(set(partition.values()))
    print(f"Detected {num_communities} cross-platform communities")
    
    # Analyze which users are in which community
    communities = {}
    for node, comm in partition.items():
        user = node[0]
        if comm not in communities:
            communities[comm] = set()
        communities[comm].add(user)
    
    print("\nCommunities (by unique users):")
    for comm_id, users in sorted(communities.items(), key=lambda x: len(x[1]), reverse=True):
        influencers = [u for u in users if 'influencer' in u]
        regular = [u for u in users if 'influencer' not in u]
        print(f"  Community {comm_id}: {len(influencers)} influencers, {len(regular)} regular users")
        print(f"    Influencers: {influencers}")
        print(f"    Sample users: {regular[:3]}")

**Interpretation:**

1. **Cross-platform influencers** (influencer_A, influencer_B) have high versatility, indicating they successfully maintain audiences across platforms. Platform-specific influencers (influencer_C) may have niche appeal.

2. **Platform similarity** shows how audiences overlap:
   
   * High Twitter-Instagram similarity suggests similar user bases
   * Lower YouTube overlap might indicate different content consumption patterns

3. **Communities** reveal audience segments:
   
   * Some communities cluster around specific influencers
   * Cross-platform communities suggest genuine fandom that follows across platforms

**Adapting to Your Data:**

1. Map user identities across platforms (use verified accounts, linked profiles, or username matching)
2. Consider using directed edges for asymmetric follow relationships
3. Add edge weights based on interaction strength (likes, comments, shares)
4. Include temporal layers to track audience evolution over time


Case Study 3: Multi-Modal Transportation Analysis
--------------------------------------------------

Urban Mobility and Resilience
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem Context:**

You're an urban transportation analyst studying a city's public transit system. You have network data for:

* **Metro/Subway:** High-capacity, fixed routes
* **Bus:** Lower capacity, more flexible routes
* **Bike-share:** Individual, first/last mile connections

You want to:

1. Identify multimodal hubs (stations serving multiple transport modes)
2. Analyze network resilience (what happens if a metro station closes?)
3. Find communities ("travel basins") that span transport modes

**Data Modeling Decisions:**

* **Node type:** Stations/stops (with geographic coordinates)
* **Layers:** One per transport mode (Metro, Bus, Bikeshare)
* **Edges:** Direct connections between stops (can walk/transfer)
* **Network type:** Multiplex with geographic coupling (same location = same node)

**Complete Code:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    import networkx as nx
    from collections import Counter
    
    # === 1. Create the transportation network ===
    network = multinet.multi_layer_network(network_type='multiplex')
    
    # Simulated city transport data
    # Stations are named by neighborhood/landmark
    transport_data = {
        'Metro': [
            ('Central', 'Financial'), ('Financial', 'Tech_Park'),
            ('Central', 'University'), ('University', 'Hospital'),
            ('Central', 'Shopping_Mall'), ('Shopping_Mall', 'Residential_North'),
        ],
        'Bus': [
            ('Central', 'Financial'), ('Financial', 'Residential_East'),
            ('Central', 'University'), ('University', 'Residential_South'),
            ('Central', 'Shopping_Mall'), ('Shopping_Mall', 'Residential_North'),
            ('Tech_Park', 'Residential_East'),  # Bus connects where metro doesn't
            ('Hospital', 'Residential_South'),
            ('Airport', 'Central'),  # Bus to airport
        ],
        'Bikeshare': [
            ('Central', 'Financial'), ('Financial', 'Tech_Park'),
            ('Central', 'University'), ('University', 'Residential_South'),
            ('Shopping_Mall', 'Residential_North'),
            ('Tech_Park', 'Coffee_District'),  # Bike-only area
            ('University', 'Student_Housing'),  # Bike-only connection
        ],
    }
    
    for mode, connections in transport_data.items():
        for stop1, stop2 in connections:
            network.add_edges([
                [stop1, mode, stop2, mode, 1.0]
            ], input_type="list")
    
    # === 2. Network overview ===
    print("=== Transportation Network Overview ===")
    network.basic_stats()
    
    # === 3. Multimodal hub identification ===
    print("\n=== Multimodal Hubs ===")
    unique_stations = set()
    for node in network.get_nodes():
        unique_stations.add(node[0])
    
    station_modes = {}
    for station in unique_stations:
        activity = mls.node_activity(network, station)
        num_modes = activity * len(network.get_layers())
        station_modes[station] = num_modes
    
    print("Stations by number of transport modes:")
    for station, modes in sorted(station_modes.items(), key=lambda x: x[1], reverse=True):
        mode_names = []
        for mode in network.get_layers():
            layer_subnet = network.subnetwork([mode], subset_by="layers")
            layer_nodes = [n[0] for n in layer_subnet.get_nodes()]
            if station in layer_nodes:
                mode_names.append(mode)
        
        if modes >= 2:
            print(f"  {station}: {modes:.0f} modes ({', '.join(mode_names)})")
    
    # === 4. Mode-specific analysis ===
    print("\n=== Transport Mode Characteristics ===")
    
    for mode in network.get_layers():
        layer_subnet = network.subnetwork([mode], subset_by="layers")
        G = layer_subnet.core_network
        
        num_stops = G.number_of_nodes()
        num_connections = G.number_of_edges()
        density = mls.layer_density(network, mode)
        
        # Find most connected stops
        degree_cent = nx.degree_centrality(G)
        top_stop = max(degree_cent.items(), key=lambda x: x[1])
        
        print(f"\n{mode}:")
        print(f"  Stops: {num_stops}")
        print(f"  Connections: {num_connections}")
        print(f"  Network density: {density:.3f}")
        print(f"  Most connected: {top_stop[0][0]} (degree={top_stop[1]:.2f})")
    
    # === 5. Resilience analysis: What if Central closes? ===
    print("\n=== Resilience Analysis: Central Station Failure ===")
    
    # Current connectivity
    G_full = network.core_network
    num_components_before = nx.number_connected_components(G_full.to_undirected())
    print(f"Before failure: {num_components_before} connected component(s)")
    
    # Simulate failure by removing Central from all layers
    G_after = G_full.copy()
    central_nodes = [n for n in G_after.nodes() if n[0] == 'Central']
    G_after.remove_nodes_from(central_nodes)
    
    num_components_after = nx.number_connected_components(G_after.to_undirected())
    print(f"After removing Central: {num_components_after} connected component(s)")
    
    # Which stations become disconnected?
    if num_components_after > 1:
        components = list(nx.connected_components(G_after.to_undirected()))
        print("\nResulting network fragments:")
        for i, comp in enumerate(sorted(components, key=len, reverse=True)):
            stations = set(n[0] for n in comp)
            print(f"  Fragment {i+1} ({len(stations)} stations): {stations}")
    
    # === 6. Travel basin detection ===
    print("\n=== Travel Basins (Communities) ===")
    
    # Moderate coupling: travel patterns may differ by mode
    partition = louvain_multilayer(
        network,
        gamma=1.0,
        omega=1.0,
        random_state=42
    )
    
    num_basins = len(set(partition.values()))
    print(f"Detected {num_basins} travel basins")
    
    # Group stations by basin
    basins = {}
    for node, basin in partition.items():
        station = node[0]
        if basin not in basins:
            basins[basin] = set()
        basins[basin].add(station)
    
    print("\nTravel basins:")
    for basin_id, stations in sorted(basins.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  Basin {basin_id}: {stations}")

**Interpretation:**

1. **Multimodal hubs** (Central, Financial, University) are critical infrastructure points where passengers transfer between modes. These should be prioritized for maintenance and security.

2. **Resilience analysis** reveals that Central is a critical node—its failure fragments the network. This suggests the need for redundant connections or alternative routes.

3. **Travel basins** correspond to geographic areas where people typically travel:
   
   * Downtown basin: Central, Financial, Shopping_Mall
   * University/Hospital basin: University, Hospital, Student_Housing
   * Residential basins: various residential areas with their nearest transit

**Adapting to Your Data:**

1. Include geographic distance as edge weight (travel time between stops)
2. Add passenger flow data to weight edges by usage
3. Include temporal layers (peak hours, off-peak, weekend)
4. Add inter-layer edges representing walking transfers between nearby stations


Case Study 4: Heterogeneous Academic Network
---------------------------------------------

Research Collaboration and Impact Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem Context:**

You're analyzing academic research patterns using data from publications. Your network includes:

* **Authors:** Researchers who write papers
* **Papers:** Research publications
* **Venues:** Conferences and journals where papers appear
* **Institutions:** Organizations where authors work

You want to:

1. Find influential authors (not just by citation count)
2. Identify research communities that span institutions
3. Discover emerging collaboration patterns

**Data Modeling Decisions:**

* **Node types:** Authors, Papers, Venues, Institutions (heterogeneous)
* **Edge types:** 
  * Author → Paper (authorship)
  * Paper → Venue (publication)
  * Author → Institution (affiliation)
* **Network type:** Heterogeneous Information Network (HIN)

**Complete Code:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    import networkx as nx
    from collections import Counter, defaultdict
    
    # === 1. Create the academic network ===
    network = multinet.multi_layer_network()
    
    # Academic publication data
    # In practice: load from DBLP, Semantic Scholar, or similar
    
    # Authors write papers
    authorship_data = [
        ('Dr_Smith', 'Paper_1'), ('Dr_Smith', 'Paper_2'),
        ('Dr_Jones', 'Paper_1'), ('Dr_Jones', 'Paper_3'),
        ('Dr_Chen', 'Paper_2'), ('Dr_Chen', 'Paper_4'),
        ('Dr_Kim', 'Paper_3'), ('Dr_Kim', 'Paper_4'),
        ('Dr_Garcia', 'Paper_5'), ('Dr_Lee', 'Paper_5'),
        ('Dr_Smith', 'Paper_6'), ('Dr_Lee', 'Paper_6'),  # Cross-institution collab
    ]
    
    # Papers published in venues
    publication_data = [
        ('Paper_1', 'ICML'), ('Paper_2', 'NeurIPS'),
        ('Paper_3', 'ICML'), ('Paper_4', 'NeurIPS'),
        ('Paper_5', 'AAAI'), ('Paper_6', 'ICML'),
    ]
    
    # Authors affiliated with institutions
    affiliation_data = [
        ('Dr_Smith', 'MIT'), ('Dr_Jones', 'MIT'),
        ('Dr_Chen', 'Stanford'), ('Dr_Kim', 'Stanford'),
        ('Dr_Garcia', 'Berkeley'), ('Dr_Lee', 'Berkeley'),
    ]
    
    # Add to network with explicit layer/type information
    for author, paper in authorship_data:
        network.add_edges([
            [author, 'authors', paper, 'papers', 1.0]
        ], input_type="list")
    
    for paper, venue in publication_data:
        network.add_edges([
            [paper, 'papers', venue, 'venues', 1.0]
        ], input_type="list")
    
    for author, institution in affiliation_data:
        network.add_edges([
            [author, 'authors', institution, 'institutions', 1.0]
        ], input_type="list")
    
    # === 2. Network overview ===
    print("=== Academic Network Overview ===")
    network.basic_stats()
    
    # === 3. Meta-path based analysis ===
    # Meta-path: Author → Paper → Venue → Paper → Author
    # This finds authors who publish in the same venues
    
    print("\n=== Meta-Path Analysis: Authors Publishing in Same Venues ===")
    
    G = network.core_network
    
    # Find which authors publish where
    author_venues = defaultdict(set)
    for author, paper in authorship_data:
        for p, venue in publication_data:
            if paper == p:
                author_venues[author].add(venue)
    
    print("Authors by venue:")
    venue_authors = defaultdict(list)
    for author, venues in author_venues.items():
        for venue in venues:
            venue_authors[venue].append(author)
    
    for venue, authors in sorted(venue_authors.items()):
        print(f"  {venue}: {authors}")
    
    # Find co-venue patterns (authors who could collaborate based on venue)
    print("\nPotential collaborators (same venues):")
    for venue, authors in venue_authors.items():
        if len(authors) >= 2:
            for i in range(len(authors)):
                for j in range(i+1, len(authors)):
                    print(f"  {authors[i]} -- {authors[j]} (both publish at {venue})")
    
    # === 4. Cross-institution collaboration analysis ===
    print("\n=== Cross-Institution Collaborations ===")
    
    # Find author affiliations
    author_institution = dict(affiliation_data)
    
    # Find collaborations (authors on same paper)
    collaborations = defaultdict(set)
    paper_authors = defaultdict(list)
    for author, paper in authorship_data:
        paper_authors[paper].append(author)
    
    cross_institution_collabs = []
    for paper, authors in paper_authors.items():
        if len(authors) >= 2:
            for i in range(len(authors)):
                for j in range(i+1, len(authors)):
                    a1, a2 = authors[i], authors[j]
                    inst1 = author_institution.get(a1, 'Unknown')
                    inst2 = author_institution.get(a2, 'Unknown')
                    if inst1 != inst2:
                        cross_institution_collabs.append((a1, a2, paper, inst1, inst2))
    
    print("Cross-institution collaborations:")
    for a1, a2, paper, inst1, inst2 in cross_institution_collabs:
        print(f"  {a1} ({inst1}) -- {a2} ({inst2}) on {paper}")
    
    # === 5. Author influence metrics ===
    print("\n=== Author Influence ===")
    
    # Count papers per author
    author_paper_count = Counter(a for a, p in authorship_data)
    
    # Count unique venues per author
    author_venue_count = {a: len(v) for a, v in author_venues.items()}
    
    # Count co-authors
    author_coauthors = defaultdict(set)
    for paper, authors in paper_authors.items():
        for author in authors:
            for coauthor in authors:
                if author != coauthor:
                    author_coauthors[author].add(coauthor)
    
    print("Author metrics:")
    print(f"{'Author':<15} {'Papers':<8} {'Venues':<8} {'Coauthors':<10}")
    print("-" * 45)
    
    all_authors = set(a for a, p in authorship_data)
    for author in sorted(all_authors):
        papers = author_paper_count.get(author, 0)
        venues = author_venue_count.get(author, 0)
        coauthors = len(author_coauthors.get(author, set()))
        print(f"{author:<15} {papers:<8} {venues:<8} {coauthors:<10}")
    
    # === 6. Institution collaboration network ===
    print("\n=== Institution Collaboration Network ===")
    
    # Build institution-level collaboration graph
    inst_collabs = Counter()
    for a1, a2, paper, inst1, inst2 in cross_institution_collabs:
        pair = tuple(sorted([inst1, inst2]))
        inst_collabs[pair] += 1
    
    print("Institution pairs by collaboration count:")
    for pair, count in inst_collabs.most_common():
        print(f"  {pair[0]} -- {pair[1]}: {count} joint papers")

**Interpretation:**

1. **Meta-path analysis** reveals implicit relationships—authors who publish at the same venues but haven't collaborated yet are potential future collaborators.

2. **Cross-institution collaborations** highlight knowledge transfer patterns. The Smith-Lee collaboration bridges MIT and Berkeley.

3. **Author influence** considers multiple factors beyond raw paper count:
   
   * Venue diversity (publishing at multiple top venues)
   * Collaboration breadth (working with many different people)
   * Cross-institution reach

**Adapting to Your Data:**

1. Load from academic databases (DBLP XML, Semantic Scholar API)
2. Add citation edges between papers for impact analysis
3. Include temporal information for trend analysis
4. Weight edges by author position (first author, corresponding author)


Adapting Case Studies to Your Domain
------------------------------------

General Adaptation Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Identify your entities** → These become node types or layers
2. **Identify your relationships** → These become edges
3. **Decide multiplex vs. heterogeneous:**
   
   * Same entities, different relationship types → Multiplex
   * Different entity types → Heterogeneous

4. **Map identifiers** → Ensure same entity has same ID across layers
5. **Choose appropriate metrics** based on your research questions
6. **Validate with domain knowledge** → Do results match expectations?

Data Loading Templates
~~~~~~~~~~~~~~~~~~~~~~~

**From CSV with explicit layers:**

.. code-block:: python

    import pandas as pd
    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    df = pd.read_csv('your_data.csv')
    # Expected columns: source, target, layer, weight
    
    for _, row in df.iterrows():
        network.add_edges([
            [row['source'], row['layer'], row['target'], row['layer'], row['weight']]
        ], input_type="list")

**From multiple files (one per layer):**

.. code-block:: python

    layer_files = {
        'layer1': 'layer1_edges.csv',
        'layer2': 'layer2_edges.csv',
        'layer3': 'layer3_edges.csv',
    }
    
    network = multinet.multi_layer_network()
    
    for layer_name, filepath in layer_files.items():
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            network.add_edges([
                [row['source'], layer_name, row['target'], layer_name, 1.0]
            ], input_type="list")

**From database:**

.. code-block:: python

    import sqlite3
    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    conn = sqlite3.connect('network.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT source, target, layer, weight FROM edges')
    for source, target, layer, weight in cursor.fetchall():
        network.add_edges([
            [source, layer, target, layer, weight]
        ], input_type="list")
    
    conn.close()

Further Reading
---------------

* :doc:`recipes_and_workflows` — More ready-to-use recipes
* :doc:`../concepts/multilayer_networks_101` — Conceptual foundations
* :doc:`community_detection` — Detailed community detection guide
* :doc:`statistics` — Complete statistics reference
* :doc:`../concepts/algorithm_landscape` — Algorithm selection guide

**Academic References:**

* Kivelä et al. (2014). "Multilayer networks." *Journal of Complex Networks*.
* De Domenico et al. (2015). "Ranking in interconnected multilayer networks." *Nature Communications*.
* Battiston et al. (2017). "The physics of higher-order interactions in complex systems." *Nature Physics*.
