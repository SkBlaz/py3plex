Reference & Citation: The Complete Guide
=========================================

*"Science progresses one funeral at a time."* — Attributed to Max Planck

The Value of Reference Material
-------------------------------

Reference documentation serves a different purpose than tutorials and guides. While learning materials explain concepts and build understanding, reference materials provide precision and completeness. When you need to know the exact parameters of a function, the precise behavior of an algorithm, or the correct citation for a method—reference material is what you need.

What This Section Contains
--------------------------

**Algorithm Reference** provides detailed documentation for every algorithm in py3plex. For each algorithm, you'll find:

* Mathematical formulation (when relevant)
* Parameters and their meanings
* Return values
* Computational complexity
* Usage examples
* References to original papers

This is the definitive source for "how does this algorithm work?" and "what do these parameters mean?"

**API Index** is a comprehensive list of all public classes, functions, and constants in py3plex. This is useful when you know what you're looking for and need to find it quickly.

**Citation & Acknowledgements** provides the information you need to properly cite py3plex in academic work, along with acknowledgements to the researchers and developers who made this library possible.

Using the Reference Material
----------------------------

**When learning:** Reference material is not designed for learning. Use the tutorials and guides instead. Return to reference material when you need precision.

**When working:** Keep the algorithm reference handy. When you're using a function and need to check a parameter, the reference provides authoritative information.

**When writing papers:** The citation section provides the BibTeX entries you need. Proper citation is essential for academic integrity and helps the project.

**When debugging:** If something isn't behaving as expected, the reference material provides the ground truth for what functions should do.

A Note on Algorithms
--------------------

The algorithms in py3plex come from academic research, often with decades of development behind them. The algorithm reference connects you to this broader context. Understanding where an algorithm comes from helps you:

* Know its strengths and limitations
* Find related methods that might work better for your case
* Cite the original authors appropriately
* Contribute back to the community of researchers

Standing on the Shoulders of Giants
-----------------------------------

py3plex exists because of the work of many researchers and developers:

* The NetworkX team, whose work provides py3plex's foundation
* Researchers who developed multilayer network theory and algorithms
* Contributors who reported bugs, suggested features, and submitted code
* Users who pushed the boundaries and discovered new use cases

The citation section is also an acknowledgement section—a recognition that science is a collective endeavor.

Getting Started with Reference
------------------------------

If you're looking for specific information:

* **Algorithm details** → :doc:`algorithm_reference`
* **API lookup** → :doc:`api_index`
* **How to cite** → :doc:`citation_and_acknowledgements`

.. note::

   **Academic Users:**
   
   If you use py3plex in published research, please cite:
   
   .. code-block:: bibtex
   
       @Article{Skrlj2019,
         author={Škrlj, Blaž and Kralj, Jan and Lavrač, Nada},
         title={Py3plex toolkit for visualization and analysis of multilayer networks},
         journal={Applied Network Science},
         year={2019},
         volume={4},
         number={1},
         pages={94},
         doi={10.1007/s41109-019-0203-7}
       }
   
   Citation helps the project continue to receive support and development.
