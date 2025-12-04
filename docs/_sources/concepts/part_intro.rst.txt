Concepts & Architecture: Understanding the Foundations
=======================================================

*"If you can't explain it simply, you don't understand it well enough."* — Albert Einstein

Why Theory Matters
------------------

You might be tempted to skip this section and jump straight to the practical guides. We understand—there's pressure to produce results quickly. But investing a few minutes in conceptual understanding will pay dividends in every analysis you do afterward.

Here's the truth: **most mistakes in multilayer network analysis come from modeling decisions, not from code errors.** Did you correctly identify what should be a layer? Did you set up the right kind of inter-layer coupling? Are you using metrics that make sense for your data type? These are the questions that separate good analysis from misleading results, and answering them requires understanding the concepts behind the tools.

What This Section Covers
------------------------

**Multilayer Networks 101** introduces the fundamental concepts. What distinguishes a multilayer network from a regular graph? When should you use one? What are the different types (multiplex, heterogeneous, temporal)? We use concrete examples to build intuition before introducing any formalism.

**The py3plex Core Model** explains how py3plex represents multilayer networks internally. Understanding this helps you work with the library more effectively and debug issues when they arise. We explain node-layer pairs, the supra-adjacency matrix, and how py3plex builds on NetworkX.

**Design Principles** describes the philosophy behind py3plex. Why was it designed the way it was? What trade-offs were made? This is particularly useful if you want to extend the library or understand why certain APIs work the way they do.

**The Algorithm Landscape** provides a map of available algorithms. Rather than an exhaustive reference (that's in Part VIII), this chapter helps you understand which algorithms exist, when to use them, and how they relate to each other.

The Payoff
----------

After reading this section, you'll be able to:

* Look at a real-world system and decide how to model it as a multilayer network
* Choose appropriate parameters for algorithms (like the inter-layer coupling strength)
* Interpret results correctly (understanding what metrics actually measure)
* Avoid common pitfalls (like accidentally flattening away important structure)
* Communicate your approach to collaborators

A Real Story
------------

Consider a researcher studying disease spread in a city. They have contact data from both public transportation and workplaces. They initially modeled this as a single network with edge weights (transportation contacts weighted lower, workplace contacts higher). Their epidemic simulations predicted faster spread than observed.

The problem? In reality, these two contact types operate differently. Workplace contacts are repeated daily; transportation contacts are typically one-time. The disease can only establish itself through repeated exposure. By flattening the network, they lost the temporal stability information that mattered for transmission dynamics.

When they remodeled as a multilayer network—with workplace contacts as one layer and transportation as another—they could apply layer-specific spreading dynamics. Their predictions matched the observed data much better.

This is the power of thinking in multilayer terms: **preserving distinctions that matter for your analysis.**

Moving Forward
--------------

If you're short on time, we recommend at least reading :doc:`multilayer_networks_101` before using py3plex. The other chapters can be consulted as needed.

If you're investing in becoming proficient with multilayer network analysis, read all chapters in order. They build on each other and provide a solid foundation for everything that follows.

.. tip::

   **Conceptual Checkpoint:**
   
   After reading this section, you should be able to answer:
   
   * What's the difference between multiplex and heterogeneous networks?
   * What does the supra-adjacency matrix represent?
   * When should you use high vs. low inter-layer coupling?
   * What information do you lose when you flatten a multilayer network?
