.. _gui-chapter:

GUI Overview: Where It Helps, Where It Does Not
================================================

The py3plex GUI is a convenience interface for interactive exploration. It is useful for rapid inspection and teaching workflows, but it should not be treated as a replacement for versioned analytical scripts.

.. admonition:: Status: Experimental
   :class: warning

   The GUI is intended for local or controlled environments. It is not a hardened public deployment target.

Appropriate Uses
----------------

* quick dataset inspection,
* exploratory layer browsing,
* demonstration and teaching,
* rapid hypothesis sketching before scripted analysis.

Inappropriate Uses
------------------

* sole source of publication-critical results,
* unversioned "click-through" analysis without provenance,
* security-sensitive internet-facing deployment.

Recommended Practice
--------------------

Use the GUI to discover questions, then transfer finalized analysis into scriptable py3plex workflows with explicit parameters, seeds, and exports.

This keeps interactive exploration and reproducible inference aligned rather than conflated.
