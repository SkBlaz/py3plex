.. _gui-chapter:

GUI Overview: Where It Helps, Where It Does Not
================================================

The py3plex GUI is a convenience interface for interactive exploration, useful for rapid inspection and teaching workflows. It should not replace versioned analytical scripts.

.. admonition:: Status: Experimental
   :class: warning

   The GUI is intended for local or controlled environments. It is not a hardened public deployment target.

Appropriate Uses
----------------

* quick dataset inspection,
* exploratory layer browsing,
* demonstration and teaching,
* rapid hypothesis sketching before scripted analysis.

One Short Interaction Flow
--------------------------

1. Load a multilayer dataset and inspect layer coverage in the GUI.
2. Run a quick centrality ranking to spot candidate bridge nodes.
3. Export the selected query/configuration and rerun the claim-bearing analysis in a versioned script.

Inappropriate Uses
------------------

* sole source of publication-critical results,
* unversioned "click-through" analysis without provenance,
* security-sensitive internet-facing deployment.

GUI-to-Script Handoff Example
-----------------------------

If the GUI suggests a candidate query such as "top 20 nodes by degree in social and work layers," reproduce it in code (for example, ``Q.nodes().from_layers(L['social'] + L['work']).compute('degree').order_by('-degree').limit(20)``) and commit that script with explicit seeds and exports.

What "Experimental" Means Operationally
---------------------------------------

Here, "experimental" means all three: unstable interface expectations over releases, incomplete provenance capture relative to scripted workflows, and higher deployment risk outside controlled environments.

Recommended Practice
--------------------

Use the GUI to discover questions, then transfer finalized analysis into scriptable py3plex workflows with explicit parameters, seeds, and exports.

This keeps interactive exploration and reproducible inference aligned rather than conflated.

Recommendation Matrix
---------------------

* **Use GUI for:** exploratory inspection, teaching demos, quick visual hypothesis generation.
* **Do not use GUI for:** final publication-grade inference, untracked parameter exploration, or public deployment without additional hardening and audit controls.
