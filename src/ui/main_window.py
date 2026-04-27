from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from datetime import datetime

from src.camera_manager import CameraManager, PHOTOS_DIR
from src.ui.viewfinder import Viewfinder
from src.ui.controls import ControlsPanel


class MainWindow(QMainWindow):
    """Main application window. Frameless, fullscreen 800x480.

    Layout: [Viewfinder | ControlsPanel]
    """

    def __init__(self, camera_manager: CameraManager, parent=None):
        super().__init__(parent)
        self._cm = camera_manager
        self._busy = False

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

    def _setup_window(self):
        self.setWindowTitle("Camera")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(800, 480)
        self.setStyleSheet("background-color: #000;")

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left: Viewfinder
        self.viewfinder = Viewfinder(self._cm)
        layout.addWidget(self.viewfinder, 1)

        # Right: Controls
        self.controls = ControlsPanel()
        layout.addWidget(self.controls, 0, Qt.AlignRight)

    def _connect_signals(self):
        self.controls.capture_requested.connect(self._on_capture)
        if self._cm.is_real and self.viewfinder.signal_done is not None:
            self.viewfinder.done_signal.connect(self._on_capture_done)

    def _on_capture(self):
        """Handle capture button click."""
        if self._busy:
            return
        self._busy = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(PHOTOS_DIR / f"{timestamp}.jpg")
        signal_fn = self.viewfinder.signal_done
        self._cm.capture(path, signal_function=signal_fn)
        # Release busy if capture completed synchronously
        if not self._cm.is_real or signal_fn is None:
            self._busy = False

    def _on_capture_done(self, job):
        """Handle capture completion in GL mode."""
        self._cm.wait(job)
        self._busy = False
