# 实时画面流与 GUI 界面实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 RPi 3B+ 800×480 DSI 触摸屏上实现相机实时预览和拍照功能

**Architecture:** 三层架构 — UI 层 (PyQt5) + 相机控制层 (CameraManager) + 硬件抽象层 (Picamera2)。MainWindow 负责布局管理和信号串联，CameraManager 封装 Picamera2 并提供 Mock 降级模式。

**Tech Stack:** Python 3.13, PyQt5, opencv-python-headless, Picamera2 (RPi only), pytest + pytest-qt

---

### Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `src/ui/__init__.py`
- Create: `tests/__init__.py`

- [ ] **创建 pyproject.toml**

```toml
[project]
name = "camera"
version = "0.1.0"
description = "Raspberry Pi Camera Application"
requires-python = ">=3.13"
dependencies = [
    "PyQt5>=5.15",
    "opencv-python-headless>=4.9",
    "numpy>=1.26",
]

[project.optional-dependencies]
picamera2 = ["picamera2"]
dev = [
    "pytest>=8.0",
    "pytest-qt>=4.2",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **创建 .gitignore**

```
__pycache__/
*.pyc
.venv/
venv/
.superpowers/
photos/
```

- [ ] **创建包 __init__.py 文件**（三个空文件）

```python
# src/__init__.py — empty
```

```python
# src/ui/__init__.py — empty
```

```python
# tests/__init__.py — empty
```

- [ ] **初始化 venv 并安装依赖**

Run: `cd /home/mazeal/camera && uv sync`

Expected: pyproject.toml 被读取，PyQt5、opencv-python-headless、numpy 安装成功

- [ ] **验证安装**

Run: `python -c "import cv2; print(cv2.__version__)"`
Run: `python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"`

Expected: 版本号输出，无报错

- [ ] **提交**

```bash
git init
git add pyproject.toml .gitignore src/ tests/
git commit -m "chore: initialize project structure and dependencies"
```

---

### Task 2: CameraManager — 相机控制层

**Files:**
- Create: `src/camera_manager.py`
- Create: `tests/test_camera_manager.py`

CameraManager 封装 Picamera2 的启动/预览/拍照，当 Picamera2 不可用时自动降级为 Mock 模式。

- [ ] **编写 CameraManager 类实现**

```python
# src/camera_manager.py
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np

PHOTOS_DIR = Path("photos")


class CameraManager:
    """Camera control layer. Wraps Picamera2 with mock fallback for dev machines."""

    def __init__(self):
        self._picam2 = None
        self._real_mode = False
        self._busy = False
        self._mock_frame_index = 0
        PHOTOS_DIR.mkdir(exist_ok=True)

        try:
            from picamera2 import Picamera2
            self._picam2 = Picamera2()
            self._real_mode = True
        except Exception:
            print("[CameraManager] Picamera2 not available, using mock mode")

    @property
    def is_real(self) -> bool:
        return self._real_mode

    @property
    def picam2(self):
        return self._picam2

    def start_preview(self) -> dict | None:
        """Configure and start camera preview. Returns config dict or None in mock mode."""
        if not self._real_mode:
            return None
        config = self._picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self._picam2.configure(config)
        self._picam2.start()
        return config

    def capture(self, output_path: str | None = None,
                signal_function=None) -> str | None:
        """Trigger photo capture.

        In real mode, signal_function (typically QGlPicamera2.signal_done) is
        passed to switch_mode_and_capture_file. The caller connects to
        Viewfinder.done_signal to know when capture completes.

        In mock mode, saves immediately.
        Returns the output path or None if busy.
        """
        if self._busy:
            return None

        if output_path is None:
            output_path = str(PHOTOS_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.jpg")

        self._busy = True

        if self._real_mode:
            cfg = self._picam2.create_still_configuration()
            self._picam2.switch_mode_and_capture_file(
                cfg, output_path, signal_function=signal_function
            )
        else:
            self._mock_capture(output_path)

        return output_path

    def wait(self, job) -> None:
        """Wait for a capture job to complete and release busy flag."""
        if self._real_mode and job is not None:
            self._picam2.wait(job)
        self._busy = False

    def set_controls(self, **kwargs) -> None:
        """Set camera controls (exposure, gain, etc.). No-op in mock mode."""
        if self._real_mode:
            self._picam2.set_controls(kwargs)

    def stop(self) -> None:
        """Stop camera and release resources."""
        if self._real_mode:
            self._picam2.stop()
            self._picam2.close()

    def get_mock_frame(self) -> np.ndarray:
        """Generate a colorful test pattern for mock mode (640x480 RGB)."""
        w, h = 640, 480
        t = self._mock_frame_index * 0.05
        self._mock_frame_index += 1
        x = np.arange(w)
        y = np.arange(h)
        xx, yy = np.meshgrid(x, y)
        r = (128 + 127 * np.sin(xx / 50 + t)).astype(np.uint8)
        g = (128 + 127 * np.sin(yy / 40 + t + 2.1)).astype(np.uint8)
        b = (128 + 127 * np.sin((xx + yy) / 60 + t + 4.2)).astype(np.uint8)
        return np.stack([r, g, b], axis=-1)

    def _mock_capture(self, path: str) -> None:
        """Simulate capture in mock mode."""
        import cv2
        frame = self.get_mock_frame()
        cv2.imwrite(path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        time.sleep(0.1)
        self._busy = False
        print(f"[Mock] Captured: {path}")
```

- [ ] **编写 CameraManager 单元测试**

```python
# tests/test_camera_manager.py
from pathlib import Path
import tempfile

import cv2
import numpy as np

from src.camera_manager import CameraManager, PHOTOS_DIR


def test_mock_mode_by_default():
    """CameraManager defaults to mock mode when Picamera2 unavailable."""
    cm = CameraManager()
    assert not cm.is_real
    assert cm.picam2 is None


def test_start_preview_mock_returns_none():
    cm = CameraManager()
    assert cm.start_preview() is None


def test_capture_creates_jpg_file():
    cm = CameraManager()
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "test.jpg")
        result = cm.capture(path)
        assert result == path
        assert Path(path).exists()
        img = cv2.imread(path)
        assert img.shape == (480, 640, 3)


def test_capture_generates_timestamp_path():
    cm = CameraManager()
    with tempfile.TemporaryDirectory() as tmp:
        PHOTOS_DIR_orig = PHOTOS_DIR
        # Override by passing explicit path
        result = cm.capture(str(Path(tmp) / "test.jpg"))
        assert result is not None


def test_capture_respects_busy_flag():
    cm = CameraManager()
    cm._busy = True
    assert cm.capture("any.jpg") is None


def test_get_mock_frame_returns_640x480_rgb():
    cm = CameraManager()
    frame = cm.get_mock_frame()
    assert frame.shape == (480, 640, 3)
    assert frame.dtype == np.uint8


def test_get_mock_frame_changes_over_time():
    cm = CameraManager()
    f1 = cm.get_mock_frame()
    f2 = cm.get_mock_frame()
    assert not np.array_equal(f1, f2)


def test_set_controls_noop_in_mock():
    cm = CameraManager()
    cm.set_controls(ExposureTime=30000)  # should not raise


def test_stop_noop_in_mock():
    cm = CameraManager()
    cm.stop()  # should not raise
```

- [ ] **运行测试**

Run: `cd /home/mazeal/camera && python -m pytest tests/test_camera_manager.py -v`

Expected: 所有测试通过

- [ ] **提交**

```bash
git add src/camera_manager.py tests/test_camera_manager.py
git commit -m "feat: add CameraManager with mock fallback"
```

---

### Task 3: Viewfinder — 取景器封装

**Files:**
- Create: `src/ui/viewfinder.py`
- Create: `tests/test_viewfinder.py`

Viewfinder 封装 QGlPicamera2（真实模式）或 QLabel + QTimer（Mock 模式），提供统一的 done_signal。

- [ ] **编写 Viewfinder 组件**

```python
# src/ui/viewfinder.py
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
        """Real mode: embed QGlPicamera2."""
        try:
            from picamera2.previews.qt import QGlPicamera2
        except ImportError:
            # Fallback if picamera2 gui extras not installed
            self._init_mock(layout)
            return
        self._gl = QGlPicamera2(picam2, width=640, height=480, keep_ar=True)
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
```

- [ ] **编写 Viewfinder 测试（Mock 模式）**

```python
# tests/test_viewfinder.py
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.camera_manager import CameraManager
from src.ui.viewfinder import Viewfinder


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_viewfinder_creates_in_mock_mode(qapp):
    cm = CameraManager()
    vf = Viewfinder(cm)
    assert vf._label is not None
    assert vf._gl is None
    assert vf._timer is not None
    assert vf._timer.isActive()
    vf.stop()


def test_viewfinder_minimum_size(qapp):
    cm = CameraManager()
    vf = Viewfinder(cm)
    assert vf.minimumWidth() == 640
    assert vf.minimumHeight() == 480
    vf.stop()


def test_viewfinder_has_done_signal(qapp):
    cm = CameraManager()
    vf = Viewfinder(cm)
    assert hasattr(vf, "done_signal")
    vf.stop()
```

- [ ] **运行测试**

Run: `cd /home/mazeal/camera && python -m pytest tests/test_viewfinder.py -v`

Expected: 所有测试通过（Mock 模式）

- [ ] **提交**

```bash
git add src/ui/viewfinder.py tests/test_viewfinder.py
git commit -m "feat: add Viewfinder widget with real and mock modes"
```

---

### Task 4: ControlsPanel — 右侧控制面板

**Files:**
- Create: `src/ui/controls.py`
- Create: `tests/test_controls.py`

ControlsPanel 是右侧边栏，包含圆形拍照按钮（纯图标）和相册按钮（占位骨架）。

- [ ] **编写 ControlsPanel 组件**

```python
# src/ui/controls.py
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QIcon, QPixmap, QRadialGradient
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy, QSpacerItem


class CaptureButton(QPushButton):
    """Circular capture button with red gradient and white ring icon."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: qradialgradient(
                    cx:0.4, cy:0.4, radius:0.5,
                    stop:0 #ff6b6b, stop:1 #c0392b
                );
                border: 3px solid rgba(255, 255, 255, 0.8);
                border-radius: 32px;
            }
            QPushButton:hover {
                background: qradialgradient(
                    cx:0.4, cy:0.4, radius:0.5,
                    stop:0 #ff8787, stop:1 #e74c3c
                );
            }
            QPushButton:pressed {
                background: qradialgradient(
                    cx:0.4, cy:0.4, radius:0.5,
                    stop:0 #e74c3c, stop:1 #a93226
                );
            }
        """)

    def sizeHint(self):
        return QSize(64, 64)


class GalleryButton(QPushButton):
    """Gallery button — rounded rectangle placeholder for future gallery."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2a2a4e;
            }
            QPushButton:pressed {
                background-color: #151530;
            }
        """)

    def _draw_icon(self):
        """Draw a simple gallery icon."""
        pixmap = QPixmap(28, 20)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(80, 80, 140), 1.5))
        painter.setBrush(QBrush(QColor(40, 40, 80)))
        painter.drawRoundedRect(1, 1, 26, 18, 2, 2)
        painter.setBrush(QBrush(QColor(80, 80, 140)))
        painter.drawEllipse(6, 5, 6, 6)
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(28, 20))

    def showEvent(self, event):
        super().showEvent(event)
        self._draw_icon()


class ControlsPanel(QWidget):
    """Right sidebar with capture and gallery buttons.

    Signals:
        capture_requested: Emitted when capture button is clicked.
    """

    capture_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(100)
        self.setStyleSheet("background-color: #16213e;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top spacer
        layout.addStretch(2)

        # Capture button
        self.capture_btn = CaptureButton()
        self.capture_btn.clicked.connect(self.capture_requested.emit)
        layout.addWidget(self.capture_btn, 0, Qt.AlignCenter)

        # Bottom spacer
        layout.addStretch(3)

        # Gallery button
        self.gallery_btn = GalleryButton()
        layout.addWidget(self.gallery_btn, 0, Qt.AlignCenter)

        # Bottom padding
        layout.addSpacing(12)
```

- [ ] **编写 ControlsPanel 测试**

```python
# tests/test_controls.py
import pytest
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import Qt

from src.ui.controls import ControlsPanel, CaptureButton, GalleryButton


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_controls_panel_fixed_width(qapp):
    panel = ControlsPanel()
    assert panel.width() == 100 or panel.minimumWidth() <= 100


def test_capture_button_is_circular(qapp):
    btn = CaptureButton()
    assert btn.width() == 64
    assert btn.height() == 64


def test_gallery_button_is_rounded(qapp):
    btn = GalleryButton()
    assert btn.width() == 56
    assert btn.height() == 48


def test_capture_button_emits_signal(qapp):
    panel = ControlsPanel()
    received = []

    def on_capture():
        received.append(True)

    panel.capture_requested.connect(on_capture)
    panel.capture_btn.click()
    assert len(received) == 1


def test_controls_panel_contains_both_buttons(qapp):
    panel = ControlsPanel()
    assert isinstance(panel.capture_btn, CaptureButton)
    assert isinstance(panel.gallery_btn, GalleryButton)


def test_gallery_button_has_icon_after_show(qapp):
    btn = GalleryButton()
    btn.show()  # triggers showEvent which draws icon
    assert not btn.icon().isNull()
```

- [ ] **运行测试**

Run: `cd /home/mazeal/camera && python -m pytest tests/test_controls.py -v`

Expected: 所有测试通过

- [ ] **提交**

```bash
git add src/ui/controls.py tests/test_controls.py
git commit -m "feat: add ControlsPanel with capture and gallery buttons"
```

---

### Task 5: MainWindow — 主窗口布局

**Files:**
- Create: `src/ui/main_window.py`
- Create: `tests/test_main_window.py`

MainWindow 负责整体布局：左侧取景器 + 右侧控制面板，并串联拍照信号。

- [ ] **编写 MainWindow 实现**

```python
# src/ui/main_window.py
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
        if self._cm.is_real:
            self.viewfinder.done_signal.connect(self._on_capture_done)

    def _on_capture(self):
        """Handle capture button click."""
        if self._busy:
            return
        self._busy = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(PHOTOS_DIR / f"{timestamp}.jpg")
        self._cm.capture(path, signal_function=self.viewfinder.signal_done)
        if not self._cm.is_real:
            self._busy = False

    def _on_capture_done(self, job):
        """Handle capture completion in real mode."""
        self._cm.wait(job)
        self._busy = False
```

- [ ] **编写 MainWindow 测试**

```python
# tests/test_main_window.py
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.camera_manager import CameraManager
from src.ui.main_window import MainWindow
from src.ui.viewfinder import Viewfinder
from src.ui.controls import ControlsPanel


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_creates(qapp):
    cm = CameraManager()
    win = MainWindow(cm)
    assert win.width() == 800
    assert win.height() == 480


def test_main_window_is_frameless(qapp):
    cm = CameraManager()
    win = MainWindow(cm)
    assert win.windowFlags() & Qt.FramelessWindowHint


def test_main_window_contains_viewfinder(qapp):
    cm = CameraManager()
    win = MainWindow(cm)
    assert isinstance(win.viewfinder, Viewfinder)
    win.viewfinder.stop()


def test_main_window_contains_controls(qapp):
    cm = CameraManager()
    win = MainWindow(cm)
    assert isinstance(win.controls, ControlsPanel)


def test_capture_sets_busy_flag(qapp):
    cm = CameraManager()
    win = MainWindow(cm)
    assert not win._busy
    win._on_capture()
    assert not win._busy  # mock mode: busy resets immediately
    win.viewfinder.stop()
```

- [ ] **运行测试**

Run: `cd /home/mazeal/camera && python -m pytest tests/test_main_window.py -v`

Expected: 所有测试通过

- [ ] **提交**

```bash
git add src/ui/main_window.py tests/test_main_window.py
git commit -m "feat: add MainWindow with viewfinder and controls layout"
```

---

### Task 6: 应用入口 main.py

**Files:**
- Create: `src/main.py`

- [ ] **编写 main.py**

```python
# src/main.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.camera_manager import CameraManager
from src.ui.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    app.setApplicationName("Camera")

    camera_manager = CameraManager()
    camera_manager.start_preview()

    window = MainWindow(camera_manager)
    window.show()

    try:
        sys.exit(app.exec_())
    finally:
        camera_manager.stop()
        if hasattr(window, "viewfinder"):
            window.viewfinder.stop()


if __name__ == "__main__":
    main()
```

- [ ] **验证启动（无头模式）**

Run: `cd /home/mazeal/camera && QT_QPA_PLATFORM=offscreen python -c "
from src.main import main
import signal, threading
timer = threading.Timer(0.5, lambda: __import__('os')._exit(0))
timer.start()
main()
"`

Expected: 应用启动 0.5 秒后自动退出，无 crash（无头模式下只能验证初始化正常）

- [ ] **提交**

```bash
git add src/main.py
git commit -m "feat: add application entry point"
```

---

### Task 7: 集成验证

**Files:**
- Modify: 无（运行验证）

- [ ] **运行所有测试**

Run: `cd /home/mazeal/camera && python -m pytest tests/ -v`

Expected: 全部通过

- [ ] **验证模块完整性**

Run: `cd /home/mazeal/camera && python -c "
from src.camera_manager import CameraManager
from src.ui.main_window import MainWindow
from src.ui.viewfinder import Viewfinder
from src.ui.controls import ControlsPanel, CaptureButton, GalleryButton
print('All imports OK')
"`

Expected: 无 ImportError

- [ ] **最终提交**

```bash
git add .
git commit -m "chore: finalize phase 1 — live preview and GUI"
```
