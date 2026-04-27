from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
import numpy as np


class Viewfinder(QWidget):
    """Camera viewfinder widget. Uses QGlPicamera2 in real mode, QLabel in mock mode.

    Signals:
        done_signal: Emitted with the capture job when photo capture completes (real mode only).
    """

    done_signal = pyqtSignal(object)

    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self._cm = camera_manager
        self._gl = None
        self._label = None
        self._timer = None
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if camera_manager.is_real:
            self._init_real(camera_manager.picam2, layout)
        else:
            self._init_mock(layout)

    def _init_real(self, picam2, layout):
        """Real mode: embed QGlPicamera2. Falls back to mock if GL fails."""
        try:
            from picamera2.previews.qt import QGlPicamera2
            self._gl = QGlPicamera2(picam2, width=640, height=480, keep_ar=True)
        except Exception as e:
            print(f"[Viewfinder] QGlPicamera2 unavailable ({e}), using mock fallback")
            self._init_mock(layout)
            return
        layout.addWidget(self._gl)
        # Forward the done_signal from QGlPicamera2
        self._gl.done_signal.connect(self.done_signal.emit)

    def _init_mock(self, layout):
        """Mock mode: QLabel updated by QTimer."""
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background-color: #111;")
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_mock_frame)
        self._timer.start(33)  # ~30fps

    def _update_mock_frame(self):
        """Update mock preview frame."""
        frame = self._cm.get_mock_frame()
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, w * ch, QImage.Format_RGB888)
        self._label.setPixmap(QPixmap.fromImage(qimg))

    @property
    def signal_done(self):
        """Callable to pass as signal_function to switch_mode_and_capture_file.
        Returns None in mock mode."""
        return self._gl.signal_done if self._gl else None

    def stop(self):
        """Stop mock timer if running."""
        if self._timer and self._timer.isActive():
            self._timer.stop()
