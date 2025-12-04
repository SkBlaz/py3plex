Examples: Learning by Doing
===========================

*"Tell me and I forget. Teach me and I remember. Involve me and I learn."* — Benjamin Franklin

The Power of Examples
---------------------

If you've read other sections of this documentation, you've seen explanations of concepts and descriptions of APIs. But there's no substitute for seeing complete, working code that solves real problems.

This section provides curated examples that demonstrate py3plex's capabilities across various use cases. Each example is:

* **Complete:** You can run it from start to finish without modification
* **Annotated:** Comments explain not just what the code does, but why
* **Practical:** Based on real analysis patterns, not toy demonstrations
* **Progressive:** Examples build in complexity, from simple to advanced

How to Use These Examples
-------------------------

**As learning material:** Work through examples in order to build skills progressively. Type the code rather than copying—the mechanical process aids learning.

**As templates:** When you face a real problem, find an example that's similar and adapt it. Starting from working code is faster than starting from scratch.

**As references:** When you need to remember how to do something specific, the examples serve as quick reminders.

**As validation:** Running examples on your installation helps verify that everything is working correctly.

What You'll Find
----------------

The examples cover:

* **Network creation and loading** — Multiple ways to get data into py3plex
* **Statistical analysis** — Computing and interpreting multilayer metrics
* **Community detection** — Finding structure in your networks
* **Visualization** — Creating publication-ready figures
* **Random walks and embeddings** — Feature extraction for machine learning
* **Complete workflows** — End-to-end analyses that combine multiple techniques

Example Organization
--------------------

Examples are organized by topic and complexity:

**Beginner examples** introduce core concepts with small, simple networks. These are ideal for learning the basics.

**Intermediate examples** tackle more realistic scenarios with larger networks and combined techniques.

**Advanced examples** demonstrate sophisticated analyses, including performance optimization and custom extensions.

From Example to Application
---------------------------

The goal of examples is not to collect code, but to develop problem-solving ability. As you work through examples, ask yourself:

* What would I change to apply this to my data?
* What assumptions does this example make that might not hold for my case?
* What other questions could this technique help me answer?

This reflective practice transforms examples from isolated code snippets into reusable patterns.

Getting Started
---------------

Browse the :doc:`index` to find examples relevant to your interests, or work through them in order for a structured learning experience.

.. note::

   **Running the Examples:**
   
   All examples assume py3plex is installed. Some examples require optional dependencies—check the imports at the top of each example.
   
   If an example fails with an ImportError, install the missing package:
   
   .. code-block:: bash
   
       pip install <missing-package>
   
   Common optional dependencies include:
   
   * ``matplotlib`` for visualization
   * ``gensim`` for embeddings
   * ``python-louvain`` for community detection
   * ``sklearn`` for machine learning examples
