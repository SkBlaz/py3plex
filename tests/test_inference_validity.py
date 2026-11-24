from types import SimpleNamespace

import numpy as np
import pytest

from py3plex.algorithms.hedwig.stats.adjustment import fdr
from py3plex.algorithms.statistics.bayesiantests import correlated_ttest
from py3plex.algorithms.statistics.enrichment_modules import compute_enrichment


def test_enrichment_counts_disjoint_annotated_entities():
    dataset = {i: (["hit", "hit"] if i < 2 else ["other"]) for i in range(10)}
    result = compute_enrichment(
        dataset, {"hit": 4}, {"partition": [0, 1]}, 12,
        multitest_method="raw", alternative="greater",
    )
    assert result["pval"].iloc[0] == pytest.approx(1 / 45)


def test_yekutieli_applies_step_up_under_dependence():
    rules = [SimpleNamespace(pval=p) for p in (0.02, 0.03)]
    assert fdr(iter(rules), q=0.05) == rules
    assert fdr(rules, q=0.04) == []


def test_constant_differences_inside_rope():
    assert correlated_ttest(np.array([0.01] * 3), 0.1) == (0, 1, 0)
