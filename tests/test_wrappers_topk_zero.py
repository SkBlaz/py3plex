"""Samples without true labels must receive no top-k predictions."""

import numpy as np
import pytest

pytest.importorskip('sklearn')
pytest.importorskip('gensim')

from sklearn.linear_model import LogisticRegression

from py3plex.wrappers.benchmark_nodes import TopKRanker


def test_topk_ranker_handles_unlabeled_samples():
    features = np.array([[0, 0], [0, 1], [1, 0], [1, 1], [2, 0], [0, 2]])
    labels = np.array([[1, 0], [0, 1], [1, 0], [0, 1], [1, 0], [0, 1]])
    ranker = TopKRanker(LogisticRegression()).fit(features, labels)

    predictions = ranker.predict(features[:3], [0, 1, 2])

    assert predictions[0] == []
    assert len(predictions[1]) == 1
    assert set(predictions[2]) == {0, 1}
