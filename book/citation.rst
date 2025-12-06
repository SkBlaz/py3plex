Citation Information
====================

How to Cite Py3plex
-------------------

If you use py3plex in your research, please cite the following paper:

BibTeX
~~~~~~

.. code-block:: bibtex

    @Article{Skrlj2019,
      author={Skrlj, Blaz and Kralj, Jan and Lavrac, Nada},
      title={Py3plex toolkit for visualization and analysis of multilayer networks},
      journal={Applied Network Science},
      year={2019},
      volume={4},
      number={1},
      pages={94},
      doi={10.1007/s41109-019-0203-7},
      url={https://doi.org/10.1007/s41109-019-0203-7}
    }

For conference proceedings, you may also cite:

.. code-block:: bibtex

    @InProceedings{Skrlj2019b,
      author="{\v{S}}krlj, Bla{\v{z}}
      and Kralj, Jan
      and Lavra{\v{c}}, Nada",
      editor="Aiello, Luca Maria
      and Cherifi, Chantal
      and Cherifi, Hocine
      and Lambiotte, Renaud
      and Li{\'o}, Pietro
      and Rocha, Luis M.",
      title="Py3plex: A Library for Scalable Multilayer Network Analysis and Visualization",
      booktitle="Complex Networks and Their Applications VII",
      year="2019",
      publisher="Springer International Publishing",
      address="Cham",
      pages="757--768",
      isbn="978-3-030-05411-3",
      doi="10.1007/978-3-030-05411-3_60"
    }

APA Style
~~~~~~~~~

Škrlj, B., Kralj, J., & Lavrač, N. (2019). Py3plex toolkit for visualization and analysis of multilayer networks. *Applied Network Science*, *4*(1), 94. https://doi.org/10.1007/s41109-019-0203-7

MLA Style
~~~~~~~~~

Škrlj, Blaz, Jan Kralj, and Nada Lavrač. "Py3plex toolkit for visualization and analysis of multilayer networks." *Applied Network Science* 4.1 (2019): 94.

Chicago Style
~~~~~~~~~~~~~

Škrlj, Blaz, Jan Kralj, and Nada Lavrač. "Py3plex toolkit for visualization and analysis of multilayer networks." *Applied Network Science* 4, no. 1 (2019): 94.

Citing This Book
----------------

If you specifically reference this book (rather than the software), please cite:

.. code-block:: text

    Škrlj, B. (2025). *Practical Multilayer Network Analysis with Py3plex* (Version 1.0).
    Available at: https://github.com/SkBlaz/py3plex

BibTeX for This Book
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bibtex

    @book{Skrlj2025book,
      author = {Škrlj, Blaž},
      title = {Practical Multilayer Network Analysis with Py3plex},
      year = {2025},
      version = {1.0},
      url = {https://github.com/SkBlaz/py3plex}
    }

Citing Specific Algorithms
--------------------------

If you use specific algorithms implemented in py3plex, consider citing the original papers:

Louvain Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bibtex

    @article{Blondel2008,
      title={Fast unfolding of communities in large networks},
      author={Blondel, Vincent D and Guillaume, Jean-Loup and Lambiotte, Renaud and Lefebvre, Etienne},
      journal={Journal of statistical mechanics: theory and experiment},
      volume={2008},
      number={10},
      pages={P10008},
      year={2008}
    }

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bibtex

    @article{Mucha2010,
      title={Community structure in time-dependent, multiscale, and multiplex networks},
      author={Mucha, Peter J and Richardson, Thomas and Macon, Kevin and Porter, Mason A and Onnela, Jukka-Pekka},
      journal={Science},
      volume={328},
      number={5980},
      pages={876--878},
      year={2010}
    }

Node2Vec
~~~~~~~~

.. code-block:: bibtex

    @inproceedings{Grover2016,
      title={node2vec: Scalable feature learning for networks},
      author={Grover, Aditya and Leskovec, Jure},
      booktitle={Proceedings of the 22nd ACM SIGKDD international conference on Knowledge discovery and data mining},
      pages={855--864},
      year={2016}
    }

Software Version Information
----------------------------

Reproducibility best practice is to cite the specific version of py3plex used:

.. code-block:: python

    import py3plex
    print(py3plex.__version__)  # e.g., "1.0.2"

In your paper's methods section, include:

.. code-block:: text

    All analyses were performed using py3plex version 1.0.2 [Skrlj2019]
    running on Python 3.10.

Or in acknowledgments:

.. code-block:: text

    This research utilized py3plex (version 1.0.2, Škrlj et al., 2019)
    for multilayer network analysis.

License
-------

Py3plex Core
~~~~~~~~~~~~

The main py3plex library is released under the **MIT License**, a permissive open-source license that allows commercial use:

.. code-block:: text

    Copyright (c) 2019-2025 Blaž Škrlj and contributors
    
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

Bundled Code
~~~~~~~~~~~~

**Important:** Some bundled code (e.g., Infomap community detection in ``py3plex/algorithms/community_detection/infomap/``) is licensed under **AGPLv3**, which has copyleft requirements.

If you use these features, your application may be subject to AGPLv3 requirements. See Chapter 4 for details on license considerations.

This Book
~~~~~~~~~

This book (*Practical Multilayer Network Analysis with Py3plex*) is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

You are free to:

* **Share** — Copy and redistribute the material
* **Adapt** — Remix, transform, and build upon the material

Under the following terms:

* **Attribution** — You must give appropriate credit and provide a link to the license

Acknowledgments
---------------

Py3plex development has been supported by:

* Slovenian Research Agency (research program P2-0103 and projects)
* Jožef Stefan Institute
* Contributors and users worldwide

The py3plex community has provided valuable feedback, bug reports, and feature suggestions. We thank all contributors.

Special thanks to:

* **NetworkX developers** — py3plex builds on NetworkX
* **Apache Arrow project** — For high-performance I/O
* **Open-source community** — For tools and libraries

Contact
-------

For questions about citing py3plex:

* **GitHub Issues:** https://github.com/SkBlaz/py3plex/issues
* **Email:** See contact information in the repository

For research collaborations or academic inquiries, see the py3plex repository for current contact information.
