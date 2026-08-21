import logging
import uuid

from py3plex.logging_config import get_logger, setup_logging


def _unique_logger_name(prefix: str = "unit") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def test_get_logger_none_returns_py3plex_root():
    logger = get_logger(None)
    assert logger.name == "py3plex"


def test_get_logger_prefixes_non_py3plex_names():
    name = _unique_logger_name("module")
    logger = get_logger(name)
    assert logger.name == f"py3plex.{name}"


def test_get_logger_keeps_existing_py3plex_prefix():
    name = f"py3plex.{_unique_logger_name('already')}"
    logger = get_logger(name)
    assert logger.name == name


def test_get_logger_does_not_add_duplicate_handlers_or_reset_level():
    name = _unique_logger_name("dedup")
    logger_first = get_logger(name, level=logging.DEBUG)
    handlers_before = len(logger_first.handlers)

    logger_second = get_logger(name, level=logging.ERROR)

    assert logger_first is logger_second
    assert len(logger_second.handlers) == handlers_before
    # level should remain from first configuration path
    assert logger_second.level == logging.DEBUG


def test_setup_logging_uses_default_format(monkeypatch):
    captured = {}

    def fake_basic_config(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)

    logger = setup_logging(level=logging.WARNING)

    assert logger.name == "py3plex"
    assert captured["level"] == logging.WARNING
    assert captured["format"] == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    assert captured["datefmt"] == "%Y-%m-%d %H:%M:%S"


def test_setup_logging_passes_custom_format(monkeypatch):
    captured = {}

    def fake_basic_config(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)

    custom = "%(levelname)s|%(message)s"
    setup_logging(level=logging.INFO, format_string=custom)

    assert captured["format"] == custom
