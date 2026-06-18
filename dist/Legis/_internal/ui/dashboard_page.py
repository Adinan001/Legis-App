# ui/dashboard_page.py — com contagem regressiva e alertas
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QAbstractItemView,
                             QHeaderView, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import date, timedelta
from config import COLORS
from ui.widgets import (CardMetrica, label_titulo, label_subtitulo,
                        estilo_tabela, separador_h)
from core.database import (obter_resumo_dashboard, buscar_configuracoes,
                           buscar_resumo_alertas, buscar_prazos_urgentes)


def _fmt_brl(valor):
    return f"R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _dias_restantes(data_iso):
    try:
        alvo = date.fromisoformat(data_iso)
        delta = (alvo - date.today()).days
        return delta
    except Exception:
        return None


class CardPrazo(QFrame):
    """Card compacto para exibir prazo com contagem regressiva."""
    def __init__(self, titulo, data_iso, tipo, processo="", parent=None):
        super().__init__(parent)
        dias = _dias_restantes(data_iso)
        data_br = "/".join(data_iso.split("-")[::-1]) if "-" in data_iso else data_iso

        if dias is None:
            bg, fg, badge = COLORS["white"], COLORS["text_muted"], "—"
        elif dias < 0:
            bg, fg = "#FDEDEC", COLORS["danger"]
            badge = f"⛔ VENCIDO há {abs(dias)}d"
        elif dias == 0:
            bg, fg = "#FEF9E7", COLORS["warning"]
            badge = "🔴 HOJE"
        elif dias <= 3:
            bg, fg = "#FEF9E7", COLORS["warning"]
            badge = f"⚠️ {dias}d"
        elif dias <= 7:
            bg, fg = "#EFF6FF", COLORS["blue"]
            badge = f"📅 {dias}d"
        else:
            bg, fg = COLORS["success_light"], COLORS["success"]
            badge = f"✅ {dias}d"

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {fg}40;
                border-left: 4px solid {fg};
                border-radius: 8px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        # Badge de dias
        lbl_badge = QLabel(badge)
        lbl_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_badge.setStyleSheet(f"color: {fg}; border: none; background: transparent; min-width: 80px;")
        lay.addWidget(lbl_badge)

        # Título e info
        info_lay = QVBoxLayout()
        info_lay.setSpacing(1)
        lbl_tit = QLabel(titulo)
        lbl_tit.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl_tit.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; background: transparent;")
        info_lay.addWidget(lbl_tit)
        sub_txt = f"{tipo}  •  {data_br}"
        if processo: sub_txt += f"  •  Proc: {processo[:30]}"
        lbl_sub = QLabel(sub_txt)
        lbl_sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; border: none; background: transparent;")
        info_lay.addWidget(lbl_sub)
        lay.addLayout(info_lay)
        lay.addStretch()


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        # Atualiza relógio a cada minuto
        self._timer_clock = QTimer(self)
        self._timer_clock.timeout.connect(self._atualizar_relogio)
        self._timer_clock.start(60_000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(12)

        # Cabeçalho com data/hora
        cab = QHBoxLayout()
        col_esq = QVBoxLayout()
        col_esq.setSpacing(2)
        self.lbl_escritorio = label_subtitulo("—")
        col_esq.addWidget(label_titulo("Visão Geral"))
        col_esq.addWidget(self.lbl_escritorio)
        cab.addLayout(col_esq)
        cab.addStretch()

        # Data e hora no canto direito
        col_dir = QVBoxLayout()
        col_dir.setSpacing(2)
        col_dir.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_data = QLabel("")
        self.lbl_data.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_data.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.lbl_data.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_hora = QLabel("")
        self.lbl_hora.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        self.lbl_hora.setAlignment(Qt.AlignmentFlag.AlignRight)
        col_dir.addWidget(self.lbl_data)
        col_dir.addWidget(self.lbl_hora)
        cab.addLayout(col_dir)
        layout.addLayout(cab)
        layout.addWidget(separador_h())

        # Cards de métricas
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self.card_proc    = CardMetrica("⚖️",  "Processos Ativos",     "0")
        self.card_cli     = CardMetrica("👥", "Clientes",              "0")
        self.card_vencido = CardMetrica("⛔", "Prazos Vencidos",       "0", COLORS["danger"])
        self.card_hoje    = CardMetrica("🔴", "Compromissos Hoje",     "0", COLORS["warning"])
        self.card_semana  = CardMetrica("📅", "Próximos 7 dias",       "0", COLORS["blue"])
        for c in [self.card_proc, self.card_cli, self.card_vencido, self.card_hoje, self.card_semana]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # Segunda linha — prazos urgentes + alertas críticos
        segunda = QHBoxLayout()
        segunda.setSpacing(14)

        # Prazos urgentes com contagem regressiva
        col_prazos = QVBoxLayout()
        col_prazos.setSpacing(6)
        lbl_prazos = QLabel("⏱️  Prazos em Andamento")
        lbl_prazos.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_prazos.setStyleSheet(f"color: {COLORS['text_primary']};")
        col_prazos.addWidget(lbl_prazos)

        self.frame_prazos = QWidget()
        self.frame_prazos.setStyleSheet(f"background: transparent;")
        self.lay_prazos = QVBoxLayout(self.frame_prazos)
        self.lay_prazos.setContentsMargins(0, 0, 0, 0)
        self.lay_prazos.setSpacing(6)
        col_prazos.addWidget(self.frame_prazos)
        col_prazos.addStretch()

        # Alertas críticos de processos
        col_alertas = QVBoxLayout()
        col_alertas.setSpacing(6)
        lbl_alertas = QLabel("🚨  Processos com Prazo Fatal")
        lbl_alertas.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_alertas.setStyleSheet(f"color: {COLORS['text_primary']};")
        col_alertas.addWidget(lbl_alertas)
        self.table_alertas = QTableWidget()
        self.table_alertas.setColumnCount(3)
        self.table_alertas.setHorizontalHeaderLabels(["Nº Processo", "Cliente", "Status"])
        self.table_alertas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_alertas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_alertas.setStyleSheet(estilo_tabela())
        self.table_alertas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_alertas.verticalHeader().setVisible(False)
        col_alertas.addWidget(self.table_alertas)

        segunda.addLayout(col_prazos, 50)
        segunda.addLayout(col_alertas, 50)
        layout.addLayout(segunda)

        self._atualizar_relogio()
        self.atualizar_dados()

    def _atualizar_relogio(self):
        from datetime import datetime
        agora = datetime.now()
        dias_semana = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        meses_pt = ["janeiro","fevereiro","março","abril","maio","junho",
                    "julho","agosto","setembro","outubro","novembro","dezembro"]
        self.lbl_data.setText(
            f"{dias_semana[agora.weekday()]}, {agora.day} de {meses_pt[agora.month-1]} de {agora.year}")
        self.lbl_hora.setText(agora.strftime("%H:%M"))

    def atualizar_dados(self):
        cfg = buscar_configuracoes()
        self.lbl_escritorio.setText(cfg.get("nome_escritorio", "Legis Beta"))

        r = obter_resumo_dashboard()
        self.card_proc.atualizar(str(r["total_processos"]))
        self.card_cli.atualizar(str(r["total_clientes"]))

        # Alertas de prazo
        resumo_alertas = buscar_resumo_alertas()
        self.card_vencido.atualizar(str(resumo_alertas["vencidos"]))
        self.card_hoje.atualizar(str(resumo_alertas["hoje"]))
        self.card_semana.atualizar(str(resumo_alertas["semana"]))

        # Atualizar cor do card vencidos
        cor_venc = COLORS["danger"] if resumo_alertas["vencidos"] > 0 else COLORS["success"]
        self.card_vencido.lbl_valor.setStyleSheet(f"color: {cor_venc}; border: none;")

        # Prazos com contagem regressiva
        while self.lay_prazos.count():
            item = self.lay_prazos.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dados = buscar_prazos_urgentes(dias_antecedencia=14)
        agenda = dados["agenda_urgente"][:6]  # máximo 6 cards

        if agenda:
            for ag in agenda:
                card = CardPrazo(
                    titulo=ag["titulo"],
                    data_iso=ag["data"],
                    tipo=ag["tipo"],
                    processo=ag.get("processo_vinculado","")
                )
                self.lay_prazos.addWidget(card)
        else:
            lbl_ok = QLabel("✅  Nenhum prazo urgente nos próximos 14 dias.")
            lbl_ok.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
            self.lay_prazos.addWidget(lbl_ok)

        # Alertas críticos (processos prazo fatal)
        criticos = r["alertas_criticos"]
        self.table_alertas.setRowCount(len(criticos))
        for i, p in enumerate(criticos):
            self.table_alertas.setItem(i, 0, QTableWidgetItem(p["numero"]))
            self.table_alertas.setItem(i, 1, QTableWidgetItem(p["cliente"]))
            item = QTableWidgetItem("🚨 PRAZO FATAL")
            item.setForeground(QColor(COLORS["danger"]))
            item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table_alertas.setItem(i, 2, item)
