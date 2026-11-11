"""The published CSV examples must load actual edges and preserve layer identity."""

import gzip

import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.linter import GraphFileLinter


MULTILAYER = """source,target,layer,weight
A,B,collaboration,1.0
A,C,dependency,0.8
B,C,collaboration,1.0
A,B,dependency,0.5
C,D,collaboration,0.9
"""


@pytest.mark.parametrize("directed", [True, False])
def test_documented_layered_csv(tmp_path, directed):
    path = tmp_path / "network.csv"
    path.write_text(MULTILAYER)
    net = multi_layer_network(directed=directed).load_network(str(path), input_type="multiedgelist")
    graph = net.core_network
    assert graph.is_directed() == directed
    assert graph.number_of_nodes() == 7
    assert graph.number_of_edges() == 5
    assert graph[("A", "dependency")][("B", "dependency")][0]["weight"] == 0.5
    assert not GraphFileLinter(str(path)).lint()


def test_documented_simple_csv(tmp_path):
    path = tmp_path / "simple.csv"
    path.write_text("source,target,weight\nA,B,1.0\nB,C,0.8\nC,D,1.5\nD,A,0.9\n")
    net = multi_layer_network(directed=False).load_network(str(path), input_type="edgelist")
    assert net.core_network.number_of_edges() == 4
    assert net.core_network[("B", "null")][("C", "null")]["weight"] == 0.8


def test_aliases_quoted_ids_gzip_and_parallel_edges(tmp_path):
    path = tmp_path / "edges.csv.gz"
    with gzip.open(path, "wt") as stream:
        stream.write('src,dst,src_layer,dst_layer,weight,label\n"a,b",c,one,two,0,test\n"a,b",c,one,two,-2,again\n')
    graph = multi_layer_network(directed=True).load_network(str(path), input_type="multiedgelist").core_network
    assert graph.number_of_edges() == 2
    assert graph[("a,b", "one")][("c", "two")][0] == {"weight": 0.0, "label": "test"}


@pytest.mark.parametrize("text", [
    "name,layer\nA,one\n", "source,target,source_layer\nA,B,one\n",
    "source,target,weight\nA,B,nope\n", "source,target,layer\nA,B,\n",
    "source,target\nA\n", "source,target\nA,B,C\n", "source,source,target\nA,A,B\n",
])
def test_invalid_csv_never_silently_becomes_empty(tmp_path, text):
    path = tmp_path / "bad.csv"
    path.write_text(text)
    with pytest.raises(ValueError, match="bad.csv"):
        multi_layer_network().load_network(str(path), input_type="multiedgelist")


def test_cli_loader_uses_the_same_csv_schema(tmp_path):
    from py3plex.cli import _load_network

    path = tmp_path / "network.csv"
    path.write_text(MULTILAYER)
    assert _load_network(str(path)).core_network.number_of_edges() == 5
