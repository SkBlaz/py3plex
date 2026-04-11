"""Property-based tests for multilayer embedding primitives."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from py3plex.embeddings.base import EmbeddingResult
from py3plex.ml.embedding.multiplex import (
    NodeLayerIndexer,
    _aggregate_state_embeddings,
)
from py3plex.exceptions import EmbeddingError


StateNode = Tuple[str, str]


@st.composite
def state_nodes_strategy(draw) -> List[StateNode]:
    atom = st.text(
        alphabet=st.characters(min_codepoint=48, max_codepoint=122),
        min_size=1,
        max_size=6,
    )
    return draw(st.lists(st.tuples(atom, atom), min_size=1, max_size=40))


@pytest.mark.property
@given(state_nodes_strategy())
@settings(max_examples=120, deadline=None)
def test_node_layer_indexer_is_order_and_roundtrip_stable(state_nodes: List[StateNode]) -> None:
    indexer = NodeLayerIndexer.from_nodes(state_nodes)

    expected = sorted(set(state_nodes), key=lambda n: (str(n[1]), str(n[0])))
    assert indexer.state_nodes == expected
    assert len(indexer.to_index) == len(indexer.state_nodes)

    for i, state_node in enumerate(indexer.state_nodes):
        assert indexer.state_of(i) == state_node
        assert indexer.index_of(state_node) == i


@st.composite
def state_embedding_inputs(draw) -> Tuple[np.ndarray, List[StateNode]]:
    n_rows = draw(st.integers(min_value=1, max_value=30))
    dim = draw(st.integers(min_value=1, max_value=12))
    atom = st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=4,
    )
    item_ids = draw(
        st.lists(st.tuples(atom, atom), min_size=n_rows, max_size=n_rows, unique=True)
    )
    floats = st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    matrix_list = draw(st.lists(st.lists(floats, min_size=dim, max_size=dim), min_size=n_rows, max_size=n_rows))
    matrix = np.asarray(matrix_list, dtype=np.float32)
    return matrix, item_ids


def _manual_group_reduce(
    matrix: np.ndarray, item_ids: List[StateNode], reducer: str
) -> Tuple[List[str], Dict[str, np.ndarray]]:
    grouped: Dict[str, List[np.ndarray]] = {}
    for row, (node, _) in zip(matrix, item_ids):
        grouped.setdefault(node, []).append(row)
    expected_nodes = sorted(grouped, key=str)
    reduced: Dict[str, np.ndarray] = {}
    for node in expected_nodes:
        stacked = np.vstack(grouped[node])
        if reducer == "sum":
            reduced[node] = np.sum(stacked, axis=0)
        elif reducer == "max":
            reduced[node] = np.max(stacked, axis=0)
        else:
            reduced[node] = np.mean(stacked, axis=0)
    return expected_nodes, reduced


@pytest.mark.property
@given(state_embedding_inputs(), st.sampled_from(["mean", "sum", "max"]))
@settings(max_examples=80, deadline=None)
def test_state_to_node_reducers_match_manual_aggregation(
    state_input: Tuple[np.ndarray, List[StateNode]], reducer: str
) -> None:
    matrix, item_ids = state_input
    state_result = EmbeddingResult(matrix=matrix, item_ids=item_ids, method="state")

    node_result = _aggregate_state_embeddings(state_result, reducer=reducer, method=f"node_{reducer}")
    expected_nodes, reduced = _manual_group_reduce(matrix, item_ids, reducer=reducer)

    assert node_result.nodes == expected_nodes
    assert node_result.to_numpy().shape[1] == matrix.shape[1]
    assert node_result.meta.get("aggregation") == reducer
    assert node_result.meta.get("source_target") == "state"

    for node in expected_nodes:
        np.testing.assert_allclose(
            node_result.get_embedding(node),
            reduced[node].astype(np.float32),
            atol=1e-6,
            rtol=0.0,
        )


@pytest.mark.property
@given(state_embedding_inputs())
@settings(max_examples=40, deadline=None)
def test_attention_reducer_is_guarded(
    state_input: Tuple[np.ndarray, List[StateNode]]
) -> None:
    matrix, item_ids = state_input
    state_result = EmbeddingResult(matrix=matrix, item_ids=item_ids, method="state")

    with pytest.raises(EmbeddingError, match="node_reduce='attention' is not implemented"):
        _aggregate_state_embeddings(state_result, reducer="attention")
