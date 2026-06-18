# ui/widgets.py — Componentes reutilizáveis do Legis
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from config import COLORS


def btn_primario(texto, parent=None):
    b = QPushButton(texto, parent)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLORS['accent']};
            color: white;
            font-weight: 600;
            font-size: 12px;
            padding: 8px 18px;
            border-radius: 6px;
            border: none;
        }}
        QPushButton:hover {{ background-color: {COLORS['accent_hover']}; }}
        QPushButton:pressed {{ background-color: #1E3A22; }}
        QPushButton:disabled {{ background-color: #A0B8A2; }}
    """)
    return b


def btn_secundario(texto, parent=None):
    b = QPushButton(texto, parent)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLORS['white']};
            color: {COLORS['text_primary']};
            font-weight: 600;
            font-size: 12px;
            padding: 8px 18px;
            border-radius: 6px;
            border: 1.5px solid {COLORS['border']};
        }}
        QPushButton:hover {{ background-color: {COLORS['accent_light']}; border-color: {COLORS['accent']}; color: {COLORS['accent']}; }}
    """)
    return b


def btn_perigo(texto, parent=None):
    b = QPushButton(texto, parent)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLORS['white']};
            color: {COLORS['danger']};
            font-weight: 600;
            font-size: 12px;
            padding: 8px 18px;
            border-radius: 6px;
            border: 1.5px solid {COLORS['danger']};
        }}
        QPushButton:hover {{ background-color: {COLORS['danger_light']}; }}
    """)
    return b


def campo_busca(placeholder="Buscar...", parent=None):
    f = QLineEdit(parent)
    f.setPlaceholderText(placeholder)
    f.setStyleSheet(f"""
        QLineEdit {{
            padding: 8px 12px;
            border: 1.5px solid {COLORS['border']};
            border-radius: 6px;
            background: {COLORS['white']};
            font-size: 12px;
            color: {COLORS['text_primary']};
        }}
        QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
    """)
    return f


def input_field(placeholder="", parent=None):
    f = QLineEdit(parent)
    f.setPlaceholderText(placeholder)
    f.setStyleSheet(f"""
        QLineEdit {{
            padding: 8px 10px;
            border: 1.5px solid {COLORS['border']};
            border-radius: 6px;
            background: {COLORS['white']};
            font-size: 12px;
            color: {COLORS['text_primary']};
        }}
        QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
    """)
    return f


def separador_h():
    linha = QFrame()
    linha.setFrameShape(QFrame.Shape.HLine)
    linha.setStyleSheet(f"color: {COLORS['border']}; background: {COLORS['border']}; border: none; max-height: 1px;")
    return linha


def label_titulo(texto):
    l = QLabel(texto)
    l.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
    l.setStyleSheet(f"color: {COLORS['text_primary']};")
    return l


def label_subtitulo(texto):
    l = QLabel(texto)
    l.setFont(QFont("Segoe UI", 12))
    l.setStyleSheet(f"color: {COLORS['text_secondary']};")
    return l


def estilo_tabela():
    return f"""
        QTableWidget {{
            background-color: {COLORS['white']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            gridline-color: {COLORS['border']};
            font-size: 12px;
            color: {COLORS['text_primary']};
        }}
        QTableWidget::item {{
            padding: 8px 10px;
        }}
        QTableWidget::item:selected {{
            background-color: {COLORS['accent_light']};
            color: {COLORS['accent']};
        }}
        QHeaderView::section {{
            background-color: #F0F5F0;
            padding: 9px 10px;
            border: none;
            border-bottom: 1.5px solid {COLORS['border']};
            font-weight: 700;
            font-size: 11px;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QScrollBar:vertical {{
            background: {COLORS['bg_main']};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLORS['border']};
            border-radius: 4px;
        }}
    """


def estilo_dialog():
    return f"""
        QDialog {{
            background-color: {COLORS['bg_main']};
        }}
        QLabel {{
            color: {COLORS['text_primary']};
            font-size: 12px;
        }}
    """


class CardMetrica(QWidget):
    """Card de indicador para o dashboard."""
    def __init__(self, icone, titulo, valor="0", cor_valor=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['white']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        topo = QHBoxLayout()
        lbl_icone = QLabel(icone)
        lbl_icone.setFont(QFont("Segoe UI", 20))
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Segoe UI", 11))
        lbl_titulo.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        topo.addWidget(lbl_icone)
        topo.addWidget(lbl_titulo)
        topo.addStretch()
        layout.addLayout(topo)

        self.lbl_valor = QLabel(valor)
        self.lbl_valor.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        cor = cor_valor or COLORS['text_primary']
        self.lbl_valor.setStyleSheet(f"color: {cor}; border: none;")
        layout.addWidget(self.lbl_valor)

    def atualizar(self, valor):
        self.lbl_valor.setText(str(valor))


class BadgeStatus(QLabel):
    """Badge colorido para status de processos."""
    CORES = {
        "Em andamento":           ("#EAF2EB", "#3A6B40"),
        "Prazo Fatal":            ("#FDEDEC", "#C0392B"),
        "Concluso para Sentença": ("#FEF9E7", "#D4A017"),
        "Arquivado":              ("#F1F5F9", "#5A6B5C"),
        "Suspenso":               ("#EFF6FF", "#2563EB"),
    }

    def __init__(self, status, parent=None):
        super().__init__(status, parent)
        bg, fg = self.CORES.get(status, ("#F1F5F9", "#5A6B5C"))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-size: 11px;
                font-weight: 600;
                padding: 3px 10px;
                border-radius: 10px;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
