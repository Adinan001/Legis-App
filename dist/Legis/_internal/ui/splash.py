# ui/splash.py — Tela de abertura
import os
from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from config import APP_VERSION

SPLASH_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "splash.png")

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Carrega imagem
        if os.path.exists(SPLASH_IMG):
            pixmap = QPixmap(SPLASH_IMG).scaled(820, 520,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
        else:
            # Fallback se imagem não existir
            pixmap = QPixmap(820, 520)
            pixmap.fill(QColor("#0F1A10"))
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor("#4A8B52")))
            painter.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "LEGIS")
            painter.end()

        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # Overlay com versão
        self.showMessage(
            f"  Legis v{APP_VERSION} — Carregando...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
            QColor("#B8CCB9")
        )
