GUI: Visual Exploration for Everyone
=====================================

*"A picture is worth a thousand words."* — Traditional Proverb

Why a Graphical Interface?
--------------------------

Not everyone who needs to analyze multilayer networks is comfortable writing Python code. Domain experts—biologists, social scientists, urban planners—often have deep knowledge of their systems but limited programming experience. For them, a graphical user interface (GUI) opens the door to powerful analysis tools.

Even for experienced programmers, visual interfaces have value. Quick exploration is often faster with point-and-click than with code. Visual feedback helps you understand data before committing to a specific analysis approach. Demonstrations to stakeholders are more compelling when they can interact with the visualization.

py3plex's GUI brings multilayer network analysis to a broader audience while remaining backed by the same robust algorithms as the Python library.

What the GUI Provides
---------------------

The py3plex GUI is a web-based interface for interactive network exploration and analysis. You can:

* **Load networks** from various file formats without writing code
* **Visualize** your networks with interactive, zoomable layouts
* **Compute statistics** by selecting options from menus
* **Detect communities** and see them colored in the visualization
* **Export results** for further analysis or publication

The interface is designed to be intuitive for newcomers while still providing access to advanced features.

What This Section Covers
------------------------

**GUI User Guide** walks you through using the interface: loading data, exploring networks, running analyses, and exporting results. If you're using the GUI for analysis, start here.

**GUI Deployment** covers how to run the GUI server—locally for personal use or on a server for team access. This is for administrators and power users.

**GUI API Reference** documents the backend API for developers who want to extend the GUI or integrate it with other systems.

**GUI Architecture** explains how the GUI is built, useful for developers who want to contribute to or modify the interface.

**GUI Testing** covers the testing infrastructure for the GUI components.

Who Should Use the GUI?
-----------------------

The GUI is particularly well-suited for:

**Domain experts** who want to analyze their networks without learning Python. The visual interface makes multilayer network analysis accessible.

**Exploratory analysis** when you want to quickly understand a new dataset. Visual exploration often reveals patterns faster than writing code.

**Teaching and demonstrations** where you want to show multilayer network concepts interactively.

**Collaborative work** where team members have varying technical backgrounds. Everyone can use the same interface.

For production pipelines, automated analyses, or advanced customization, the Python library remains the better choice. The GUI and library complement each other.

Getting Started with the GUI
----------------------------

To start using the GUI, follow the deployment instructions in :doc:`gui_deployment`, then work through the :doc:`gui_user_guide` for a complete walkthrough.

.. tip::

   **GUI vs. Python Library:**
   
   ============== ============= =================
   Task           GUI           Python Library
   ============== ============= =================
   Quick explore  ✓ Better      Good
   Scripted       Not suitable  ✓ Better
   Reproducible   Challenging   ✓ Better
   Non-technical  ✓ Better      Challenging
   Advanced       Limited       ✓ Better
   ============== ============= =================
   
   Choose the tool that fits your needs—or use both!
