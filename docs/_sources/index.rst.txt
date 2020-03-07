*py3plex* - documentation
#########################

Found at: https://github.com/SkBlaz/Py3Plex

Welcome to the *py3plex* library's documentation! Here, user can learn more about how *py3plex* can be used to solve problems related to complex networks!

The aim of this library is to:

#. Provide primitives for working with multilayer (and multiplex) complex networks
#. Provide a core set of algorithm for statistical analysis of such networks
#. Provide extensive collection of network decomposition algorithms
#. Provide python wrappers for highly efficient algorithm implementations


.. code:: bash

    pip install py3plex

    
To test whether the core library functionality works well, you can run the test suite from the ./tests folder as::
  
  python3 -m pytest test_core_functionality.py
    
That's almost it. For full functionality, one needs node2vec and InfoMap binary files, which need to be put into the ./bin folder. This project offers pre-compiled versions, however was tested only on Ubuntu linux > 15.
    
A quick overview is discussed next:

.. toctree::
   :maxdepth: 2
   :caption: Basic tutorial:

   core_idea.rst
   basic_usage.rst
   basic_usage_analysis.rst
   basic_usage_analysis_multiplex.rst
   supra.rst
   visualization.rst
   acknowledgements.rst
   community_detection.rst
   supra.rst
   learning.rst
  
.. toctree::
   :maxdepth: 2
   :caption: Further steps: learning:
			 
   learning2.rst
   learning3.rst
   
All examples and tutorials are accessible here: _a link: https://github.com/SkBlaz/Py3Plex/tree/master/examples

**In progress: We are adding more involved examples, which are for now found in ./examples folder!**

The documentation of all methods is given below:

More detailed overview
==================
 
* :ref:`genindex`
* :ref:`modindex`

.. toctree::
   :maxdepth: 2
