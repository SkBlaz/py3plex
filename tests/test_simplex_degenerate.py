import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from py3plex.algorithms.statistics.bayesiantests import plot_posterior

@pytest.mark.parametrize("zero", [0,1,2])
@pytest.mark.parametrize("names", [("A","B"), ["A","B"]])
def test_posterior_on_simplex_edge(zero, names):
    points = np.array([[.4,.6],[.7,.3]])
    points = np.insert(points, zero, 0., axis=1)
    fig = plot_posterior(points, names=names)
    assert len(fig.axes) == 1
    assert len(fig.axes[0].collections) == 1
    assert all(np.isfinite(fig.axes[0].collections[0].get_offsets()).ravel())
    assert any("A" in t.get_text() for t in fig.axes[0].texts)
    plt.close(fig)
