# ui/movimentacoes_dialog.py — Janela de Últimas Movimentações detectadas
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QWidget, QFrame, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import COLORS


class MovimentacoesDialog(QDialog):
    """
    Mostra as movimentações novas detectadas na varredura automática do Datajud.
    Só deve ser instanciada quando houver pelo menos uma novidade.
    """
    def __init__(self, parent=None, novidades=None):
        super().__init__(parent)
        self.novidades = novidades or []
        self.setWindowTitle("Legis — Últimas Movimentações")
        self.setMinimumWidth(620)
        self.setMinimumHeight(480)
        self.setStyleSheet(f"QDialog {{ background: {COLORS['bg_main']}; }}")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho escuro
        header = QWidget()
        header.setStyleSheet(f"background: {COLORS['bg_sidebar']};")
        header.setFixedHeight(64)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 16, 0)
        titulo = QLabel("🔔  Últimas Movimentações")
        titulo.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white; border: none;")
        h_lay.addWidget(titulo)
        h_lay.addStretch()
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fechar.setStyleSheet(f"""
            QPushButton {{ background: rgba(255,255,255,0.15); color: white;
                border: none; border-radius: 6px; padding: 8px 18px; font-size: 12px; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.28); }}
        """)
        btn_fechar.clicked.connect(self.accept)
        h_lay.addWidget(btn_fechar)
        layout.addWidget(header)

        # Subtítulo com contagem
        qtd = len(self.novidades)
        plural = "movimentação nova detectada" if qtd == 1 else "movimentações novas detectadas"
        sub = QLabel(f"  A varredura automática no Datajud encontrou {qtd} {plural}:")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; padding: 14px 24px 6px 24px;")
        layout.addWidget(sub)

        # Área rolável com os cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        cont = QWidget()
        cont.setStyleSheet("background: transparent;")
        cont_lay = QVBoxLayout(cont)
        cont_lay.setContentsMargins(24, 6, 24, 18)
        cont_lay.setSpacing(10)

        for nov in self.novidades:
            cont_lay.addWidget(self._card(nov))
        cont_lay.addStretch()

        scroll.setWidget(cont)
        layout.addWidget(scroll)

    def _card(self, nov):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background: white; border: 1px solid {COLORS['border']};
                border-left: 4px solid {COLORS['accent']}; border-radius: 8px; }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        # Cliente + movimento
        cliente = nov.get("cliente", "—")
        lbl_cli = QLabel(f"👤  {cliente}")
        lbl_cli.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        lay.addWidget(lbl_cli)

        mov = nov.get("ultima_movimentacao", "—")
        lbl_mov = QLabel(f"🔴  {mov}")
        lbl_mov.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_mov.setStyleSheet(f"color: {COLORS['danger']}; border: none;")
        lbl_mov.setWordWrap(True)
        lay.addWidget(lbl_mov)

        # Número + data
        num = nov.get("numero_processo", "")
        num_fmt = num
        if len(num) == 20:
            num_fmt = f"{num[:7]}-{num[7:9]}.{num[9:13]}.{num[13:14]}.{num[14:16]}.{num[16:20]}"
        data_iso = nov.get("data_ultima_mov", "")
        data_fmt = data_iso
        if "T" in data_iso:
            partes = data_iso.split("T")
            data_fmt = "/".join(partes[0].split("-")[::-1]) + " " + partes[1][:5]
        rodape = QLabel(f"Processo: {num_fmt}   •   {data_fmt}   •   {nov.get('tribunal','').upper()}")
        rodape.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        lay.addWidget(rodape)

        return card
