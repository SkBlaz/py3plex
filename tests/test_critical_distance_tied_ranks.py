from unittest.mock import patch
import pandas as pd
import pytest
from py3plex.algorithms.statistics.critical_distances import plot_critical_distance

@pytest.mark.parametrize("scores,expected", [([.5,.5],[1.5,1.5]), ([.8,.8,.8],[2.,2.,2.]), ([.1,.9,.5],[3.,1.,2.])])
def test_average_ranks_respect_ties_and_input_order(scores, expected):
    names = ["a","b","c"][:len(scores)]
    data = pd.DataFrame({"dataset":["d"]*len(scores), "setting":names, "macro_F":scores})
    for frame in (data, data.iloc[::-1]):
        with patch("py3plex.algorithms.statistics.critical_distances.diagram") as draw:
            plot_critical_distance(frame)
        assert dict(draw.call_args.args[0]) == dict(zip(names,expected))

def test_average_ranks_across_datasets():
    data = pd.DataFrame({"dataset":["d1","d1","d2","d2"], "setting":["a","b","a","b"], "macro_F":[.5,.5,.8,.2]})
    with patch("py3plex.algorithms.statistics.critical_distances.diagram") as draw:
        plot_critical_distance(data)
    assert dict(draw.call_args.args[0]) == {"a":1.25,"b":1.75}
