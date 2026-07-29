#!/usr/bin/env python3
"""
Property-based tests for the experiments module.

Tests Experiment dataclass construction, ID computation, serialisation
round-trips, and tag/notes handling.
"""

import pytest
from hypothesis import given, settings, strategies as st

# Import experiments module
try:
    from py3plex.experiments import Experiment, ExperimentStore, ExperimentRunner
    EXPERIMENTS_AVAILABLE = True
except ImportError:
    EXPERIMENTS_AVAILABLE = False
    pytest.skip("experiments module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

_short_str = st.text(
    min_size=0, max_size=40,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" _.-:"),
)
_tag = st.text(
    min_size=1, max_size=20,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
)
_tags = st.lists(_tag, min_size=0, max_size=6)
_simple_dict = st.fixed_dictionaries({"key": _short_str})


# ---------------------------------------------------------------------------
# Experiment construction
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_experiment_default_creation():
    """Experiment can be created with all defaults."""
    exp = Experiment()
    assert exp.id == ""
    assert exp.engine == ""
    assert exp.tags == []
    assert exp.notes is None
    assert exp.query == {}
    assert exp.randomness == {}
    assert exp.backend == {}
    assert exp.network_fingerprint == {}
    assert exp.environment == {}
    assert exp.performance == {}
    assert exp.artifacts == {}


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(engine=_short_str)
def test_experiment_stores_engine(engine):
    """Experiment stores the engine string."""
    exp = Experiment(engine=engine)
    assert exp.engine == engine


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(notes=st.one_of(st.none(), _short_str))
def test_experiment_stores_notes(notes):
    """Experiment stores the notes field (may be None)."""
    exp = Experiment(notes=notes)
    assert exp.notes == notes


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(tags=_tags)
def test_experiment_stores_tags(tags):
    """Experiment stores the tags list."""
    exp = Experiment(tags=tags)
    assert exp.tags == tags


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(version=_short_str)
def test_experiment_stores_py3plex_version(version):
    """Experiment stores the py3plex_version string."""
    exp = Experiment(py3plex_version=version)
    assert exp.py3plex_version == version


# ---------------------------------------------------------------------------
# Experiment.compute_id
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(engine=_short_str, version=_short_str)
def test_compute_id_returns_string(engine, version):
    """compute_id() returns a non-empty string."""
    exp = Experiment(engine=engine, py3plex_version=version)
    exp_id = exp.compute_id()
    assert isinstance(exp_id, str)
    assert len(exp_id) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(engine=_short_str, version=_short_str)
def test_compute_id_deterministic(engine, version):
    """Calling compute_id() twice on same data produces the same ID."""
    exp1 = Experiment(engine=engine, py3plex_version=version)
    exp2 = Experiment(engine=engine, py3plex_version=version)
    assert exp1.compute_id() == exp2.compute_id()


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(engine1=_short_str, engine2=_short_str)
def test_compute_id_differs_for_different_engine(engine1, engine2):
    """compute_id() generally differs when engine differs."""
    from hypothesis import assume
    assume(engine1 != engine2)
    id1 = Experiment(engine=engine1).compute_id()
    id2 = Experiment(engine=engine2).compute_id()
    # IDs should differ (though hash collisions are theoretically possible, very unlikely)
    assert id1 != id2


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(engine=_short_str, version=_short_str)
def test_compute_id_sets_id_full_longer(engine, version):
    """compute_id() sets id_full to a string at least as long as id."""
    exp = Experiment(engine=engine, py3plex_version=version)
    exp.compute_id()
    assert len(exp.id_full) >= len(exp.id)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(engine=_short_str, version=_short_str)
def test_compute_id_id_is_prefix_of_id_full(engine, version):
    """id should be the first N characters of id_full."""
    exp = Experiment(engine=engine, py3plex_version=version)
    exp.compute_id()
    assert exp.id_full.startswith(exp.id)


# ---------------------------------------------------------------------------
# Experiment.to_dict / from_dict round-trip
# ---------------------------------------------------------------------------


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(engine=_short_str, tags=_tags)
def test_to_dict_round_trip(engine, tags):
    """Experiment.to_dict() followed by from_dict() recovers the same fields."""
    exp = Experiment(engine=engine, tags=tags)
    d = exp.to_dict()
    exp2 = Experiment.from_dict(d)
    assert exp2.engine == exp.engine
    assert exp2.tags == exp.tags


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(engine=_short_str)
def test_to_dict_returns_dict(engine):
    """Experiment.to_dict() returns a plain dict."""
    exp = Experiment(engine=engine)
    d = exp.to_dict()
    assert isinstance(d, dict)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(engine=_short_str)
def test_to_dict_has_expected_keys(engine):
    """Experiment.to_dict() includes standard top-level keys."""
    exp = Experiment(engine=engine)
    d = exp.to_dict()
    for key in ("id", "id_full", "engine", "py3plex_version", "tags", "notes", "query"):
        assert key in d, f"Expected key '{key}' in Experiment.to_dict() result"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(notes=st.one_of(st.none(), _short_str))
def test_to_dict_preserves_notes_none_or_str(notes):
    """Experiment.to_dict() preserves notes as None or a string."""
    exp = Experiment(notes=notes)
    d = exp.to_dict()
    assert d["notes"] == notes


# ---------------------------------------------------------------------------
# Experiment – dict fields remain dicts
# ---------------------------------------------------------------------------


@pytest.mark.property
def test_experiment_dict_fields_are_dicts():
    """All dict-typed fields return dicts in to_dict()."""
    exp = Experiment()
    d = exp.to_dict()
    for key in ("query", "randomness", "backend", "network_fingerprint",
                "environment", "performance", "artifacts"):
        assert isinstance(d[key], dict), f"Expected dict for key '{key}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
