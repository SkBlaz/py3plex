Case Study 2 — Biological Multilayer Network
========================================================

.. admonition:: Case Study Template
   :class: note

   This case study demonstrates a complete workflow for biological multilayer network 
   analysis. The methodology and code patterns are production-ready and applicable to 
   real datasets. Examples use representative synthetic data to illustrate the analysis 
   pipeline while protecting proprietary biological data.

Domain Context
--------------

Biological systems exhibit multilayer structure through different interaction types:

* **Protein-protein interactions** — Physical binding
* **Regulatory relationships** — Gene expression control
* **Metabolic pathways** — Enzyme-substrate relationships
* **Co-expression networks** — Correlated expression across conditions

A **biological multiplex network** represents these different interaction mechanisms as separate layers while capturing the same entities (genes/proteins) across layers.

**Research questions:**

1. How do protein functions differ across interaction types?
2. Which genes are central in regulation but peripheral in metabolism?
3. Do communities reflect functional modules consistently across layers?
4. How do dynamics (e.g., epidemic-like spreading) differ by interaction type?

Dataset Structure (Template)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Example dataset:** Multi-omic interaction network

* **Nodes:** ~2,000 genes/proteins
* **Layers:** Physical interaction, regulatory, metabolic
* **Edges:** ~10,000 interactions across layers
* **Attributes:** GO terms, tissue specificity, expression levels
* **Focus:** Dynamics simulation and layer-specific analysis

**Data format:**

.. code-block:: text

    # Format: gene_A, interaction_type, gene_B, interaction_type, confidence
    BRCA1, protein_interaction, TP53, protein_interaction, 0.95
    BRCA1, regulation, ATM, regulation, 0.87
    TP53, metabolic, MDM2, metabolic, 0.92

Loading and Preprocessing
--------------------------

Create and Load Network
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Create biological multilayer network
    network = multinet.multi_layer_network(directed=True)  # Regulation is directed
    
    # Load from biological database format
    network.load_network('biological_multiplex.edgelist', input_type='edgelist')
    
    # Add gene annotations (GO terms, etc.)
    # annotations = load_annotations('gene_annotations.tsv')
    # for node in network.get_nodes():
    #     network.core_network.nodes[node]['GO_terms'] = annotations.get(node[0], [])
    
    print(f"Loaded {network.number_of_nodes()} genes")
    print(f"Layers: {network.get_layers()}")

Analysis Pipeline Sketch
------------------------

Step 1: Network Topology
~~~~~~~~~~~~~~~~~~~~~~~~

Analyze structural properties of each interaction layer:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Compare topology across interaction types
    for layer in ["protein_interaction", "regulation", "metabolic"]:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", "clustering")
             .execute(network)
        )
        df = result.to_pandas()
        print(f"{layer}: avg degree = {df['degree'].mean():.2f}, "
              f"avg clustering = {df['clustering'].mean():.3f}")

**Expected patterns:**

* Protein interaction: High clustering (modules)
* Regulation: Lower clustering (hierarchical)
* Metabolic: Medium clustering (pathways)

Step 2: Dynamics Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Model information spreading or cascade dynamics using SIR model:

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    
    # Simulate disease/perturbation spreading
    sir = SIRDynamics(
        network,
        beta=0.3,      # Transmission rate
        gamma=0.1,     # Recovery rate
        initial_infected=0.05  # Start with 5% infected
    )
    sir.set_seed(42)
    
    results = sir.run(steps=100)
    
    # Analyze outbreak size
    final_recovered = results.get_measure("state_counts")['R'][-1]
    print(f"Final outbreak size: {final_recovered / network.number_of_nodes():.1%}")

**Research question:** How does perturbation spread differently through physical vs. regulatory interactions?

Step 3: Layer-Specific Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Identify genes that are central in one layer but not others:

.. code-block:: python

    # Find regulatory hubs
    regulatory_hubs = (
        Q.nodes()
         .from_layers(L["regulation"])
         .where(degree__gt=20)
         .compute("betweenness_centrality")
         .execute(network)
    )
    
    # Find protein interaction hubs
    ppi_hubs = (
        Q.nodes()
         .from_layers(L["protein_interaction"])
         .where(degree__gt=20)
         .compute("betweenness_centrality")
         .execute(network)
    )
    
    # Compare overlap
    reg_hub_ids = set(regulatory_hubs.node_ids)
    ppi_hub_ids = set(ppi_hubs.node_ids)
    
    overlap = reg_hub_ids & ppi_hub_ids
    reg_only = reg_hub_ids - ppi_hub_ids
    ppi_only = ppi_hub_ids - reg_hub_ids
    
    print(f"Overlap: {len(overlap)} genes")
    print(f"Regulatory only: {len(reg_only)} genes")
    print(f"PPI only: {len(ppi_only)} genes")

Step 4: Intervention Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simulate what-if scenarios: node removal, layer removal:

.. code-block:: python

    import copy
    
    # Baseline dynamics
    baseline_sir = SIRDynamics(network, beta=0.3, gamma=0.1)
    baseline_sir.set_seed(42)
    baseline_results = baseline_sir.run(steps=100)
    baseline_outbreak = baseline_results.get_measure("state_counts")['R'][-1]
    
    # Intervention: Remove top hub
    network_intervened = copy.deepcopy(network)
    top_hub = regulatory_hubs.node_ids[0]
    network_intervened.core_network.remove_node(top_hub)
    
    # Dynamics after intervention
    intervened_sir = SIRDynamics(network_intervened, beta=0.3, gamma=0.1)
    intervened_sir.set_seed(42)
    intervened_results = intervened_sir.run(steps=100)
    intervened_outbreak = intervened_results.get_measure("state_counts")['R'][-1]
    
    reduction = (baseline_outbreak - intervened_outbreak) / baseline_outbreak
    print(f"Outbreak reduced by {reduction:.1%} after removing hub")

Key Findings (Template)
------------------------

Spreading Patterns
~~~~~~~~~~~~~~~~~~

**Expected observation:** Cascade dynamics depend on layer structure

* **Protein interaction layer:** Slow, localized spreading (high clustering)
* **Regulatory layer:** Fast, global spreading (low clustering, directed)
* **Metabolic layer:** Intermediate spreading

**Interpretation:** Regulatory interactions enable rapid perturbation propagation

Layer Interactions
~~~~~~~~~~~~~~~~~~

**Expected observation:** Cross-layer hub genes

* Genes highly central in both protein interaction and regulation
* These genes are critical: removing them has amplified impact
* Potential drug targets or disease genes

Summary
-------

This case study template demonstrates:

1. **Biological network loading** with proper directionality
2. **Layer-specific topology** analysis
3. **Dynamics simulation** (SIR model for perturbation spreading)
4. **Intervention analysis** (what-if scenarios)
5. **Cross-layer hub identification**

**To complete this case study:**

1. Obtain biological multiplex dataset (e.g., STRING + RegulonDB + KEGG)
2. Add gene annotations (GO terms, pathways)
3. Run analysis pipeline
4. Validate findings against known biology
5. Visualize with annotations

**Relevant examples:**

* ``examples/dynamics/example_sir_model.py`` — SIR dynamics
* ``examples/network_analysis/example_multilayer_centrality.py`` — Centrality analysis
* ``docfiles/sir_epidemic_simulator.rst`` — SIR documentation
