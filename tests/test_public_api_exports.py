"""Tests for top-level py3plex public API exports."""
import pytest


def _import_py3plex_or_skip():
    """Import py3plex or skip when optional heavy deps are unavailable."""
    try:
        import py3plex
    except ModuleNotFoundError as exc:
        if exc.name in {"matplotlib"}:
            pytest.skip(f"optional dependency missing for top-level import: {exc.name}")
        raise
    return py3plex


def test_config_exported_from_main_package():
    """config should be exported from top-level py3plex package."""
    py3plex = _import_py3plex_or_skip()

    assert "config" in py3plex.__all__
    assert hasattr(py3plex, "config")

    from py3plex import config as config_from_main
    import py3plex.config as config_module

    assert config_from_main is config_module


def test_io_convenience_functions_exported_from_main_package():
    """Arrow/Parquet convenience I/O functions should be top-level exports."""
    py3plex = _import_py3plex_or_skip()

    names = [
        "save_to_arrow",
        "load_from_arrow",
        "save_network_to_parquet",
        "load_network_from_parquet",
    ]

    for name in names:
        assert name in py3plex.__all__
        assert hasattr(py3plex, name)
        assert callable(getattr(py3plex, name))


def test_io_convenience_functions_match_io_module():
    """Top-level I/O convenience exports should match py3plex.io objects."""
    _import_py3plex_or_skip()
    from py3plex import (
        load_from_arrow,
        load_network_from_parquet,
        save_network_to_parquet,
        save_to_arrow,
    )
    from py3plex.io import (
        load_from_arrow as io_load_from_arrow,
        load_network_from_parquet as io_load_network_from_parquet,
        save_network_to_parquet as io_save_network_to_parquet,
        save_to_arrow as io_save_to_arrow,
    )

    assert save_to_arrow is io_save_to_arrow
    assert load_from_arrow is io_load_from_arrow
    assert save_network_to_parquet is io_save_network_to_parquet
    assert load_network_from_parquet is io_load_network_from_parquet
