import numpy as np
import pytest
from py3plex.algorithms import attribute_correlation as module

@pytest.mark.parametrize("method,backend", [("pearson","pearsonr"),("spearman","spearmanr"),("kendall","kendalltau")])
def test_tiny_rounding_errors_are_clamped(method,backend,monkeypatch):
    monkeypatch.setattr(module,backend,lambda x,y:(1.0000000000000002,1.0000000000000002))
    assert module._compute_correlation(np.array([1,2,3]),np.array([1,2,3]),method)==(1.,1.)

def test_undefined_correlation_remains_nan(monkeypatch):
    monkeypatch.setattr(module,"pearsonr",lambda x,y:(float("nan"),float("nan")))
    assert all(np.isnan(v) for v in module._compute_correlation(np.array([1,1]),np.array([1,1]),"pearson"))
