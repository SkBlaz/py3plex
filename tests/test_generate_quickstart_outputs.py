import runpy
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "docfiles" / "generate_quickstart_outputs.py"
EXPECTED_DEPRECATION_OUTPUT = "\n".join(
    [
        "=" * 70,
        "ERROR: This script is DEPRECATED and should not be executed.",
        "=" * 70,
        "",
        "The quickstart.rst file has been removed and consolidated into:",
        "  docfiles/getting_started/quickstart_5min.rst",
        "",
        "If you need to regenerate outputs for the new quickstart file,",
        "please create a new script or update this one to reference the",
        "new file structure.",
        "",
        "=" * 70,
        "",
    ]
)


def test_script_exits_with_deprecation_message():
    result = subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 1
    assert "ERROR: This script is DEPRECATED and should not be executed." in result.stdout
    assert "docfiles/getting_started/quickstart_5min.rst" in result.stdout
    assert "QUICKSTART SNIPPET OUTPUTS" not in result.stdout
    assert result.stderr == ""


def test_runpath_raises_system_exit_before_body(capfd):
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(str(SCRIPT_PATH))

    captured = capfd.readouterr()
    assert excinfo.value.code == 1
    assert "ERROR: This script is DEPRECATED and should not be executed." in captured.out
    assert "QUICKSTART SNIPPET OUTPUTS" not in captured.out


def test_deprecation_message_is_exact():
    result = subprocess.run([sys.executable, str(SCRIPT_PATH)], capture_output=True, text=True)

    assert result.returncode == 1
    assert result.stdout == EXPECTED_DEPRECATION_OUTPUT


def test_runpath_exits_before_importing_py3plex(capfd):
    original = sys.modules.pop("py3plex.core.multinet", None)
    try:
        with pytest.raises(SystemExit):
            runpy.run_path(str(SCRIPT_PATH))
    finally:
        captured = capfd.readouterr()
        if original is not None:
            sys.modules["py3plex.core.multinet"] = original
        else:
            sys.modules.pop("py3plex.core.multinet", None)

    assert "ERROR: This script is DEPRECATED and should not be executed." in captured.out
    if original is None:
        assert "py3plex.core.multinet" not in sys.modules
    else:
        assert sys.modules["py3plex.core.multinet"] is original
