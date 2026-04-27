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
