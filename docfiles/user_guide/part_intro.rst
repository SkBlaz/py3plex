User Guide: From Understanding to Mastery
==========================================

*"Knowing is not enough; we must apply. Willing is not enough; we must do."* — Johann Wolfgang von Goethe

The Heart of the Documentation
------------------------------

This section is the practical core of the py3plex documentation. While Part I got you started and Part II built your conceptual foundation, Part III is where you develop real competence.

Each chapter in this section covers a major capability of py3plex. They're designed to be read in order the first time through, building on each other. After that, they serve as reference material you can return to for specific tasks.

Chapter Overview
----------------

**Working with Networks** covers the fundamental operations: creating networks, loading data, querying structure, extracting subnetworks. This is the foundation for everything else.

**Statistics** teaches you how to measure what matters. Layer density, node activity, edge overlap, versatility—these metrics quantify the multilayer structure of your data. Understanding what they measure (and don't measure) is essential for valid analysis.

**Community Detection** addresses one of the most common analysis tasks: finding groups of nodes that naturally cluster together. In multilayer networks, this is more complex than single-layer community detection, and the algorithms offer parameters you need to understand.

**Random Walks & Embeddings** covers techniques for turning network structure into features for machine learning. Random walks are also fundamental to many other algorithms, so understanding them opens doors to advanced methods.

**I/O and Formats** deals with the practical matter of getting data in and out of py3plex. Real-world data comes in many formats, and you often need to export results for other tools or collaborators.

**Visualization** teaches you to create visual representations of your networks. Good visualizations reveal patterns that statistics miss and are essential for communicating findings.

**DSL (Domain-Specific Language)** introduces py3plex's SQL-like query language. For interactive exploration and quick analysis, the DSL is often faster than writing Python code.

**Graph Operations** covers the dplyr-style chainable API for data transformations. This modern interface makes complex operations readable and composable.

**Recipes & Workflows** provides ready-to-use solutions for common tasks. When you need to accomplish something specific, check here first—we've probably already solved it.

**Case Studies** demonstrates complete analyses from start to finish. These are the most valuable chapters for understanding how to apply py3plex to real problems.

How to Use This Section
-----------------------

**If you're learning py3plex for the first time:**

Read the chapters in order. Each builds on concepts from previous chapters, and the examples often reference earlier material. Plan to work through the code examples—reading code is not the same as running it.

**If you're looking for a specific solution:**

Check the Recipes & Workflows chapter first. If your task isn't there, look in the relevant topical chapter (e.g., Community Detection for clustering problems).

**If you're deepening your expertise:**

The Case Studies chapter shows how experts approach real problems. Pay attention not just to what they do, but why they make specific choices.

A Philosophy of Practice
------------------------

We believe that proficiency comes from deliberate practice with feedback. This means:

1. **Run the code.** Don't just read it. Type it in (or copy-paste), run it, and look at the output.

2. **Modify and experiment.** After running an example, change something. What happens if you use a different parameter? A different algorithm? A different dataset?

3. **Apply to your own data.** The examples use sample data, but the goal is to apply these techniques to your own problems. Start with small subsets of your data and scale up.

4. **Reflect on what you learn.** When something surprises you, stop and understand why. These surprises are often where the deepest learning happens.

The Real-World Connection
-------------------------

Every technique in this section exists because it solves real problems. Community detection has helped researchers identify functional modules in protein interaction networks. Random walk embeddings have improved drug-drug interaction prediction. Visualization has revealed unexpected patterns in transportation networks.

As you work through these chapters, keep your own applications in mind. Ask yourself: How would I use this for my data? What questions could this help me answer?

Let's Go Deeper
---------------

Ready to develop real competence with py3plex? Start with :doc:`networks` to learn the fundamental operations.

.. note::

   **Progress Tracking:**
   
   As you work through this section, you might find it helpful to keep notes on:
   
   * Techniques you've tried and how they worked
   * Parameters that seem to work well for your data
   * Questions that arise (these are great topics for the Community Detection or Statistics chapters)
   * Ideas for your own analysis that you want to try later
