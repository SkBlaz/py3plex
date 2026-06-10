"""Environment fingerprinting for experiment reproducibility.

Captures Python version, platform, and key library versions so that two
experiments executed in different environments can be distinguished.

The ``env_hash`` field is derived from the *stable* subset of the fingerprint
(i.e. everything except volatile run-time data like hostname or PID).
"""

import platform
from typing import Dict, Optional

from .utils import stable_hash


def _safe_version(module_name: str) -> Optional[str]:
    """Import *module_name* and return its ``__version__`` attribute, or None."""
    try:
        import importlib

        mod = importlib.import_module(module_name)
        return getattr(mod, "__version__", None)
    except ImportError:
        return None


def get_environment_fingerprint() -> Dict[str, object]:
    """Return a dictionary describing the current execution environment.

    The returned dict contains:

    * ``python`` – ``major.minor.micro`` string.
    * ``platform`` – ``platform.platform()`` string.
    * ``numpy``, ``pandas``, ``networkx``, ``pyarrow`` – version strings or
      ``None`` when the library is not installed.
    * ``py3plex`` – py3plex version string.
    * ``env_hash`` – stable SHA-256 prefix derived from the above fields
      (excluding ``platform`` which can change between machines running the
      same code, and thus is stored for information but not hashed).

    Returns:
        Dict with environment metadata and a deterministic ``env_hash``.
    """
    py_ver = platform.python_version()
    plat = platform.platform()

    deps: Dict[str, Optional[str]] = {
        "numpy": _safe_version("numpy"),
        "pandas": _safe_version("pandas"),
        "networkx": _safe_version("networkx"),
        "pyarrow": _safe_version("pyarrow"),
    }

    py3plex_ver = _safe_version("py3plex") or "unknown"

    # Hash only stable fields (versions), not host-specific platform string
    hashable = {
        "python": py_ver,
        "py3plex_version": py3plex_ver,
        "deps": {k: v for k, v in sorted(deps.items())},
    }
    env_hash = stable_hash(hashable, length=16)

    return {
        "python": py_ver,
        "platform": plat,
        "numpy": deps["numpy"],
        "networkx": deps["networkx"],
        "pandas": deps.get("pandas"),
        "pyarrow": deps.get("pyarrow"),
        "py3plex_version": py3plex_ver,
        "deps": deps,
        "env_hash": env_hash,
    }
