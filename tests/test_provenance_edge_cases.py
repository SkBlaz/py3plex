"""Coverage for provenance bundle and replay failure paths."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

import py3plex.provenance.bundle as bundle_module
from py3plex.provenance.bundle import (
    BundleError,
    _serialize_attributes,
    _serialize_items,
    create_replay_bundle,
    export_bundle,
    load_bundle,
)
from py3plex.provenance.replay import ReplayContext, ReplayError
from py3plex.provenance.schema import (
    ProvenanceMode,
    create_provenance_record,
)


def _result(*, replayable=True):
    provenance = create_provenance_record(
        mode=ProvenanceMode.REPLAYABLE if replayable else ProvenanceMode.LOG,
        ast_hash="abc",
        ast_summary="SELECT nodes",
        network_fingerprint={"node_count": 2, "edge_count": 1, "layer_count": 1, "layers": ["L"]},
    ).to_dict()
    return SimpleNamespace(
        meta={"provenance": provenance},
        target="nodes",
        items=[("A", "L"), "B"],
        attributes={"degree": {("A", "L"): 1, "B": 0}},
        count=2,
        is_replayable=replayable,
    )


def test_plain_bundle_roundtrip_and_optional_result_payload(tmp_path):
    output = tmp_path / "bundle"
    export_bundle(_result(replayable=False), output, compress=False, include_results=False)

    bundle_path = tmp_path / "bundle.json"
    assert bundle_path.exists()
    bundle = load_bundle(bundle_path)
    assert "provenance" in bundle
    assert "result" not in bundle


def test_bundle_serializes_tuple_items_and_attribute_keys(tmp_path):
    output = tmp_path / "bundle.json"
    export_bundle(_result(), output, compress=False)

    bundle = load_bundle(output)
    assert bundle["result"]["items"] == [["A", "L"], "B"]
    assert "('A', 'L')" in bundle["result"]["attributes"]["degree"]
    assert _serialize_items(("A", "L")) == ("A", "L")
    assert _serialize_attributes({"label": "hub"}) == {"label": "hub"}


def test_bundle_rejects_missing_or_malformed_files(tmp_path):
    with pytest.raises(BundleError, match="does not have provenance"):
        export_bundle(SimpleNamespace(meta={}), tmp_path / "missing.json")

    with pytest.raises(BundleError, match="not found"):
        load_bundle(tmp_path / "missing.json")

    malformed = tmp_path / "malformed.json"
    malformed.write_text("not json", encoding="utf-8")
    with pytest.raises(BundleError, match="Failed to read bundle"):
        load_bundle(malformed)

    missing_provenance = tmp_path / "missing-provenance.json"
    missing_provenance.write_text("{}", encoding="utf-8")
    with pytest.raises(BundleError, match="does not contain provenance"):
        load_bundle(missing_provenance, validate=False)


def test_bundle_validation_reports_invalid_provenance(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"provenance": {"schema_version": "1.0"}}', encoding="utf-8")

    with pytest.raises(BundleError, match="Invalid provenance schema"):
        load_bundle(invalid)


def test_bundle_warns_when_schema_version_is_unknown(tmp_path):
    result = _result()
    result.meta["provenance"]["schema_version"] = "2.0"
    output = tmp_path / "version.json"
    export_bundle(result, output, compress=False)

    with pytest.warns(UserWarning, match="schema version 2.0"):
        assert load_bundle(output)["provenance"]["schema_version"] == "2.0"


def test_bundle_wraps_serialization_and_write_errors(tmp_path, monkeypatch):
    def fail_json(*args, **kwargs):
        raise ValueError("cannot encode")

    monkeypatch.setattr(bundle_module.json, "dumps", fail_json)
    with pytest.raises(BundleError, match="Failed to serialize bundle"):
        export_bundle(_result(), tmp_path / "serialization.json")

    monkeypatch.undo()
    directory = tmp_path / "write.json"
    directory.mkdir()
    with pytest.raises(BundleError, match="Failed to write bundle"):
        export_bundle(_result(), directory, compress=False)


def test_create_replay_bundle_requires_replayable_result(tmp_path):
    with pytest.raises(BundleError, match="replayable provenance"):
        create_replay_bundle(_result(replayable=False), tmp_path / "nope", compress=False)

    create_replay_bundle(_result(), tmp_path / "replay", compress=False)
    assert (tmp_path / "replay.json").exists()

    create_replay_bundle(_result(), tmp_path / "compressed", compress=True)
    assert (tmp_path / "compressed.json.gz").exists()


def _context(*, mode=ProvenanceMode.REPLAYABLE, ast=True, capture=True, engine="dsl_v2_executor"):
    snapshot = {"nodes": [], "edges": [], "directed": False, "metadata": {}}
    record = create_provenance_record(
        mode=mode,
        engine=engine,
        ast_serialized={"select": {}} if ast else None,
        snapshot_data=snapshot if capture else None,
        snapshot_external_path="snapshot.json" if not capture else None,
    )
    return ReplayContext(record)


def test_replay_validation_explains_non_replayable_and_incomplete_records():
    with pytest.raises(ReplayError, match="not 'replayable'"):
        _context(mode=ProvenanceMode.LOG).validate(strict=False)

    with pytest.raises(ReplayError, match="AST not serialized"):
        _context(ast=False).validate(strict=False)

    ctx = _context(ast=True, capture=False)
    ctx.provenance.network_capture.snapshot_external_path = None
    with pytest.raises(ReplayError, match="snapshot not captured"):
        ctx.validate(strict=False)


def test_replay_context_restores_inline_and_rejects_unimplemented_sources():
    inline = _context()
    inline.validate(strict=False)
    restored = inline.restore_network()
    assert restored.core_network is None
    assert inline.restore_network() is restored

    external = _context(capture=False)
    with pytest.raises(ReplayError, match="External snapshot restoration"):
        external.restore_network()

    delta = _context(capture=False)
    delta.provenance.network_capture.snapshot_external_path = None
    delta.provenance.network_capture.delta_ops = [{"op": "add_node"}]
    with pytest.raises(ReplayError, match="Delta-based reconstruction"):
        delta.restore_network()

    absent = _context(capture=False)
    absent.provenance.network_capture.snapshot_external_path = None
    with pytest.raises(ReplayError, match="No network capture"):
        absent.restore_network()


def test_replay_validation_warns_on_version_mismatch():
    ctx = _context()
    with patch("py3plex.dsl.provenance.get_py3plex_version", return_value="0.0.0"):
        with pytest.warns(UserWarning, match="Version mismatch"):
            ctx.validate(strict=True)


def test_replay_wraps_invalid_serialized_queries_and_empty_snapshots():
    invalid_snapshot = _context()
    invalid_snapshot.provenance.network_capture.snapshot_data = {"invalid": True}
    with pytest.raises(ReplayError, match="Failed to restore network"):
        invalid_snapshot.restore_network()

    invalid_query = _context()
    with patch(
        "py3plex.dsl.serializer.deserialize_query",
        side_effect=ValueError("cannot decode"),
    ):
        with pytest.raises(ReplayError, match="Failed to reconstruct DSL v2 query"):
            invalid_query.reconstruct_query()

    empty_query = _context()
    empty_query.provenance.query.ast_serialized = {}
    with pytest.raises(ReplayError, match="No serialized AST"):
        empty_query._reconstruct_dsl_v2_query()


def test_replay_query_reconstruction_supports_legacy_and_rejects_unknown_engine():
    legacy = _context(engine="dsl_legacy")
    legacy.provenance.query.params = {"raw_string": "SELECT *"}
    assert legacy.reconstruct_query() == "SELECT *"

    missing_raw = _context(engine="dsl_legacy")
    with pytest.raises(ReplayError, match="raw query string"):
        missing_raw.reconstruct_query()

    unsupported = _context(engine="other")
    with pytest.raises(ReplayError, match="Unsupported engine"):
        unsupported.reconstruct_query()


def test_replay_context_accepts_a_preconstructed_network():
    network = object()
    ctx = _context()
    ctx.network = network
    assert ctx.restore_network() is network


def test_replay_randomness_restoration_accepts_seed_sequence_entropy():
    from py3plex.provenance.replay import _restore_random_state

    _restore_random_state(
        SimpleNamespace(base_seed=42, seed_sequence_entropy=[1, 2, 3])
    )
