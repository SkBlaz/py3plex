"""
Application Bootstrap - Main entry point for the desktop GUI.

Handles DPI awareness, theme initialization, single-instance guard,
and global exception handling.
"""

import sys
import traceback
from typing import Optional

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False
    print("PySide6 not installed. Install with: pip install PySide6")

from pathlib import Path

from .services.logger import get_logger
from .services.preferences import PreferencesService


logger = get_logger()


class Application:
    """Main application class."""

    def __init__(self):
        """Initialize the application."""
        self.app: Optional[QApplication] = None
        self.main_window = None
        self.preferences = PreferencesService()

    def setup(self) -> None:
        """Set up the application."""
        if not HAS_PYSIDE6:
            raise RuntimeError("PySide6 is required but not installed")

        # Enable HiDPI support
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Py3plex Desktop")
        self.app.setOrganizationName("SkBlaz")
        self.app.setOrganizationDomain("github.com/SkBlaz/py3plex")

        # Set up global exception handler
        sys.excepthook = self._handle_exception

        logger.info("Application initialized")

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Global exception handler."""
        # Log the exception
        logger.error(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        # Format error message
        error_msg = ''.join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )

        # Show error dialog
        if self.app:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText("An unexpected error occurred")
            msg_box.setInformativeText(str(exc_value))
            msg_box.setDetailedText(error_msg)
            msg_box.exec()

    def load_theme(self) -> None:
        """Load and apply theme."""
        if not self.app:
            return

        theme = self.preferences.get("theme", "light")
        theme_file = Path(__file__).parent / "themes" / f"{theme}.qss"

        if theme_file.exists():
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                    self.app.setStyleSheet(stylesheet)
                    logger.info(f"Loaded {theme} theme")
            except Exception as e:
                logger.error(f"Error loading theme: {e}")
        else:
            logger.warning(f"Theme file not found: {theme_file}")

    def create_main_window(self):
        """Create and show the main window."""
        # Import here to avoid circular imports
        from .main_window import MainWindow

        self.main_window = MainWindow(self)

        # Restore window geometry
        geometry = self.preferences.get_window_geometry()
        if geometry:
            self.main_window.setGeometry(
                geometry["x"],
                geometry["y"],
                geometry["width"],
                geometry["height"]
            )
        else:
            # Default size
            self.main_window.resize(1400, 900)
            # Center on screen
            screen = self.app.primaryScreen().geometry()
            x = (screen.width() - 1400) // 2
            y = (screen.height() - 900) // 2
            self.main_window.move(x, y)

        if self.preferences.get("window_maximized", False):
            self.main_window.showMaximized()
        else:
            self.main_window.show()

        logger.info("Main window created and shown")

    def run(self) -> int:
        """Run the application."""
        if not self.app:
            logger.error("Application not initialized")
            return 1

        return self.app.exec()

    def quit(self):
        """Quit the application."""
        # Save window geometry before quitting
        if self.main_window:
            geo = self.main_window.geometry()
            self.preferences.set_window_geometry(
                geo.x(), geo.y(), geo.width(), geo.height()
            )
            self.preferences.set("window_maximized", self.main_window.isMaximized())

        if self.app:
            self.app.quit()


def main() -> int:
    """Main entry point."""
    try:
        app = Application()
        app.setup()
        app.load_theme()
        app.create_main_window()
        return app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
