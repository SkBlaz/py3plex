"""Tests for py3plex.meta.utils helper functions."""

from datetime import datetime, timezone

from py3plex.meta.utils import aggregate_provenance


class _DummyResult:
    def __init__(self):
        self.meta = {
            "provenance": {
                "query": {"ast_hash": "deadbeefdeadbeef"},
                "randomness": {"seed": 42, "method": "bootstrap", "n_samples": 10},
                "performance": {"total_ms": 1.23},
                "warnings": [],
            }
        }


def test_aggregate_provenance_timestamp_is_timezone_aware():
    """Timestamp should be UTC-aware and normalized to trailing Z."""
    provenance = aggregate_provenance(
        network_names=["n1"],
        results={"n1": _DummyResult()},
        networks_fingerprints={
            "n1": {
                "node_count": 1,
                "edge_count": 0,
                "layer_count": 1,
                "layers": ["L1"],
            }
        },
    )

    ts = provenance["timestamp_utc"]
    assert ts.endswith("Z")
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)
