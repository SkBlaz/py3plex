Front Matter
============

About This Book
---------------

**Practical Multilayer Network Analysis with Py3plex** is a technical handbook for readers who already know basic graph analytics and want to make better modeling decisions on multilayer data.

This is not a complete API catalog. It is a working text about representation, inference, failure modes, and reproducibility.

Scope and Reader Contract
-------------------------

The core narrative is organized around four questions:

1. When does multilayer modeling change the scientific conclusion?
2. Which py3plex implementation choices are consequential for that conclusion?
3. Which approximations are acceptable under realistic constraints?
4. How do we make the workflow auditable and reproducible?

The book assumes intermediate Python fluency, familiarity with standard graph concepts, and comfort reading short mathematical arguments.

How to Read This Book
---------------------

* **Part I (Foundations)** defines semantics and design boundaries.
* **Part II (Working Practice)** covers onboarding, representation choices, visualization, and algorithm families.
* **Part III (DSL)** teaches query reasoning, not just syntax.
* **Part IV (Case Studies)** demonstrates analytical payoff and contestable modeling choices.
* **Part V (Systems)** treats testing and reproducibility as central scientific practice.

Reference-heavy material (deployment details, long validation scripts, API listings) is placed in appendices to keep the main text focused.

What This Book Deliberately Does Not Do
---------------------------------------

* It does not claim that multilayer modeling is always superior.
* It does not treat convenience interfaces as methodological guarantees.
* It does not equate reproducible code execution with valid scientific inference.

About the Software
------------------

This edition targets **py3plex 1.1.5**. py3plex implements multilayer data structures, algorithm wrappers, DSL tooling, and workflow utilities. Some operations delegate to single-layer backends after explicit transformations; those transitions are identified in the relevant chapters.

Conventions
-----------

* Code blocks are minimal and intended to expose analytical decisions.
* We label whether a statement is a **concept**, **implementation choice**, **approximation**, or **workflow recommendation**.
* Caveats are presented inline where methods are introduced.

Acknowledgment and Citation
---------------------------

If py3plex contributes to published work, cite:

.. code-block:: bibtex

    @Article{Skrlj2019,
      author={Skrlj, Blaz and Kralj, Jan and Lavrac, Nada},
      title={Py3plex toolkit for visualization and analysis of multilayer networks},
      journal={Applied Network Science},
      year={2019},
      volume={4},
      number={1},
      pages={94},
      doi={10.1007/s41109-019-0203-7}
    }

License
-------

The py3plex library is released under the MIT License. Book text is released under CC BY 4.0.

.. note::
   **Version Information:** This book edition is version 1.1.5 (2025), aligned with py3plex 1.1.5 and Python 3.8+ runtime support.
