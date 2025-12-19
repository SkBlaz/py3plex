Citation and References
=======================

If you use py3plex in your research, please **cite our work**. The primary journal article is the recommended citation for the toolkit. When you rely on a specific algorithm implementation, add the corresponding original paper below.

Primary Citation
----------------

**Recommended citation for py3plex:**

.. code-block:: bibtex

    @Article{Skrlj2019,
      author    = {{\v{S}}krlj, Bla{\v{z}} and Kralj, Jan and Lavra{\v{c}}, Nada},
      title     = {Py3plex toolkit for visualization and analysis of multilayer networks},
      journal   = {Applied Network Science},
      year      = {2019},
      volume    = {4},
      number    = {1},
      pages     = {94},
      doi       = {10.1007/s41109-019-0203-7},
      url       = {https://doi.org/10.1007/s41109-019-0203-7}
    }

**Plain text for copy/paste:**

  Škrlj, B., Kralj, J., & Lavrač, N. (2019). Py3plex toolkit for visualization and analysis of multilayer networks. *Applied Network Science*, 4(1), 94. https://doi.org/10.1007/s41109-019-0203-7

Conference Paper
----------------

For the **initial algorithmic work** and overall system description:

.. code-block:: bibtex

    @InProceedings{Skrlj2019Conference,
      author    = {{\v{S}}krlj, Bla{\v{z}} and Kralj, Jan and Lavra{\v{c}}, Nada},
      editor    = {Aiello, Luca Maria and Cherifi, Chantal and Cherifi, Hocine 
                   and Lambiotte, Renaud and Li{\'o}, Pietro and Rocha, Luis M.},
      title     = {Py3plex: A Library for Scalable Multilayer Network Analysis and Visualization},
      booktitle = {Complex Networks and Their Applications VII},
      year      = {2019},
      publisher = {Springer International Publishing},
      address   = {Cham},
      pages     = {757--768},
      isbn      = {978-3-030-05411-3},
      doi       = {10.1007/978-3-030-05411-3_60}
    }

Algorithm-Specific Citations
-----------------------------

When using **specific algorithms**, please also cite the **original papers** that introduced them. Match the citation to the algorithm you invoked in your workflow.

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

Use this for multilayer modularity-based community detection (:mod:`py3plex.algorithms.community_detection.multilayer_modularity`).

.. code-block:: bibtex

    @Article{Mucha2010,
      author  = {Mucha, Peter J. and Richardson, Thomas and Macon, Kevin 
                 and Porter, Mason A. and Onnela, Jukka-Pekka},
      title   = {Community structure in time-dependent, multiscale, and multiplex networks},
      journal = {Science},
      year    = {2010},
      volume  = {328},
      number  = {5980},
      pages   = {876--878},
      doi     = {10.1126/science.1184819}
    }

Node2Vec
~~~~~~~~

Random-walk-based node embedding used by :mod:`py3plex.wrappers.node2vec_embedding` and related utilities.

.. code-block:: bibtex

    @InProceedings{Grover2016,
      author    = {Grover, Aditya and Leskovec, Jure},
      title     = {node2vec: Scalable Feature Learning for Networks},
      booktitle = {Proceedings of the 22nd ACM SIGKDD International Conference 
                   on Knowledge Discovery and Data Mining},
      year      = {2016},
      pages     = {855--864},
      doi       = {10.1145/2939672.2939754}
    }

Louvain Algorithm
~~~~~~~~~~~~~~~~~

Greedy modularity optimization for single- and multi-layer community detection.

.. code-block:: bibtex

    @Article{Blondel2008,
      author  = {Blondel, Vincent D. and Guillaume, Jean-Loup and Lambiotte, Renaud 
                 and Lefebvre, Etienne},
      title   = {Fast unfolding of communities in large networks},
      journal = {Journal of Statistical Mechanics: Theory and Experiment},
      year    = {2008},
      volume  = {2008},
      number  = {10},
      pages   = {P10008},
      doi     = {10.1088/1742-5468/2008/10/P10008}
    }

Infomap
~~~~~~~

Information-theoretic community detection based on random walks.

.. code-block:: bibtex

    @Article{Rosvall2008,
      author  = {Rosvall, Martin and Bergstrom, Carl T.},
      title   = {Maps of random walks on complex networks reveal community structure},
      journal = {Proceedings of the National Academy of Sciences},
      year    = {2008},
      volume  = {105},
      number  = {4},
      pages   = {1118--1123},
      doi     = {10.1073/pnas.0706851105}
    }

MultiXRank
~~~~~~~~~~

Multilayer random walk with restart used for ranking and recommendation tasks.

.. code-block:: bibtex

    @Article{Baptista2022,
      author  = {Baptista, Anthony and Gonzalez, Aur{\'e}lien and Baudot, Ana{\"\i}s},
      title   = {Universal multilayer network exploration by random walk with restart},
      journal = {Communications Physics},
      year    = {2022},
      volume  = {5},
      number  = {1},
      pages   = {170},
      doi     = {10.1038/s42005-022-00937-9}
    }

DeepWalk
~~~~~~~~

Uniform random-walk embeddings that predate Node2Vec.

.. code-block:: bibtex

    @InProceedings{Perozzi2014,
      author    = {Perozzi, Bryan and Al-Rfou, Rami and Skiena, Steven},
      title     = {DeepWalk: Online Learning of Social Representations},
      booktitle = {Proceedings of the 20th ACM SIGKDD International Conference 
                   on Knowledge Discovery and Data Mining},
      year      = {2014},
      pages     = {701--710},
      doi       = {10.1145/2623330.2623732}
    }

Multilayer Network Theory
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Foundational papers** on multilayer networks and their mathematical formulation:

.. code-block:: bibtex

    @Article{Kivela2014,
      author  = {Kivel{\"a}, Mikko and Arenas, Alex and Barthelemy, Marc 
                 and Gleeson, James P. and Moreno, Yamir and Porter, Mason A.},
      title   = {Multilayer networks},
      journal = {Journal of Complex Networks},
      year    = {2014},
      volume  = {2},
      number  = {3},
      pages   = {203--271},
      doi     = {10.1093/comnet/cnu016}
    }

.. code-block:: bibtex

    @Article{Boccaletti2014,
      author  = {Boccaletti, Stefano and Bianconi, Ginestra and Criado, Regino 
                 and del Genio, Charo I. and G{\'o}mez-Garde{\~n}es, Jes{\'u}s 
                 and Romance, Miguel and Sendi{\~n}a-Nadal, Irene and Wang, Zhen 
                 and Zanin, Massimiliano},
      title   = {The structure and dynamics of multilayer networks},
      journal = {Physics Reports},
      year    = {2014},
      volume  = {544},
      number  = {1},
      pages   = {1--122},
      doi     = {10.1016/j.physrep.2014.07.001}
    }

.. code-block:: bibtex

    @Article{DeDomenico2013,
      author  = {De Domenico, Manlio and Sol{\'e}-Ribalta, Albert and Cozzo, Emanuele 
                 and Kivel{\"a}, Mikko and Moreno, Yamir and Porter, Mason A. 
                 and G{\'o}mez, Sergio and Arenas, Alex},
      title   = {Mathematical formulation of multilayer networks},
      journal = {Physical Review X},
      year    = {2013},
      volume  = {3},
      number  = {4},
      pages   = {041022},
      doi     = {10.1103/PhysRevX.3.041022}
    }

Complete Citation List
----------------------

For a full list of algorithm-specific citations, see the :doc:`../algorithm_guide`, which includes the major algorithms with their original references and DOIs.

Acknowledgments
---------------

Development and Contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

py3plex is developed and maintained by:

* **Blaž Škrlj** (lead developer) - Jožef Stefan Institute, Ljubljana, Slovenia
* **Jan Kralj** (contributor) - Jožef Stefan Institute
* **Nada Lavrač** (contributor) - Jožef Stefan Institute

Funding and Support
~~~~~~~~~~~~~~~~~~~

This work has been **supported by**:

* **Jožef Stefan Institute**, Ljubljana, Slovenia
* **Slovenian Research Agency** (research program P2-0103)

External Libraries
~~~~~~~~~~~~~~~~~~

py3plex builds upon **excellent open-source libraries**:

* **NetworkX** - Graph data structures and algorithms
* **NumPy** - Numerical computing
* **SciPy** - Scientific computing
* **Matplotlib** - Visualization
* **scikit-learn** - Machine learning utilities

Community Acknowledgments
~~~~~~~~~~~~~~~~~~~~~~~~~

We thank all contributors, users, and the broader network science community for their support, feedback, and contributions.

Special thanks to contributors who have submitted pull requests, reported issues, or provided feedback.

License Information
-------------------

py3plex is released under the **MIT License**.

.. code-block:: text

    MIT License
    
    Copyright (c) 2019-2025 Blaž Škrlj, Jan Kralj, Nada Lavrač
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

**Note:** Some bundled algorithms may have **different licenses**:

* Infomap community detection code: **AGPLv3**
* Louvain community detection: **BSD-3-Clause**

See ``LICENSE`` file in the repository for detailed license compatibility information.

Contact
-------

For questions about citing py3plex or collaboration opportunities:

* **Email:** blaz.skrlj@ijs.si
* **GitHub:** https://github.com/SkBlaz/py3plex
* **Issues:** https://github.com/SkBlaz/py3plex/issues

Related Work
------------

Other tools and libraries for multilayer network analysis:

* **muxViz** - Multilayer network visualization (R)
* **pymnet** - Multilayer networks in Python
* **multinet** - R package for multilayer networks
* **graphistry** - GPU-accelerated graph visualization

For a comprehensive comparison and positioning of py3plex, see the original publication.

Usage in Publications
---------------------

If you've used py3plex in your research and would like to be listed here, please:

1. Open an issue or pull request
2. Provide citation to your paper
3. Brief description of how py3plex was used

We maintain a list of publications using py3plex to showcase applications and build community.

See Also
--------

* :doc:`acknowledgements` - Full acknowledgments
* :doc:`../algorithm_guide` - Complete algorithm citations with references
* `py3plex GitHub <https://github.com/SkBlaz/py3plex>`_ - Source code and issues
* `Applied Network Science paper <https://doi.org/10.1007/s41109-019-0203-7>`_ - Primary publication
