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
