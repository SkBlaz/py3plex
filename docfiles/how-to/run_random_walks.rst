How to Run Random Walk Algorithms
==================================

Use the random-walk helpers to sample paths, or train node embeddings with
``network.embed()``. The network stores nodes as ``(id, layer)`` replicas.

Build a Sample Network
----------------------

.. code-block:: python

    from py3plex.core import multinet

    network = multinet.multi_layer_network(directed=False, verbose=False)
    network.add_edges([
        ["Alice", "friends", "Bob", "friends", 1],
        ["Bob", "friends", "Charlie", "friends", 1],
        ["Charlie", "friends", "Alice", "friends", 1],
        ["Alice", "colleagues", "Dana", "colleagues", 1],
        ["Bob", "colleagues", "Dana", "colleagues", 1],
        ["Alice", "friends", "Alice", "colleagues", 1],
    ], input_type="list")

Sample Walks
------------

``generate_walks()`` accepts a NetworkX graph. Each returned node sequence
starts with its initial replica. A walk that reaches a dead end can stop
early.

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks

    walks = generate_walks(
        network.core_network,
        start_nodes=[("Alice", "friends")],
        num_walks=3,
        walk_length=8,
        p=1.0,
        q=2.0,
        seed=42,
    )
    print(walks[0])

With ``p < 1``, a walk is more likely to backtrack. With ``q > 1``, it is
more likely to stay near the previous replica. Equal values of 1 remove
this second-order bias. Pass ``weighted=False`` to ignore edge weights.

Node2Vec Embeddings
-------------------

``network.embed()`` returns an ``EmbeddingResult``. Its ``item_ids`` give the
replica identifiers in row order, and ``vectors`` provides an ID-to-vector
mapping.

.. code-block:: python

    embeddings = network.embed(
        method="node2vec",
        dimensions=8,
        walk_length=8,
        num_walks=4,
        p=1.0,
        q=2.0,
        seed=42,
    )
    vector = embeddings[("Alice", "friends")]
    assert vector.shape == (8,)

DeepWalk Embeddings
-------------------

Choose DeepWalk for first-order walk embeddings without Node2Vec's
second-order parameters.

.. code-block:: python

    deepwalk = network.embed(
        method="deepwalk", dimensions=8, walk_length=8, num_walks=4, seed=42
    )

Using Embeddings for Downstream Tasks
-------------------------------------

Use the matrix and its row IDs together for classification, clustering, or
visualization. For example, join labels to ``embeddings.item_ids`` in that
order before fitting a classifier. If multiple replicas share one physical
label, keep replicas of the same physical node together when splitting data
to evaluate generalization to unseen entities.

.. code-block:: python

    X = embeddings.to_numpy()
    neighbors = embeddings.most_similar(("Alice", "friends"), k=3)
    print(neighbors)

Cosine similarity ranks candidates. To evaluate link prediction, reserve
edges for evaluation before training the embedding and compare scores on
held-out edges and non-edges.

Layer-Specific Embeddings
-------------------------

Filtering a DSL embedding query selects the rows to return. To train on
edges of just one layer, create the layer graph explicitly.

.. code-block:: python

    layer = "friends"
    replicas = [node for node in network.get_nodes() if node[1] == layer]
    graph = network.core_network.subgraph(replicas)
    layer_network = multinet.multi_layer_network(directed=graph.is_directed())
    layer_network.core_network = graph.copy()

    layer_embeddings = layer_network.embed(
        method="node2vec", dimensions=8, walk_length=8, num_walks=4, seed=42
    )
    assert all(node[1] == layer for node in layer_embeddings.item_ids)

Embeddings trained separately have separate coordinate systems. Use a
shared embedding to compare vectors across layers directly.

Query and Filter Nodes Before Embedding with DSL
------------------------------------------------

Select rows by layer and degree, then export their embeddings and metrics.
The embedding backend still sees the network supplied to ``execute()``.

.. code-block:: python

    from py3plex.dsl import L, Q

    result = (
        Q.nodes()
        .from_layers(L["friends"])
        .where(degree__gt=1)
        .compute("degree")
        .embed(method="node2vec", dim=8, walk_length=8, num_walks=4, seed=42)
        .execute(network)
    )
    vectors = result.to_numpy("embedding")
    assert vectors.shape == (result.count, 8)

Saving and Loading Embeddings
-----------------------------

Use the embedding container to save the matrix with its replica IDs. For a
combined table, export the selected IDs, metrics, and embedding dimensions
from the same result rows.

.. code-block:: python

    from py3plex.embeddings import EmbeddingResult

    embeddings.save("node_embeddings.npz")
    restored = EmbeddingResult.load("node_embeddings.npz")
    assert restored.item_ids == embeddings.item_ids

    table = result.to_pandas().drop(columns="embedding")
    for column, values in enumerate(vectors.T):
        table[f"emb_{column}"] = values
    table.to_csv("embeddings_with_metrics.csv", index=False)

Next Steps
----------

* :doc:`../user_guide/random_walks_embeddings` for walk parameters and sampling.
* :doc:`query_with_dsl` for selecting and exporting results.
* :doc:`../reference/algorithm_reference` for embedding backends.
