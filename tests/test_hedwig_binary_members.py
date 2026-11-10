import pytest
rdflib = pytest.importorskip("rdflib")
from py3plex.algorithms.hedwig.core.kb import ExperimentKB

def test_binary_members_and_domains():
    graph = rdflib.Graph()
    a,b,c,p = [rdflib.URIRef("urn:" + name) for name in ("a","b","c","relation")]
    for source,target in [(a,b),(a,c),(b,c)]:
        graph.add((source,p,target))
    kb = ExperimentKB.__new__(ExperimentKB)
    kb.members = {}
    kb.binary_predicates = {str(p)}
    kb.uri_to_idx = {a:0,b:1,c:2}
    kb.examples = [None]*3
    kb._calc_binary_members(graph)
    assert set(kb.binary_members[str(p)][0]) == {1,2}
    assert kb.binary_members[str(p)][1] == [2]
    assert set(kb.reverse_binary_members[str(p)][2]) == {0,1}
    domain,range_ = kb.binary_domains[str(p)]
    assert domain.tolist() == [1,1,0]
    assert range_.tolist() == [0,1,1]

def test_empty_binary_predicates():
    kb = ExperimentKB.__new__(ExperimentKB)
    kb.members = {}
    kb.binary_predicates = set()
    kb._calc_binary_members(rdflib.Graph())
    assert kb.binary_domains == {}
