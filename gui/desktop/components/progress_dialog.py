"""
Progress Dialog - Cancelable progress dialog for long-running operations.
"""

from typing import Optional

try:
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
    from PySide6.QtCore import Qt, Signal
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False
    # Create dummy base class when PySide6 not available
    class QDialog:
        pass
    class Signal:
        def __init__(self):
            pass


if HAS_PYSIDE6:
    class ProgressDialog(QDialog):
        """A cancelable progress dialog."""
        
        # Signal emitted when user cancels
        cancelled = Signal()
        
        def __init__(self, title: str = "Progress", parent=None):
            """Initialize progress dialog."""
            super().__init__(parent)
            
            self.setWindowTitle(title)
            self.setModal(True)
            self.setMinimumWidth(400)
            
            # Prevent closing with X button
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowCloseButtonHint
            )
            
            self._setup_ui()
            self._is_cancelled = False
        
        def _setup_ui(self) -> None:
            """Set up the user interface."""
            layout = QVBoxLayout(self)
            layout.setSpacing(16)
            
            # Status label
            self.status_label = QLabel("Initializing...")
            self.status_label.setWordWrap(True)
            layout.addWidget(self.status_label)
            
            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            layout.addWidget(self.progress_bar)
            
            # Detail label (optional additional info)
            self.detail_label = QLabel("")
            self.detail_label.setWordWrap(True)
            self.detail_label.setStyleSheet("color: #6c757d; font-size: 12px;")
            layout.addWidget(self.detail_label)
            
            # Cancel button
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self._on_cancel)
            layout.addWidget(self.cancel_button)
        
        def set_progress(self, percent: int, message: str = "") -> None:
            """
            Update progress.
            
            Args:
                percent: Progress percentage (0-100)
                message: Status message
            """
            self.progress_bar.setValue(percent)
            if message:
                self.status_label.setText(message)
        
        def set_detail(self, detail: str) -> None:
            """Set detail message."""
            self.detail_label.setText(detail)
        
        def set_indeterminate(self, indeterminate: bool = True) -> None:
            """Set progress bar to indeterminate mode."""
            if indeterminate:
                self.progress_bar.setMinimum(0)
                self.progress_bar.setMaximum(0)
            else:
                self.progress_bar.setMinimum(0)
                self.progress_bar.setMaximum(100)
        
        def _on_cancel(self) -> None:
            """Handle cancel button click."""
            self._is_cancelled = True
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
            self.status_label.setText("Cancellation requested...")
            self.cancelled.emit()
        
        def is_cancelled(self) -> bool:
            """Check if user cancelled."""
            return self._is_cancelled
        
        def finish(self, message: str = "Complete") -> None:
            """Mark as finished."""
            self.progress_bar.setValue(100)
            self.status_label.setText(message)
            self.cancel_button.setText("Close")
            self.cancel_button.setEnabled(True)
            self.cancel_button.clicked.disconnect()
            self.cancel_button.clicked.connect(self.accept)
else:
    # Stub class when PySide6 not available
    class ProgressDialog:
        """Stub progress dialog when PySide6 not available."""
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PySide6 not installed")

