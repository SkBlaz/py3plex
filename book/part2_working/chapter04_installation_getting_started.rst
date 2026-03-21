.. _installation-chapter:

Installation and First Verified Run
===================================

This chapter gives one supported onboarding path. Alternatives and deployment-heavy setups are in Appendix B.

Golden-Path Setup
-----------------

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
    pip install --upgrade pip
    pip install py3plex

If you need editable development mode, install from source in a separate environment. Keep research and development environments distinct.

Minimal Smoke Test
------------------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q

    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        ['Alice', 'social', 'Bob', 'social', 1],
        ['Bob', 'social', 'Cara', 'social', 1],
    ], input_type='list')

    result = Q.nodes().compute('degree').execute(net)
    print(result.count)

Interpretation note: this verifies installation and execution path only. It does not validate model semantics.

First-Run Checks That Actually Matter
-------------------------------------

After the smoke test:

1. verify your Python version and py3plex version,
2. verify deterministic behavior by setting explicit seeds in stochastic workflows,
3. confirm that your intended file formats are parsed as expected.

Common Early Failures
---------------------

* **Import succeeds, query fails:** often missing optional dependencies for specific algorithms.
* **Unexpected node counts:** replica vs physical-node confusion.
* **Platform mismatch in scripts:** shell-activation differences or path assumptions.

Do not debug these by adding ad-hoc hacks to notebooks; fix environment specification first.

Where Extended Setup Lives
--------------------------

For Docker, CI images, and deployment-oriented setup, use Appendix B. Keeping those details out of the core narrative prevents onboarding chapters from becoming support manuals.
