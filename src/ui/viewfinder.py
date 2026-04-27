from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

import numpy as np


class Viewfinder(QWidget):
    """Camera viewfinder widget with three-tier fallback:

    1. QGlPicamera2 (OpenGL hardware accelerated)
    2. Software preview via post_callback (real camera, no GL)
    3. Mock test pattern (no camera hardware)
    """

    done_signal = pyqtSignal(object)
    _frame_received = pyqtSignal(object)

    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self._cm = camera_manager
        self._gl = None
        self._picam2 = None
        self._label = None
        self._timer = None
        self._software_mode = False
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not camera_manager.is_real:
            self._init_mock(layout)
            return

        # Try QGlPicamera2 first
        if self._try_init_gl(camera_manager.picam2, layout):
            return

        # Fallback to software preview
        print("[Viewfinder] Falling back to software preview mode")
        self._init_software(camera_manager.picam2, layout)

    def _try_init_gl(self, picam2, layout) -> bool:
        """Try to initialize QGlPicamera2. Returns True on success."""
        try:
            from picamera2.previews.qt import QGlPicamera2
            self._gl = QGlPicamera2(picam2, width=640, height=480, keep_ar=True)
            layout.addWidget(self._gl)
            self._gl.done_signal.connect(self.done_signal.emit)
            return True
        except Exception as e:
            print(f"[Viewfinder] QGlPicamera2 unavailable ({e})")
            return False

    def _init_software(self, picam2, layout):
        """Software-based real camera preview using post_callback."""
        self._software_mode = True
        self._picam2 = picam2
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background-color: #111;")
        layout.addWidget(self._label)

        self._frame_received.connect(self._display_software_frame)

        try:
            picam2.post_callback = self._on_camera_frame
        except Exception as e:
            print(f"[Viewfinder] post_callback failed ({e}), falling back to timer")
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._poll_camera_frame)
            self._timer.start(66)

    def _on_camera_frame(self, request):
        """Called from camera thread when a new frame is available."""
        try:
            frame = request.make_array("main")
            self._frame_received.emit(np.copy(frame))
        except Exception:
            pass

    def _poll_camera_frame(self):
        """Fallback: poll frames via capture_array from Qt timer."""
        try:
            frame = self._picam2.capture_array("main")
            self._display_software_frame(frame)
        except Exception:
            pass

    def _display_software_frame(self, frame):
        """Display a camera frame on the QLabel (runs in Qt main thread)."""
        try:
            h, w, ch = frame.shape
            qimg = QImage(frame.data, w, h, w * ch, QImage.Format_RGB888)
            self._label.setPixmap(QPixmap.fromImage(qimg))
        except Exception:
            pass

    def _init_mock(self, layout):
        """Mock mode: QLabel updated by QTimer with test pattern."""
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background-color: #111;")
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_mock_frame)
        self._timer.start(33)

    def _update_mock_frame(self):
        frame = self._cm.get_mock_frame()
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, w * ch, QImage.Format_RGB888)
        self._label.setPixmap(QPixmap.fromImage(qimg))

    @property
    def signal_done(self):
        """Callable for picamera2's signal_function, or None if not available."""
        return self._gl.signal_done if self._gl else None

    def stop(self):
        if self._timer and self._timer.isActive():
            self._timer.stop()
        if self._picam2 and self._software_mode:
            try:
                self._picam2.post_callback = None
            except Exception:
                pass
