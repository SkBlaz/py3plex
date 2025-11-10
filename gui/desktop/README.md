# Py3plex Desktop GUI

A modern, cross-platform desktop application for multilayer network analysis and visualization.

## Features

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Modern UI**: Built with PySide6 (Qt6) for native performance
- **Dark Mode**: Automatic theme switching with light and dark themes
- **HiDPI Support**: Crisp rendering on high-resolution displays
- **MVVM Architecture**: Clean separation of concerns for maintainability
- **Persistent Settings**: Remembers window size, theme, and recent files

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install from Repository

```bash
# Install py3plex with GUI dependencies
pip install -e ".[gui]"
```

Or install GUI dependencies separately:

```bash
pip install PySide6>=6.5.0 platformdirs>=3.0.0
```

## Running the Application

### Using the entry point (after installation):

```bash
py3plex-gui
```

### Using Python module:

```bash
python -m gui.desktop
```

### From source:

```bash
cd /path/to/py3plex
python -m gui.desktop.app
```

## Architecture

The desktop GUI follows **MVVM (Model-View-ViewModel)** architecture for clean separation of concerns:

```
gui/desktop/
├── app.py                 # Application bootstrap & entry point
├── main_window.py         # Main window with menus & toolbars
├── design_system.py       # Design tokens (colors, spacing, typography)
├── themes/                # QSS stylesheets
│   ├── light.qss
│   └── dark.qss
├── services/              # Business logic layer
│   ├── logger.py          # Logging service
│   ├── preferences.py     # Settings persistence
│   ├── io_service.py      # (Future) File I/O operations
│   └── algorithms_service.py  # (Future) Algorithm execution
├── views/                 # (Future) UI views
│   ├── home_view.py
│   ├── dataset_view.py
│   ├── analysis_view.py
│   └── visualization_view.py
├── viewmodels/            # (Future) View state management
├── components/            # (Future) Reusable UI components
└── resources/             # Icons, assets, sample data
```

## Configuration

Application settings are stored in platform-specific locations:

- **Linux**: `~/.config/py3plex/preferences.json`
- **macOS**: `~/Library/Application Support/py3plex/preferences.json`
- **Windows**: `%APPDATA%\py3plex\preferences.json`

Logs are stored in:

- **Linux**: `~/.local/share/py3plex/logs/gui.log`
- **macOS**: `~/Library/Logs/py3plex/gui.log`
- **Windows**: `%LOCALAPPDATA%\py3plex\logs\gui.log`

## Keyboard Shortcuts

- `Ctrl/Cmd+O` - Open file
- `Ctrl/Cmd+E` - Export results
- `Ctrl/Cmd+Q` - Quit application
- `Ctrl/Cmd+,` - Preferences
- `Ctrl/Cmd+T` - Toggle theme
- `F1` - (Future) Command palette

## Development Status

### ✅ Implemented (Phases 1-2)

- Application bootstrap with DPI awareness
- Main window with menu bar and toolbar
- Theme system (light/dark with QSS)
- Preferences service with persistence
- Logging service with file rotation
- Window geometry restoration
- Design system (colors, spacing, typography)
- **I/O service with multi-format support**
- **Algorithms service with 6 algorithms**
- **File loading with progress tracking**
- **Metadata display**

### 🚧 In Progress

- Network visualization canvas
- Algorithm execution with progress tracking
- Inspector panel for node/edge properties

### 📋 Planned (Future Phases)

- MVVM view/viewmodel implementation
- Drag-and-drop file loading
- Interactive graph visualization with pan/zoom
- Algorithm parameter forms
- Export functionality (CSV, JSON, images)
- Command palette (F1)
- Recent files menu
- Comprehensive keyboard shortcuts
- Integration tests

## Testing

The desktop GUI services can be tested independently:

```python
# Test I/O service
from gui.desktop.services.io_service import get_io_service

io = get_io_service()
graph = io.load_graph("path/to/network.gml")
metadata = io.get_metadata()
print(f"Nodes: {metadata['nodes']}, Edges: {metadata['edges']}")
```

```python
# Test algorithms service
from gui.desktop.services.algorithms_service import get_algorithms_service

algos = get_algorithms_service()
for algo in algos.get_algorithms():
    print(f"{algo.name} - {algo.description}")

# Run an algorithm
result = algos.run_algorithm(graph, "degree_centrality")
```

Unit tests for services are located in `tests/gui/` (when installed in development mode).

## Contributing

When adding new features:

1. Follow MVVM architecture patterns
2. Use the design system (`design_system.py`) for consistent styling
3. Add logging statements for debugging
4. Keep business logic in `services/` layer
5. UI code should be in `views/` with state in `viewmodels/`
6. Use PySide6's signals/slots for async operations
7. Update this README with new features

## License

MIT License - see LICENSE file in repository root.

## Author

Blaž Škrlj - [GitHub](https://github.com/SkBlaz/py3plex)
