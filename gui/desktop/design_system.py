"""
Design System - Central definition of visual design tokens.

Provides consistent spacing, typography, colors, and icon registry
for the entire application.
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class SpacingScale:
    """Spacing scale following 8px base unit."""
    
    xs: int = 4   # 0.5 * 8px
    sm: int = 8   # 1 * 8px
    md: int = 16  # 2 * 8px
    lg: int = 24  # 3 * 8px
    xl: int = 32  # 4 * 8px
    xxl: int = 48 # 6 * 8px


@dataclass
class Typography:
    """Typography scale with font sizes."""
    
    # Font families
    sans: str = "Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif"
    mono: str = "Consolas, Monaco, 'Courier New', monospace"
    
    # Font sizes
    xs: int = 11
    sm: int = 12
    base: int = 14
    lg: int = 16
    xl: int = 20
    xxl: int = 24
    title: int = 28


@dataclass
class ColorTokens:
    """Color tokens for light and dark themes."""
    
    # Light theme colors
    light_primary: str = "#0066cc"
    light_primary_hover: str = "#0052a3"
    light_secondary: str = "#6c757d"
    light_success: str = "#28a745"
    light_warning: str = "#ffc107"
    light_danger: str = "#dc3545"
    light_info: str = "#17a2b8"
    
    light_bg_primary: str = "#ffffff"
    light_bg_secondary: str = "#f8f9fa"
    light_bg_tertiary: str = "#e9ecef"
    
    light_text_primary: str = "#212529"
    light_text_secondary: str = "#6c757d"
    light_text_disabled: str = "#adb5bd"
    
    light_border: str = "#dee2e6"
    light_border_focus: str = "#80bdff"
    
    # Dark theme colors
    dark_primary: str = "#4d9eff"
    dark_primary_hover: str = "#6fb0ff"
    dark_secondary: str = "#adb5bd"
    dark_success: str = "#4caf50"
    dark_warning: str = "#ffb74d"
    dark_danger: str = "#ef5350"
    dark_info: str = "#29b6f6"
    
    dark_bg_primary: str = "#1e1e1e"
    dark_bg_secondary: str = "#2d2d2d"
    dark_bg_tertiary: str = "#3e3e3e"
    
    dark_text_primary: str = "#e0e0e0"
    dark_text_secondary: str = "#b0b0b0"
    dark_text_disabled: str = "#6c6c6c"
    
    dark_border: str = "#4a4a4a"
    dark_border_focus: str = "#4d9eff"


class IconRegistry:
    """Registry for icon paths and symbols."""
    
    # Using Unicode symbols for now; can be replaced with SVG/PNG later
    ICONS: Dict[str, str] = {
        "open": "📁",
        "save": "💾",
        "export": "📤",
        "settings": "⚙️",
        "run": "▶️",
        "pause": "⏸️",
        "stop": "⏹️",
        "cancel": "❌",
        "refresh": "🔄",
        "search": "🔍",
        "filter": "🔎",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "graph": "📊",
        "network": "🕸️",
        "node": "⭕",
        "edge": "↔️",
        "community": "👥",
        "metrics": "📈",
        "layout": "🎨",
        "zoom_in": "🔍+",
        "zoom_out": "🔍-",
        "fit": "⬜",
        "help": "❓",
        "close": "✖️",
        "minimize": "➖",
        "maximize": "⬜",
    }
    
    @classmethod
    def get(cls, icon_name: str) -> str:
        """Get icon by name."""
        return cls.ICONS.get(icon_name, "•")


# Singleton instances
spacing = SpacingScale()
typography = Typography()
colors = ColorTokens()
icons = IconRegistry()
