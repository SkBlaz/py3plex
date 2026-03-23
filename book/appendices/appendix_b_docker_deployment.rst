Appendix B: Docker, Docker Compose, and Deployment
==================================================

This appendix keeps one recommended deployment path for controlled environments and highlights caveats that matter for analytical integrity.

Recommended Path (Controlled Environment)
-----------------------------------------

1. Build one pinned image for the analysis environment.
2. Run py3plex workflows in that container with mounted input/output directories.
3. Keep GUI usage local or inside trusted internal networks only.

.. code-block:: bash

    docker build -t py3plex:1.1.4 .
    docker run --rm -v $(pwd)/data:/data -v $(pwd)/results:/results py3plex:1.1.4 python script.py

For multi-service local orchestration:

.. code-block:: bash

    docker compose up -d
    docker compose logs -f
    docker compose down

Security and Boundary Warnings
------------------------------

.. warning::

   The GUI is experimental and should not be treated as a hardened public service. Use controlled, trusted environments unless you add independent hardening, authentication, and operational monitoring.

At minimum:

* run with explicit secrets via environment variables,
* prefer non-root containers,
* restrict uploads and writable paths,
* terminate TLS if exposed beyond localhost/VPN,
* keep base images and dependencies updated.

What This Appendix Deliberately Omits
-------------------------------------

To keep the book focused, broad cloud deployment matrices and command-heavy infrastructure permutations are maintained in repository documentation rather than the manuscript body.

See also:

* :ref:`gui-chapter` for GUI usage boundaries,
* repository deployment docs for extended cloud and reverse-proxy recipes.
