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
