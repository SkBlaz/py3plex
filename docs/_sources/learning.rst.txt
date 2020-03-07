Random networks
=====================

Multi-layered structures can also be generated (ER-based)

.. code-block:: python
   :linenos:

	from py3plex.core import multinet
	from py3plex.core import random_generators

	ER_multilayer = random_generators.random_multilayer_ER(200,6,0.09,directed=True)
	ER_multilayer.visualize_network(show=True, no_labels = True)


.. image:: ../example_images/synthetic.png
   :width: 500
