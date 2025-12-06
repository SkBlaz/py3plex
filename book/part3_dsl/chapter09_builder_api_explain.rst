The Builder API and Explain Plans
============================================

*TODO: Expand with examples from docfiles/user_guide/dsl.rst sections on builder API*

Builder Pattern and Fluent API
-------------------------------

[Explain chainable method pattern]

Method Chaining
~~~~~~~~~~~~~~~

[Examples of building queries incrementally]

Type Hints and IDE Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~

[Show autocompletion benefits]

EXPLAIN Mode
------------

Query Execution Plans
~~~~~~~~~~~~~~~~~~~~~

[Show how queries are parsed and planned]

.. code-block:: python

    from py3plex.dsl import Q
    
    # Get execution plan without running query
    plan = Q.nodes().where(degree__gt=5).explain()
    print(plan)

Complexity Estimates
~~~~~~~~~~~~~~~~~~~~

[Understand query performance]

Optimization Tips
~~~~~~~~~~~~~~~~~

[How to write efficient queries]

Advanced Builder Features
-------------------------

Parameterized Queries
~~~~~~~~~~~~~~~~~~~~~

[Safe parameter binding]

.. code-block:: python

    from py3plex.dsl import Q, Param
    
    # Parameterized query
    result = (
        Q.nodes()
         .where(degree__gt=Param('min_degree'))
         .execute(network, params={'min_degree': 5})
    )

Query Reuse
~~~~~~~~~~~

[Build queries once, execute multiple times]

Summary
-------

[Key points about builder API and explain]

*Source files:*
- docfiles/user_guide/dsl.rst (builder API sections)
- examples/network_analysis/example_dsl_builder_api.py
