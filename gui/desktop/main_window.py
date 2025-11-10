"""
Main Window - Primary application window with menus, toolbars, and panels.
"""

from typing import TYPE_CHECKING

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
        QMessageBox, QFileDialog, QSplitter
    )
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QAction, QKeySequence
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False

from .services.logger import get_logger
from .services.io_service import get_io_service
from .design_system import icons
from .components.progress_dialog import ProgressDialog

if TYPE_CHECKING:
    from .app import Application

logger = get_logger()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, app: "Application"):
        """Initialize main window."""
        super().__init__()

        self.application = app
        self.preferences = app.preferences

        self.setWindowTitle("Py3plex Desktop - Multilayer Network Analysis")
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._connect_signals()

        logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface layout."""
        # Central widget with splitter layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # Left panel (navigation/file browser) - for future implementation
        self.left_panel = QWidget()
        self.left_panel.setMinimumWidth(200)
        self.left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.addWidget(QLabel("📁 Files"))
        left_layout.addStretch()

        # Center panel (main content area)
        self.center_panel = QWidget()
        center_layout = QVBoxLayout(self.center_panel)

        # Welcome message
        welcome_label = QLabel("Welcome to Py3plex Desktop")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 40px;")
        center_layout.addWidget(welcome_label)

        instructions = QLabel(
            "🕸️ Multilayer Network Analysis\n\n"
            "Get started:\n"
            "• File → Open to load a network\n"
            "• Or drag and drop a file here\n\n"
            "Supported formats: edgelist, GML, GraphML, pickle"
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 20px;")
        center_layout.addWidget(instructions)
        center_layout.addStretch()

        # Right panel (inspector/properties) - for future implementation
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(200)
        self.right_panel.setMaximumWidth(400)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.addWidget(QLabel("ℹ️ Inspector"))
        right_layout.addStretch()

        # Add panels to splitter
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.center_panel)
        self.main_splitter.addWidget(self.right_panel)

        # Set initial splitter sizes (20% - 60% - 20%)
        self.main_splitter.setSizes([280, 840, 280])

    def _create_menus(self) -> None:
        """Create application menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction(f"{icons.get('open')} &Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a network file")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Recent files submenu (placeholder)
        recent_menu = file_menu.addMenu("Recent Files")
        recent_menu.setEnabled(False)

        file_menu.addSeparator()

        export_action = QAction(f"{icons.get('export')} &Export...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setStatusTip("Export results")
        export_action.setEnabled(False)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.setStatusTip("Quit application")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        preferences_action = QAction(f"{icons.get('settings')} &Preferences...", self)
        preferences_action.setShortcut(QKeySequence.Preferences)
        preferences_action.setStatusTip("Open preferences")
        preferences_action.triggered.connect(self._on_preferences)
        edit_menu.addAction(preferences_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        toggle_theme_action = QAction("Toggle &Theme", self)
        toggle_theme_action.setShortcut(QKeySequence("Ctrl+T"))
        toggle_theme_action.setStatusTip("Toggle between light and dark theme")
        toggle_theme_action.triggered.connect(self._on_toggle_theme)
        view_menu.addAction(toggle_theme_action)

        view_menu.addSeparator()

        # Panel visibility toggles
        left_panel_action = QAction("Show &Files Panel", self, checkable=True)
        left_panel_action.setChecked(True)
        left_panel_action.triggered.connect(lambda checked: self.left_panel.setVisible(checked))
        view_menu.addAction(left_panel_action)

        right_panel_action = QAction("Show &Inspector Panel", self, checkable=True)
        right_panel_action.setChecked(True)
        right_panel_action.triggered.connect(lambda checked: self.right_panel.setVisible(checked))
        view_menu.addAction(right_panel_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.setStatusTip("About Py3plex Desktop")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self) -> None:
        """Create main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Open button
        open_action = QAction(icons.get("open"), "Open", self)
        open_action.setToolTip("Open network file")
        open_action.triggered.connect(self._on_open)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # Run button
        run_action = QAction(icons.get("run"), "Run", self)
        run_action.setToolTip("Run analysis")
        run_action.setEnabled(False)
        toolbar.addAction(run_action)

        toolbar.addSeparator()

        # Settings button
        settings_action = QAction(icons.get("settings"), "Settings", self)
        settings_action.setToolTip("Preferences")
        settings_action.triggered.connect(self._on_preferences)
        toolbar.addAction(settings_action)

    def _create_status_bar(self) -> None:
        """Create status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Status message
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)

        # Right-side indicators
        status_bar.addPermanentWidget(QLabel(f"Theme: {self.preferences.get('theme')}"))

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        pass  # Signals will be connected as features are implemented

    def _on_open(self) -> None:
        """Handle open file action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Network File",
            self.preferences.get("last_directory", ""),
            "Network Files (*.edgelist *.gml *.graphml *.gpickle *.pkl);;All Files (*)"
        )

        if file_path:
            logger.info(f"Selected file: {file_path}")

            # Save last directory
            from pathlib import Path
            self.preferences.set("last_directory", str(Path(file_path).parent))
            self.preferences.add_recent_file(file_path)

            # Load the file
            self._load_file(file_path)

    def _load_file(self, filepath: str) -> None:
        """Load a network file."""
        io_service = get_io_service()

        # Validate file first
        is_valid, error_msg = io_service.validate_file(filepath)
        if not is_valid:
            QMessageBox.critical(
                self,
                "Invalid File",
                f"Cannot load file: {error_msg}"
            )
            return

        # Create progress dialog
        progress = ProgressDialog("Loading Network", self)

        # Progress callback
        def update_progress(percent: int, message: str):
            progress.set_progress(percent, message)
            # Process events to keep UI responsive
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

        progress.show()

        # Load graph
        graph = io_service.load_graph(filepath, update_progress)

        progress.accept()

        if graph:
            # Show metadata
            metadata = io_service.get_metadata()
            info_text = f"Loaded: {Path(filepath).name}\n\n"
            info_text += f"Nodes: {metadata.get('nodes', 0)}\n"
            info_text += f"Edges: {metadata.get('edges', 0)}\n"
            info_text += f"Directed: {metadata.get('directed', False)}\n"

            if 'density' in metadata:
                info_text += f"Density: {metadata['density']:.4f}\n"
            if 'components' in metadata:
                info_text += f"Components: {metadata['components']}\n"

            self.status_label.setText(f"Loaded: {metadata.get('nodes', 0)} nodes, {metadata.get('edges', 0)} edges")

            QMessageBox.information(
                self,
                "Network Loaded",
                info_text
            )
        else:
            QMessageBox.critical(
                self,
                "Load Failed",
                "Failed to load network file. Check logs for details."
            )

    def _on_preferences(self) -> None:
        """Handle preferences action."""
        QMessageBox.information(
            self,
            "Preferences",
            "Preferences dialog will be implemented in next phase."
        )

    def _on_toggle_theme(self) -> None:
        """Handle theme toggle action."""
        new_theme = self.preferences.toggle_theme()
        self.application.load_theme()
        self.status_label.setText(f"Theme changed to: {new_theme}")
        logger.info(f"Theme toggled to: {new_theme}")

    def _on_about(self) -> None:
        """Handle about action."""
        QMessageBox.about(
            self,
            "About Py3plex Desktop",
            "<h2>Py3plex Desktop</h2>"
            "<p>Version 2.0.0</p>"
            "<p>A desktop GUI for multilayer network analysis and visualization.</p>"
            "<p>Built with PySide6 and Qt6</p>"
            "<p><b>Author:</b> Blaž Škrlj</p>"
            "<p><b>License:</b> MIT</p>"
            "<p><a href='https://github.com/SkBlaz/py3plex'>GitHub Repository</a></p>"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        # Save preferences before closing
        geo = self.geometry()
        self.preferences.set_window_geometry(geo.x(), geo.y(), geo.width(), geo.height())
        self.preferences.set("window_maximized", self.isMaximized())

        logger.info("Application closing")
        event.accept()
