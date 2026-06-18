# ui/alertas_widget.py — Painel de alertas e notificações de prazo
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QWidget, QScrollArea, QFrame, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import date
from config import COLORS, APP_NAME
from core.database import buscar_prazos_urgentes, buscar_resumo_alertas


CORES_URGENCIA = {
    "vencido": ("#FDEDEC", "#C0392B", "⛔"),
    "hoje":    ("#FEF9E7", "#D4A017", "🔴"),
    "urgente": ("#EFF6FF", "#2563EB", "⚠️"),
    "normal":  ("#EAFAF1", "#27AE60", "✅"),
}


class CardAlerta(QFrame):
    def __init__(self, urgencia, titulo, subtitulo, detalhe="", parent=None):
        super().__init__(parent)
        bg, fg, icone = CORES_URGENCIA.get(urgencia, ("#F1F5F9", "#5A6B5C", "📌"))
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {fg}40;
                border-left: 4px solid {fg};
                border-radius: 8px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        lbl_ic = QLabel(icone)
        lbl_ic.setFont(QFont("Segoe UI", 16))
        lbl_ic.setStyleSheet("border: none; background: transparent;")
        lbl_ic.setFixedWidth(28)
        lay.addWidget(lbl_ic)

        texto_lay = QVBoxLayout()
        texto_lay.setSpacing(2)
        lbl_tit = QLabel(titulo)
        lbl_tit.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_tit.setStyleSheet(f"color: {fg}; border: none; background: transparent;")
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none; background: transparent;")
        texto_lay.addWidget(lbl_tit)
        texto_lay.addWidget(lbl_sub)
        if detalhe:
            lbl_det = QLabel(detalhe)
            lbl_det.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none; background: transparent;")
            texto_lay.addWidget(lbl_det)
        lay.addLayout(texto_lay)
        lay.addStretch()


class PainelAlertas(QDialog):
    """Dialog de alertas exibido ao abrir o sistema quando há prazos urgentes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Alertas de Prazo")
        self.setMinimumSize(620, 500)
        self.setStyleSheet(f"QDialog {{ background: {COLORS['bg_main']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho
        cab = QWidget()
        cab.setStyleSheet(f"background: {COLORS['bg_sidebar']}; border-radius: 0px;")
        cab_lay = QHBoxLayout(cab)
        cab_lay.setContentsMargins(24, 16, 24, 16)

        lbl_tit = QLabel("🔔  Alertas e Prazos")
        lbl_tit.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_tit.setStyleSheet("color: white; border: none;")
        cab_lay.addWidget(lbl_tit)
        cab_lay.addStretch()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.15); color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 6px; padding: 6px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.25); }}
        """)
        btn_fechar.clicked.connect(self.accept)
        cab_lay.addWidget(btn_fechar)
        layout.addWidget(cab)

        # Resumo de contadores
        resumo = buscar_resumo_alertas()
        resumo_widget = QWidget()
        resumo_widget.setStyleSheet(f"background: {COLORS['white']}; border-bottom: 1px solid {COLORS['border']};")
        resumo_lay = QHBoxLayout(resumo_widget)
        resumo_lay.setContentsMargins(24, 12, 24, 12)
        resumo_lay.setSpacing(24)

        for valor, label, cor in [
            (resumo["vencidos"],  "Vencidos",        COLORS["danger"]),
            (resumo["hoje"],      "Hoje",             COLORS["warning"]),
            (resumo["semana"],    "Próximos 7 dias",  COLORS["blue"]),
            (resumo["criticos"],  "Prazo Fatal",      COLORS["danger"]),
        ]:
            item = QVBoxLayout()
            lbl_v = QLabel(str(valor))
            lbl_v.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            lbl_v.setStyleSheet(f"color: {cor}; border: none;")
            lbl_l = QLabel(label)
            lbl_l.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
            item.addWidget(lbl_v)
            item.addWidget(lbl_l)
            resumo_lay.addLayout(item)
        resumo_lay.addStretch()
        layout.addWidget(resumo_widget)

        # Conteúdo em scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COLORS['bg_main']};")
        cont_lay = QVBoxLayout(conteudo)
        cont_lay.setContentsMargins(24, 16, 24, 16)
        cont_lay.setSpacing(8)

        dados = buscar_prazos_urgentes(dias_antecedencia=7)

        # Agenda urgente
        if dados["agenda_urgente"]:
            lbl_sec = QLabel("📅  Compromissos e Prazos")
            lbl_sec.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl_sec.setStyleSheet(f"color: {COLORS['text_primary']};")
            cont_lay.addWidget(lbl_sec)

            for ag in dados["agenda_urgente"]:
                urgencia = ag.get("urgencia", "normal")
                data_br = "/".join(ag["data"].split("-")[::-1]) if "-" in ag["data"] else ag["data"]
                proc = ag.get("processo_vinculado","")
                detalhe = f"Processo: {proc}" if proc else ""

                labels_urgencia = {
                    "vencido": f"VENCIDO em {data_br} às {ag['hora']}",
                    "hoje":    f"HOJE às {ag['hora']}",
                    "urgente": f"{data_br} às {ag['hora']}",
                }
                subtitulo = labels_urgencia.get(urgencia, f"{data_br} às {ag['hora']}")

                card = CardAlerta(urgencia, ag["titulo"], subtitulo, detalhe)
                cont_lay.addWidget(card)

            cont_lay.addSpacing(8)

        # Processos críticos
        if dados["processos_criticos"]:
            lbl_sec2 = QLabel("⚖️  Processos com Prazo Fatal")
            lbl_sec2.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl_sec2.setStyleSheet(f"color: {COLORS['text_primary']};")
            cont_lay.addWidget(lbl_sec2)

            for p in dados["processos_criticos"]:
                card = CardAlerta(
                    "vencido",
                    p["numero"],
                    f"Cliente: {p['cliente']}  •  {p['acao']}",
                    "Status: PRAZO FATAL"
                )
                cont_lay.addWidget(card)

        if not dados["agenda_urgente"] and not dados["processos_criticos"]:
            lbl_ok = QLabel("✅  Nenhum prazo urgente para os próximos 7 dias.")
            lbl_ok.setFont(QFont("Segoe UI", 13))
            lbl_ok.setStyleSheet(f"color: {COLORS['success']}; padding: 20px;")
            lbl_ok.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cont_lay.addWidget(lbl_ok)

        cont_lay.addStretch()
        scroll.setWidget(conteudo)
        layout.addWidget(scroll)


class BotaoAlertas(QPushButton):
    """Botão de sino para a sidebar que mostra contagem de alertas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.atualizar_contagem()

        # Atualiza a cada 5 minutos
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.atualizar_contagem)
        self._timer.start(300_000)

    def atualizar_contagem(self):
        try:
            resumo = buscar_resumo_alertas()
            self._count = resumo["total"]
        except Exception:
            self._count = 0
        self._atualizar_visual()

    def _atualizar_visual(self):
        if self._count > 0:
            self.setText(f"  🔔  Alertas  ({self._count})")
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 8px 14px;
                    background: {COLORS['danger']}22;
                    border: 1px solid {COLORS['danger']}55;
                    border-radius: 7px; font-size: 12px;
                    color: {COLORS['danger']}; font-weight: 700;
                }}
                QPushButton:hover {{ background: {COLORS['danger']}33; }}
            """)
        else:
            self.setText("  🔔  Alertas")
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 8px 14px;
                    background: rgba(255,255,255,0.08);
                    border: 1px solid rgba(255,255,255,0.15);
                    border-radius: 7px; font-size: 12px;
                    color: {COLORS['sidebar_text']};
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.15); color: white; }}
            """)
