Appendix D: Error Handling and Exception Hierarchy
===================================================

This appendix is a practical reference for the exceptions analysts hit most often.

Hierarchy at a Glance
---------------------

.. code-block:: text

    Py3plexException
    ├── Validation / input errors
    ├── I/O and serialization errors
    ├── DSL query errors
    ├── Algorithm execution/convergence errors
    └── Configuration errors

High-Frequency Exceptions in Workflow Practice
----------------------------------------------

* **InvalidLayerError / UnknownLayerError**  
  Usually indicates schema mismatch or layer-label drift at load time.

* **QuerySyntaxError / DslSyntaxError**  
  Indicates malformed DSL expressions or invalid builder chaining.

* **QueryExecutionError / DslExecutionError**  
  Indicates runtime mismatch (missing metric, unsupported operation, grouping misuse).

* **SerializationError / FileFormatError**  
  Indicates import/export mismatch or malformed files.

* **ConvergenceError**  
  Indicates iterative algorithms did not stabilize under provided settings.

Workflow-Review Use
-------------------

Exception categories help distinguish software faults from methodological faults. A layer-name error suggests data/schema review; a grouping misuse error suggests query-design review; a convergence error suggests algorithm/parameter sensitivity review.

Minimal Handling Pattern
------------------------

.. code-block:: python

    from py3plex.exceptions import Py3plexException

    try:
        result = run_analysis(network)
    except Py3plexException as e:
        # Log context, then route to data/query/algorithm review
        print(f"py3plex workflow error: {e}")

For pedagogical DSL error examples and recovery patterns, see Chapters 9–11.
