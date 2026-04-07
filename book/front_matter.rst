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

Read the book as a staged argument. **Part I (Foundations)** defines semantics and design boundaries; **Part II (Working Practice)** turns those choices into onboarding, representation, visualization, and algorithm decisions; **Part III (DSL)** makes query logic auditable; **Part IV (Case Studies)** shows where conclusions materially change; and **Part V (Systems)** treats testing and reproducibility as scientific controls. The core chapters carry the argument, while the appendices remain software reference material for implementation detail and lookup.

What This Book Deliberately Does Not Do
---------------------------------------

* It does not claim that multilayer modeling is always superior.
* It does not treat convenience interfaces as methodological guarantees.
* It does not equate reproducible code execution with valid scientific inference.

About the Software
------------------

This edition targets **py3plex 1.1.6**. py3plex implements multilayer data structures, algorithm wrappers, DSL tooling, and workflow utilities. Some operations delegate to single-layer backends after explicit transformations; those transitions are identified in the relevant chapters.

Conventions
-----------

* Code blocks are minimal and intended to expose analytical decisions.
* We label whether a statement is a **concept**, **implementation choice**, **approximation**, or **workflow recommendation**.
* Caveats are presented inline where methods are introduced.

Acknowledgment and Citation
---------------------------

If py3plex contributes to published work, cite the primary toolkit paper:

Skrlj, B., Kralj, J., and Lavrac, N. (2019). *Py3plex toolkit for visualization and analysis of multilayer networks*. Applied Network Science, 4(1), 94. DOI: ``10.1007/s41109-019-0203-7``.

License
-------

The py3plex library is released under the MIT License; this book text is released under CC BY 4.0.

Running Example Used Throughout
-------------------------------

Across Parts I–V, we repeatedly revisit a three-layer commuter network (metro, bus, and walking-transfer links) to compare a flattened ranking against a multilayer ranking, then stress-test that difference under uncertainty and disruption scenarios.

.. note::
   **Version Information:** This book edition is version 1.1.6 (2026), aligned with py3plex 1.1.6 and Python 3.8+ runtime support.
