.. _visualization-chapter:

Visualization as Diagnostic Analysis
====================================

Visualization in multilayer work is best used as a diagnostic instrument, not as proof by picture.

Analytical Purpose of Plots
---------------------------

Use visualization to test hypotheses about structure:

* Are layers genuinely distinct or mostly redundant?
* Are bridging nodes meaningful connectors or layout artifacts?
* Are inter-layer links interpretable under the domain model?

If the plot cannot answer one of these questions, it is likely decorative.

A Focused Workflow
------------------

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default

    layers, layer_graphs, positions = network.get_layers()
    # layers: layer-name list; layer_graphs: per-layer graph objects; positions: layout coordinates
    draw_multilayer_default((layers, layer_graphs, positions), display=False)

Implementation note: layout defaults are convenience choices. They are not statistical estimators.

Paired-Figure Diagnostic Concept
--------------------------------

Use two panels of the same network with different layout seeds. If a bridge narrative appears only in one seed, treat it as a layout-sensitive hypothesis, not a structural fact.

Common Analyst Failure Modes
----------------------------

1. **"Large node means key actor, ship it."**
   Often false when size encodes aggregate degree across incomparable layers.

2. **"Dense layer means stronger subsystem."**
   May reflect data collection bias, sampling intensity, or thresholding rules.

3. **"Clean visual split means true modularity."**
   May be a force-layout artifact with no robust metric support.

How to Make Plots More Trustworthy
----------------------------------

* annotate what is encoded by size, color, and edge opacity,
* compare at least two layout seeds for stability,
* pair visual claims with numeric checks (coverage, centrality summaries, modularity diagnostics),
* keep layer-specific and global plots side-by-side.

Plot-to-Metric Follow-Up Workflow
---------------------------------

If a plot suggests "Node X is a cross-layer broker," follow immediately with a numeric check (for example, per-layer betweenness plus coverage threshold) before making any interpretive claim.

When Not to Rely on Visualization
---------------------------------

For very large graphs, visual clutter makes node-level interpretation unreliable. Prefer summary statistics and targeted subgraph diagnostics.
Multilayer plots become actively misleading when edge density and overlap force occlusion that can fabricate apparent hubs or apparent separations not supported by underlying metrics.

Conclusion
----------

In this book, visualizations are exploratory and communicative aids. Claims should be grounded in reproducible computations, with plots used to expose potential structure and potential misunderstanding.
