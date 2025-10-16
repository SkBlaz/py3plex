*py3plex* - documentation
#########################

**py3plex** is a Python library for multilayer and heterogeneous network analysis.

GitHub: https://github.com/SkBlaz/Py3Plex

Installation
============

.. code:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

Quick Start
===========

**New to py3plex? Start with our 10-minute tutorial!**

See :doc:`10min_tutorial` for a comprehensive introduction.

See comprehensive examples in the `examples/ directory <https://github.com/SkBlaz/Py3Plex/tree/master/examples>`_.

Basic usage:

.. code:: python

    from py3plex.core import multinet
    
    # Load a network
    network = multinet.multi_layer_network().load_network(
        "data.edgelist", input_type="edgelist", directed=False)
    
    # Visualize
    network.visualize_network()

Documentation Structure
=======================

.. toctree::
   :maxdepth: 2
   :caption: Basic tutorial:

   10min_tutorial
   core_idea.rst
   basic_usage.rst
   basic_usage_analysis.rst
   basic_usage_analysis_multiplex.rst
   supra.rst
   visualization.rst
   acknowledgements.rst
   community_detection.rst
   learning.rst
   development.rst
  
.. toctree::
   :maxdepth: 2
   :caption: Further steps: learning:
			 
   learning2.rst
   learning3.rst		 

.. toctree::
   :maxdepth: 2
   :caption: API documentation:
			 
   apidocs.rst
   AUTOGEN_results/modules.rst
   
Examples & Tutorials
====================

**The best way to learn py3plex is through examples!**

**Getting Started:**

- :doc:`10min_tutorial` - **Start here!** A comprehensive 10-minute introduction to py3plex

**Core Examples:**

All examples are available at: https://github.com/SkBlaz/Py3Plex/tree/master/examples

Key examples:

- ``tutorial_10min.py`` - Executable version of the 10-minute tutorial
- ``example_multilayer_visualization.py`` - Network visualization
- ``example_community_detection.py`` - Community detection with Louvain and Infomap
- ``example_network_decomposition.py`` - Meta-path feature extraction
- ``example_n2v_embedding.py`` - Node2Vec embeddings
- ``example_label_propagation.py`` - Semi-supervised learning
- ``example_multiplex_dynamics.py`` - Temporal analysis

References
==========
 
* :ref:`genindex`
* :ref:`modindex`
