Examples Documentation
======================

This section contains executable examples with their actual outputs captured from CI.

About This System
-----------------

**Examples-as-Tests-as-Docs Pipeline**

This documentation uses a hard 1:1 mapping system where:

* Every example is an executable Python script in ``examples/docs/``
* CI runs each example and captures its output to ``examples/docs_outputs/``
* The exact output shown here is what CI captured - no hand-written outputs
* If code changes cause output to diverge, CI fails and blocks the merge

**How It Works**

1. Developer writes a Python example in ``examples/docs/``
2. Run ``python scripts/generate_docs_outputs.py`` to capture outputs
3. Reference the output in RST using ``.. literalinclude::``
4. CI validates that outputs match and fails on divergence

**Adding New Examples**

To add a new example:

.. code-block:: bash

   # 1. Create example script
   vim examples/docs/03_my_example.py
   
   # 2. Generate outputs
   python scripts/generate_docs_outputs.py
   
   # 3. Reference in RST
   .. literalinclude:: ../examples/docs_outputs/03_my_example.txt
      :language: none
   
   # 4. Commit both code and outputs
   git add examples/docs/03_my_example.py examples/docs_outputs/
   git commit -m "Add example: my_example"

**Testing**

The system includes automated tests:

.. code-block:: bash

   # Run all example tests
   pytest tests/test_docs_examples.py -v
   
   # Validate outputs
   python scripts/validate_docs_outputs.py

Basic Network Query Example
---------------------------

This example demonstrates creating a simple multilayer network and querying it.

**Output:**

.. literalinclude:: ../examples/docs_outputs/01_basic_query.txt
   :language: none

**What this shows:**

* Creating a multilayer network
* Adding nodes and edges to multiple layers
* Computing node degrees using DSL queries
* Displaying network statistics

Community Detection Example
---------------------------

This example demonstrates running Louvain community detection on a multilayer network.

**Output:**

.. literalinclude:: ../examples/docs_outputs/02_community_detection.txt
   :language: none

**What this shows:**

* Creating a network with community structure
* Running multilayer Louvain algorithm
* Displaying detected communities
* Showing community membership for each node
