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
    draw_multilayer_default((layers, layer_graphs, positions), display=False)

Implementation note: layout defaults are convenience choices. They are not statistical estimators.

Common Misreadings
------------------

1. **Large central node = important actor**
   Often false when size encodes aggregate degree across incomparable layers.

2. **Dense layer = stronger system component**
   May reflect data collection bias or thresholding rules.

3. **Clean separation = true modularity**
   May be a force-layout artifact.

How to Make Plots More Trustworthy
----------------------------------

* annotate what is encoded by size, color, and edge opacity,
* compare at least two layout seeds for stability,
* pair visual claims with numeric checks (coverage, centrality summaries, modularity diagnostics),
* keep layer-specific and global plots side-by-side.

When Not to Rely on Visualization
---------------------------------

For very large graphs, visual clutter makes node-level interpretation unreliable. Prefer summary statistics and targeted subgraph diagnostics.

Conclusion
----------

In this book, visualizations are exploratory and communicative aids. Claims should be grounded in reproducible computations, with plots used to expose potential structure and potential misunderstanding.
