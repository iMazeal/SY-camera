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
