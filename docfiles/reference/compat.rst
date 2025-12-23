.. _api-compat:

Compatibility Layer API
=======================

.. module:: py3plex.compat

The compatibility layer provides lossless conversion between py3plex and external graph libraries.

Main Conversion API
-------------------

.. autofunction:: convert

.. autofunction:: to_ir

.. autofunction:: from_ir

Intermediate Representation
---------------------------

.. autoclass:: GraphIR
   :members:
   :undoc-members:

.. autoclass:: NodeTable
   :members:
   :undoc-members:

.. autoclass:: EdgeTable
   :members:
   :undoc-members:

.. autoclass:: GraphMeta
   :members:
   :undoc-members:

Schema Validation
-----------------

.. autoclass:: GraphSchema
   :members:
   :undoc-members:

.. autofunction:: infer_schema

.. autofunction:: validate_against_schema

Equality Checking
-----------------

.. autofunction:: ir_equals

.. autofunction:: ir_diff

Sidecar Bundles
---------------

.. module:: py3plex.compat.sidecar

.. autofunction:: export_sidecar

.. autofunction:: import_sidecar

Exceptions
----------

.. module:: py3plex.compat.exceptions

.. autoexception:: CompatibilityError
   :members:
   :show-inheritance:

.. autoexception:: SchemaError
   :members:
   :show-inheritance:

.. autoexception:: ConversionNotSupportedError
   :members:
   :show-inheritance:

Converters
----------

NetworkX
~~~~~~~~

.. module:: py3plex.compat.converters.networkx_converter

.. autofunction:: to_networkx_from_ir

.. autofunction:: from_networkx_to_ir

SciPy Sparse
~~~~~~~~~~~~

.. module:: py3plex.compat.converters.scipy_converter

.. autofunction:: to_scipy_sparse_from_ir

.. autofunction:: from_scipy_sparse_to_ir

igraph
~~~~~~

.. module:: py3plex.compat.converters.igraph_converter

.. autofunction:: to_igraph_from_ir

.. autofunction:: from_igraph_to_ir
