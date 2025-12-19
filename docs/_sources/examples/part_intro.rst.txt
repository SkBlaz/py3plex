Examples
========

Complete, runnable code examples for common py3plex workflows. Every script lives under ``examples/`` and mirrors the categories listed in :doc:`index`.

Each example is:

* **Complete** — Runs from start to finish without modification
* **Annotated** — Explains what the code does and why
* **Practical** — Based on real analysis patterns

**Topics covered**

* Network creation and loading
* Statistical analysis
* Community detection
* Visualization
* Random walks and embeddings
* Complete end-to-end workflows

How to Use
----------

* **Learn:** Start with the simplest scripts, then progress to full pipelines.
* **Adapt:** Copy the closest example and swap in your data or parameters.
* **Refer:** Jump to a specific topic when you need a quick reminder.
* **Validate:** Run an example after installing py3plex to confirm your setup.

Run scripts from the repository root with your virtual environment activated so relative paths resolve correctly:

.. code-block:: bash

   python examples/<category>/<filename>.py

See the :doc:`index` for a full listing.

.. note::

   All examples require py3plex to be installed. Some need optional dependencies—check imports at the top of each example and install as needed.

   Common optional dependencies:

   * ``matplotlib`` — Visualization
   * ``gensim`` — Embeddings
   * ``python-louvain`` — Community detection
   * ``sklearn`` — Machine learning
