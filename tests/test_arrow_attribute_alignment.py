import pytest
from py3plex.dsl.result import QueryResult
pa = pytest.importorskip("pyarrow")

@pytest.mark.parametrize("values,expected", [([1,2],[1]), ([],[None]), ([1],[1])])
def test_arrow_and_parquet_align_selected_items(values, expected, tmp_path):
    import pyarrow.parquet as pq
    result = QueryResult(target="nodes", items=[("a","L")], attributes={"score":values})
    assert result.to_arrow()["score"].to_pylist() == expected
    result.to_parquet(str(tmp_path / "result.parquet"))
    assert pq.read_table(tmp_path / "result.parquet")["score"].to_pylist() == expected
    assert result.attributes["score"] == values

def test_empty_arrow_ignores_extra_attributes():
    result = QueryResult(target="nodes", items=[], attributes={"score":[1,2]})
    assert result.to_arrow().num_rows == 0
