from unittest.mock import patch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import numpy as np
import pandas as pd
import pytest
from py3plex.algorithms.statistics.critical_distances import diagram, plot_critical_distance


def scores():
    return pd.DataFrame([(f"d{i}", name, value) for i in range(10) for name,value in [("a",.9),("b",.6),("c",.3)]], columns=["dataset","setting","macro_F"])


def test_nemenyi_cd_uses_all_algorithms_and_dataset_count():
    with patch("py3plex.algorithms.statistics.critical_distances.diagram") as draw:
        plot_critical_distance(scores(), crit_dist=True)
    assert len(draw.call_args.args[0]) == 3
    # Published Nemenyi q_0.05 for k=3 is approximately 2.3437.
    assert draw.call_args.kwargs["critical_distance"] == pytest.approx(2.3437 * np.sqrt(12/60), abs=1e-4)
    assert draw.call_args.args[1] is None


def test_cd_plot_draws_cd_and_only_nonsignificant_group():
    with plt.rc_context({"text.usetex":False}), patch("matplotlib.pyplot.show"):
        diagram([("a",1.),("b",1.4),("c",3.)], None, None, critical_distance=.6)
        ax=plt.gca()
        assert any("critical distance" in t.get_text() for t in ax.texts)
        groups=[line for line in ax.lines if to_rgba(line.get_color())==to_rgba("r") and line.get_linewidth()==1]
        assert len(groups)==1
        assert np.allclose(groups[0].get_xdata(), [.96,1.44])
        plt.close("all")


def test_diagram_saves_without_latex(tmp_path):
    path=tmp_path / "cd.svg"
    with plt.rc_context({"text.usetex":False}):
        assert diagram([("a",1.),("b",2.)],None,str(path),critical_distance=.5) == str(path)
    assert path.stat().st_size > 0
    plt.close("all")


def test_incomplete_comparisons_are_rejected():
    with pytest.raises(ValueError, match="same algorithms"):
        plot_critical_distance(scores().iloc[:-1], crit_dist=True)
