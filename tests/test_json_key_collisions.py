import json
import pytest
from py3plex.dsl.result import QueryResult

@pytest.mark.parametrize("keys", [(1,"1"), (("a","L"),'["a","L"]')])
@pytest.mark.parametrize("reverse", [False,True])
def test_json_rejects_ambiguous_identifiers_before_writing(keys, reverse, tmp_path):
    pairs = list(zip(keys, [10,20]))
    if reverse:
        pairs.reverse()
    result = QueryResult(target="nodes", items=list(keys), attributes={"score":dict(pairs)})
    path = tmp_path / "result.json"
    path.write_text("existing")
    with pytest.raises(ValueError, match="JSON key collision"):
        result.to_json(path)
    assert path.read_text() == "existing"
    assert len(result.attributes["score"]) == 2

def test_safe_keys_keep_existing_schema():
    result = QueryResult(target="nodes", items=[1,"two"], attributes={"score":{1:10,"two":20}})
    assert json.loads(result.to_json())["attributes"]["score"] == {"1":10,"two":20}

def test_nested_metadata_collision_is_rejected():
    result = QueryResult(target="nodes", items=[], meta={"nested":{1:10,"1":20}})
    with pytest.raises(ValueError, match="JSON key collision"):
        result.to_json()
