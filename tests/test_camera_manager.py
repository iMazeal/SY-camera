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


def test_capture_with_explicit_path():
    """Capture with explicit path saves file correctly."""
    cm = CameraManager()
    with tempfile.TemporaryDirectory() as tmp:
        result = cm.capture(str(Path(tmp) / "test.jpg"))
        assert result is not None


def test_capture_respects_busy_flag():
    cm = CameraManager()
    cm._busy = True
    assert cm.capture("any.jpg") is None


def test_wait_releases_busy_flag():
    """Wait releases busy flag even with no job (mock mode)."""
    cm = CameraManager()
    cm._busy = True
    cm.wait(None)
    assert not cm._busy


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
