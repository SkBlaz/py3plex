"""
Preferences Service - Persistent application settings.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field

try:
    from platformdirs import user_config_dir
except ImportError:
    # Fallback if platformdirs not installed
    def user_config_dir(appname: str, appauthor: str) -> str:
        return str(Path.home() / ".config" / appname)


@dataclass
class Preferences:
    """Application preferences data class."""

    # Appearance
    theme: str = "light"  # "light" or "dark"
    font_scale: float = 1.0

    # Paths
    last_directory: str = ""
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10

    # Window
    window_geometry: Optional[Dict[str, int]] = None
    window_maximized: bool = False

    # Performance
    max_nodes_for_labels: int = 1000
    enable_antialiasing: bool = True
    enable_animations: bool = True

    # Algorithms
    default_layout: str = "spring"
    default_community_algorithm: str = "louvain"


class PreferencesService:
    """Service for managing application preferences."""

    def __init__(self):
        """Initialize preferences service."""
        self.config_dir = Path(user_config_dir("py3plex", "SkBlaz"))
        self.config_file = self.config_dir / "preferences.json"
        self._preferences = self._load()

    def _load(self) -> Preferences:
        """Load preferences from disk."""
        if not self.config_file.exists():
            return Preferences()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Preferences(**data)
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return Preferences()

    def save(self) -> None:
        """Save preferences to disk."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._preferences), f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")

    @property
    def preferences(self) -> Preferences:
        """Get current preferences."""
        return self._preferences

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value by key."""
        return getattr(self._preferences, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a preference value by key."""
        if hasattr(self._preferences, key):
            setattr(self._preferences, key, value)
            self.save()

    def add_recent_file(self, filepath: str) -> None:
        """Add a file to recent files list."""
        # Remove if already in list
        if filepath in self._preferences.recent_files:
            self._preferences.recent_files.remove(filepath)

        # Add to beginning
        self._preferences.recent_files.insert(0, filepath)

        # Limit list size
        max_files = self._preferences.max_recent_files
        self._preferences.recent_files = (
            self._preferences.recent_files[:max_files]
        )

        self.save()

    def clear_recent_files(self) -> None:
        """Clear recent files list."""
        self._preferences.recent_files = []
        self.save()

    def get_recent_files(self) -> List[str]:
        """Get list of recent files that still exist."""
        # Filter out files that no longer exist
        existing = [f for f in self._preferences.recent_files if Path(f).exists()]

        # Update list if any were removed
        if len(existing) != len(self._preferences.recent_files):
            self._preferences.recent_files = existing
            self.save()

        return existing

    def set_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """Save window geometry."""
        self._preferences.window_geometry = {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
        self.save()

    def get_window_geometry(self) -> Optional[Dict[str, int]]:
        """Get saved window geometry."""
        return self._preferences.window_geometry

    def set_theme(self, theme: str) -> None:
        """Set theme preference."""
        if theme in ("light", "dark"):
            self._preferences.theme = theme
            self.save()

    def toggle_theme(self) -> str:
        """Toggle between light and dark theme."""
        new_theme = "dark" if self._preferences.theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme
