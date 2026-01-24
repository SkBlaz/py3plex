Examples Documentation
=====================

This section contains executable examples with their actual outputs captured from CI.

Basic Network Query Example
---------------------------

This example demonstrates creating a simple multilayer network and querying it.

**Source code:**

.. literalinclude:: ../examples/docs/01_basic_query.py
   :language: python
   :lines: 1-30
   :linenos:

**Output:**

.. literalinclude:: ../examples/docs_outputs/01_basic_query.txt
   :language: none

**What this shows:**

* Creating a multilayer network
* Adding nodes and edges to multiple layers
* Computing node degrees using DSL queries
* Displaying network statistics

The output above is automatically captured from running the example in CI. If the output changes, CI will regenerate it and validation will ensure documentation stays up to date.
