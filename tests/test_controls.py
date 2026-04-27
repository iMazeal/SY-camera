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
