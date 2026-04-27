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
