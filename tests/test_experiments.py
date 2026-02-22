"""Tests for py3plex.experiments – Network Experiment Registry.

Covers:
- Deterministic ID generation (same inputs → same ID)
- Experiment model round-trip (to_dict / from_dict)
- ExperimentStore: save / load / list / delete
- Artifact serialisation helpers
- Environment fingerprinting stability
- ExperimentRunner.record_query_result (legacy DSL + DSL v2)
- DSL v2 QueryResult.record_as_experiment integration hook
- CLI subcommands (list, show, run, reproduce, export) via subprocess
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from py3plex.core import multinet
from py3plex.dsl import Q, execute_query
from py3plex.experiments import (
    Experiment,
    ExperimentRunner,
    ExperimentStore,
    list_experiments,
    load_experiment,
    register_default_store,
    reproduce_experiment,
)
from py3plex.experiments.env import get_environment_fingerprint
from py3plex.experiments.errors import ExperimentNotFound
from py3plex.experiments.utils import canonical_json, stable_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _small_net():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([{"source": "A", "type": "s"}, {"source": "B", "type": "s"}])
    net.add_edges(
        [{"source": "A", "target": "B", "source_type": "s", "target_type": "s"}]
    )
    return net


def _fake_provenance(**overrides):
    prov = {
        "engine": "dsl_v2_executor",
        "py3plex_version": "1.1.3",
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "query": {
            "ast_hash": "abc123",
            "ast_summary": "nodes",
            "params": {},
        },
        "network_fingerprint": {
            "node_count": 5,
            "edge_count": 4,
            "layer_count": 1,
            "layers": ["social"],
        },
        "randomness": {},
        "backend": {},
        "performance": {},
    }
    prov.update(overrides)
    return prov


# ===========================================================================
# utils.py
# ===========================================================================

class TestCanonicalJson:
    def test_key_ordering_is_stable(self):
        d1 = {"b": 1, "a": 2}
        d2 = {"a": 2, "b": 1}
        assert canonical_json(d1) == canonical_json(d2)

    def test_nested_dict_ordering(self):
        d = {"z": {"y": 1, "x": 2}, "a": 3}
        canon = canonical_json(d)
        parsed = json.loads(canon)
        # Keys should remain present
        assert "z" in parsed
        assert "a" in parsed

    def test_lists_preserved(self):
        d = {"items": [3, 1, 2]}
        parsed = json.loads(canonical_json(d))
        assert parsed["items"] == [3, 1, 2]  # order preserved for lists


class TestStableHash:
    def test_same_input_same_hash(self):
        h1 = stable_hash({"a": 1, "b": 2})
        h2 = stable_hash({"a": 1, "b": 2})
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = stable_hash({"a": 1})
        h2 = stable_hash({"a": 2})
        assert h1 != h2

    def test_hash_is_hex_string(self):
        h = stable_hash({"x": 42})
        assert isinstance(h, str)
        int(h, 16)  # raises ValueError if not hex


# ===========================================================================
# env.py
# ===========================================================================

class TestEnvironmentFingerprint:
    def test_required_keys_present(self):
        env = get_environment_fingerprint()
        for key in ("python", "platform", "py3plex_version", "env_hash"):
            assert key in env, f"Missing key: {key}"

    def test_env_hash_is_string(self):
        env = get_environment_fingerprint()
        assert isinstance(env["env_hash"], str)
        assert len(env["env_hash"]) > 0

    def test_stability(self):
        """Calling twice in the same process should produce the same hash."""
        e1 = get_environment_fingerprint()
        e2 = get_environment_fingerprint()
        assert e1["env_hash"] == e2["env_hash"]


# ===========================================================================
# model.py – Experiment
# ===========================================================================

class TestExperimentFromProvenance:
    def test_basic_construction(self):
        exp = Experiment.from_provenance(_fake_provenance())
        assert exp.id
        assert exp.engine == "dsl_v2_executor"
        assert exp.py3plex_version == "1.1.3"

    def test_id_is_deterministic(self):
        prov = _fake_provenance()
        id1 = Experiment.from_provenance(prov).id
        id2 = Experiment.from_provenance(prov).id
        assert id1 == id2

    def test_different_prov_different_id(self):
        prov1 = _fake_provenance()
        prov2 = _fake_provenance()
        prov2["network_fingerprint"] = {
            "node_count": 99,
            "edge_count": 50,
            "layer_count": 2,
            "layers": ["a", "b"],
        }
        assert Experiment.from_provenance(prov1).id != Experiment.from_provenance(prov2).id

    def test_id_full_vs_short(self):
        exp = Experiment.from_provenance(_fake_provenance())
        assert len(exp.id_full) == 64  # sha256 hex
        assert exp.id_full.startswith(exp.id)

    def test_tags_and_notes_stored(self):
        exp = Experiment.from_provenance(_fake_provenance(), tags=["t1", "t2"], notes="hello")
        assert "t1" in exp.tags
        assert exp.notes == "hello"


class TestExperimentRoundTrip:
    def test_to_dict_from_dict_identity(self):
        exp = Experiment.from_provenance(_fake_provenance(), tags=["x"], notes="n")
        data = exp.to_dict()
        exp2 = Experiment.from_dict(data)
        assert exp2.id == exp.id
        assert exp2.engine == exp.engine
        assert exp2.tags == exp.tags
        assert exp2.notes == exp.notes

    def test_to_dict_is_json_serialisable(self):
        exp = Experiment.from_provenance(_fake_provenance())
        text = json.dumps(exp.to_dict(), default=str)
        assert json.loads(text)


# ===========================================================================
# store.py – ExperimentStore
# ===========================================================================

class TestExperimentStore:
    def _store(self, tmp_path):
        return ExperimentStore(path=str(tmp_path))

    def test_save_creates_metadata_file(self, tmp_path):
        store = self._store(tmp_path)
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        meta = tmp_path / exp.id / "metadata.json"
        assert meta.exists()

    def test_load_returns_same_id(self, tmp_path):
        store = self._store(tmp_path)
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        loaded = store.load(exp.id)
        assert loaded.id == exp.id

    def test_load_missing_raises(self, tmp_path):
        store = self._store(tmp_path)
        with pytest.raises(ExperimentNotFound):
            store.load("nonexistent_id_xyz")

    def test_list_returns_saved_entry(self, tmp_path):
        store = self._store(tmp_path)
        exp = Experiment.from_provenance(_fake_provenance(), tags=["demo"])
        store.save(exp)
        entries = store.list()
        assert any(e["id"] == exp.id for e in entries)

    def test_list_tag_filter(self, tmp_path):
        store = self._store(tmp_path)
        e1 = Experiment.from_provenance(_fake_provenance(), tags=["alpha"])
        e2 = Experiment.from_provenance(
            _fake_provenance(engine="pipeline_step"), tags=["beta"]
        )
        store.save(e1)
        store.save(e2)
        result = store.list(tags=["alpha"])
        ids = [e["id"] for e in result]
        assert e1.id in ids
        assert e2.id not in ids

    def test_list_engine_filter(self, tmp_path):
        store = self._store(tmp_path)
        e1 = Experiment.from_provenance(_fake_provenance())
        e2 = Experiment.from_provenance(_fake_provenance(engine="pipeline_step"))
        store.save(e1)
        store.save(e2)
        result = store.list(engine="pipeline_step")
        assert all(e["engine"] == "pipeline_step" for e in result)

    def test_idempotent_save(self, tmp_path):
        store = self._store(tmp_path)
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        store.save(exp)  # save again – should not error or duplicate
        assert len(store.list()) == 1

    def test_delete_removes_entry(self, tmp_path):
        store = self._store(tmp_path)
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        store.delete(exp.id)
        with pytest.raises(ExperimentNotFound):
            store.load(exp.id)

    def test_list_limit(self, tmp_path):
        store = self._store(tmp_path)
        for i in range(5):
            p = _fake_provenance()
            p["network_fingerprint"]["node_count"] = i
            store.save(Experiment.from_provenance(p))
        assert len(store.list(limit=3)) == 3


# ===========================================================================
# runner.py – ExperimentRunner
# ===========================================================================

class TestExperimentRunner:
    def _runner(self, tmp_path):
        return ExperimentRunner(store=ExperimentStore(path=str(tmp_path)))

    def test_record_legacy_query_result(self, tmp_path):
        net = _small_net()
        result = execute_query(net, "SELECT nodes")
        runner = self._runner(tmp_path)
        exp = runner.record_query_result(result, tags=["legacy"])
        assert exp.id
        # check round-trip via store
        loaded = runner.store.load(exp.id)
        assert loaded.id == exp.id

    def test_record_dsl_v2_query_result(self, tmp_path):
        net = _small_net()
        result = Q.nodes().execute(net)
        runner = self._runner(tmp_path)
        exp = runner.record_query_result(result, tags=["v2"])
        assert exp.id
        loaded = runner.store.load(exp.id)
        assert loaded.engine != ""

    def test_reproduce_returns_experiment(self, tmp_path):
        """reproduce() should at minimum return the stored experiment."""
        net = _small_net()
        result = execute_query(net, "SELECT nodes")
        runner = self._runner(tmp_path)
        exp = runner.record_query_result(result, tags=["repro"])
        # reproduce with no network re-executes nothing but returns info
        repro = runner.reproduce(exp.id, network=None)
        assert repro is not None


# ===========================================================================
# DSL v2 QueryResult integration hook
# ===========================================================================

class TestQueryResultHook:
    def test_record_as_experiment_exists(self):
        net = _small_net()
        result = Q.nodes().execute(net)
        assert hasattr(result, "record_as_experiment")

    def test_record_as_experiment_stores_and_returns(self, tmp_path):
        net = _small_net()
        result = Q.nodes().execute(net)
        store = ExperimentStore(path=str(tmp_path))
        exp = result.record_as_experiment(store=store, tags=["hook-test"])
        assert exp.id
        loaded = store.load(exp.id)
        assert loaded.id == exp.id

    def test_determinism_across_identical_queries(self, tmp_path):
        """Two identical queries on the same network produce the same experiment ID."""
        net = _small_net()
        store = ExperimentStore(path=str(tmp_path))
        id1 = Q.nodes().execute(net).record_as_experiment(store=store).id
        id2 = Q.nodes().execute(net).record_as_experiment(store=store).id
        assert id1 == id2

    def test_different_query_different_id(self, tmp_path):
        net = _small_net()
        store = ExperimentStore(path=str(tmp_path))
        exp_a = Q.nodes().execute(net).record_as_experiment(store=store)
        exp_b = Q.edges().execute(net).record_as_experiment(store=store)
        assert exp_a.id != exp_b.id


# ===========================================================================
# Public convenience functions
# ===========================================================================

class TestPublicConvenienceFunctions:
    def test_register_default_store(self, tmp_path):
        store = register_default_store(path=str(tmp_path))
        assert isinstance(store, ExperimentStore)

    def test_list_experiments_uses_store(self, tmp_path):
        store = register_default_store(path=str(tmp_path))
        exp = Experiment.from_provenance(_fake_provenance(), tags=["pub"])
        store.save(exp)
        entries = list_experiments(store=store)
        assert any(e["id"] == exp.id for e in entries)

    def test_load_experiment_uses_store(self, tmp_path):
        store = register_default_store(path=str(tmp_path))
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        loaded = load_experiment(exp.id, store=store)
        assert loaded.id == exp.id

    def test_reproduce_experiment_stub(self, tmp_path):
        store = register_default_store(path=str(tmp_path))
        net = _small_net()
        result = Q.nodes().execute(net)
        runner = ExperimentRunner(store=store)
        exp = runner.record_query_result(result)
        # reproduce_experiment is a thin wrapper – just check it doesn't raise
        repro = reproduce_experiment(exp.id, store=store)
        assert repro is not None


# ===========================================================================
# CLI integration (subprocess)
# ===========================================================================

def _cli(*args, store_dir):
    """Run py3plex CLI with experiment subcommand."""
    cmd = [
        sys.executable, "-m", "py3plex",
        "experiment", f"--store-dir={store_dir}",
    ] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc


class TestCLI:
    def test_list_empty(self, tmp_path):
        proc = _cli("list", store_dir=str(tmp_path))
        assert proc.returncode == 0
        assert "No experiments found" in proc.stdout

    def test_list_shows_saved_experiment(self, tmp_path):
        store = ExperimentStore(path=str(tmp_path))
        exp = Experiment.from_provenance(_fake_provenance(), tags=["cli-test"])
        store.save(exp)
        proc = _cli("list", store_dir=str(tmp_path))
        assert proc.returncode == 0
        assert exp.id in proc.stdout

    def test_list_json_format(self, tmp_path):
        store = ExperimentStore(path=str(tmp_path))
        store.save(Experiment.from_provenance(_fake_provenance()))
        proc = _cli("list", "--format=json", store_dir=str(tmp_path))
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_show_existing(self, tmp_path):
        store = ExperimentStore(path=str(tmp_path))
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        proc = _cli("show", exp.id, store_dir=str(tmp_path))
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["id"] == exp.id

    def test_show_missing_returns_error(self, tmp_path):
        proc = _cli("show", "does_not_exist_xyz", store_dir=str(tmp_path))
        assert proc.returncode != 0

    def test_export_json(self, tmp_path):
        store = ExperimentStore(path=str(tmp_path))
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        out_file = tmp_path / "out.json"
        proc = _cli("export", exp.id, f"--output={out_file}", store_dir=str(tmp_path))
        assert proc.returncode == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["id"] == exp.id

    def test_export_csv(self, tmp_path):
        store = ExperimentStore(path=str(tmp_path))
        exp = Experiment.from_provenance(_fake_provenance())
        store.save(exp)
        out_file = tmp_path / "out.csv"
        proc = _cli(
            "export", exp.id, f"--output={out_file}", "--format=csv",
            store_dir=str(tmp_path),
        )
        assert proc.returncode == 0
        assert out_file.exists()
        text = out_file.read_text()
        assert "id" in text

    def test_run_command(self, tmp_path):
        net = _small_net()
        # serialise network to a tmp edgelist
        net_path = tmp_path / "net.csv"
        # multiedgelist uses whitespace-separated format: node1 layer1 node2 layer2
        net_path.write_text("A social B social\n")
        cfg = {
            "network": str(net_path),
            "input_type": "multiedgelist",
            "query": "SELECT nodes",
            "tags": ["cli-run"],
        }
        cfg_path = tmp_path / "cfg.json"
        cfg_path.write_text(json.dumps(cfg))
        proc = _cli("run", str(cfg_path), store_dir=str(tmp_path))
        assert proc.returncode == 0
        assert "Experiment recorded:" in proc.stdout

    def test_reproduce_command(self, tmp_path):
        store = ExperimentStore(path=str(tmp_path))
        net = _small_net()
        result = execute_query(net, "SELECT nodes")
        runner = ExperimentRunner(store=store)
        exp = runner.record_query_result(result)
        proc = _cli("reproduce", exp.id, store_dir=str(tmp_path))
        # returncode 0 or 2 are acceptable (2 = info / guidance)
        assert proc.returncode in (0, 2)
