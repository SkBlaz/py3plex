.. _appendix-e:

Appendix E: Extended API and DSL Reference
==========================================

This appendix is lookup-oriented reference. Conceptual interpretation belongs in Chapters 9–11 and foundational semantics in Chapters 2–4.

Core API (Minimal Reference)
----------------------------

.. code-block:: python

    from py3plex.core import multinet
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([['A', 'social', 'B', 'social', 1]], input_type='list')
    layers = net.get_layers()

DSL Builder Quick Reference
---------------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    result = (
        Q.nodes()
         .from_layers(L['social'])
         .where(degree__gt=3)
         .compute('degree')
         .order_by('-degree')
         .limit(10)
         .execute(net)
    )

String DSL Quick Reference
--------------------------

.. code-block:: python

    from py3plex.dsl import execute_query
    execute_query(net, 'SELECT nodes WHERE layer="social" COMPUTE degree')

Common Measures
---------------

``degree``, ``betweenness_centrality``, ``closeness_centrality``, ``pagerank``, ``clustering``

Result Export
-------------

.. code-block:: python

    df = result.to_pandas()
    result.to_json()

CLI Hint
--------

.. code-block:: bash

    python -m py3plex --help

Reference Boundary Note
-----------------------

If semantics or claim interpretation is at stake, return to Chapters 2–4 and 9–11. This appendix intentionally omits methodological argument and focuses on navigable syntax lookup.
