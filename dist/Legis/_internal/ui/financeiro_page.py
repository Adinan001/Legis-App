# ui/financeiro_page.py — Com filtro mensal/anual e gráfico de barras
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QDialog, QFormLayout,
                             QComboBox, QMessageBox, QDialogButtonBox,
                             QPushButton, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient
import config
from config import COLORS, MESES
from ui.widgets import (btn_primario, btn_perigo, btn_secundario, campo_busca,
                        input_field, label_titulo, estilo_tabela, separador_h,
                        estilo_dialog, CardMetrica)
from core.database import (buscar_lancamentos, buscar_lancamentos_mes,
                           buscar_resumo_mensal, buscar_anos_disponiveis,
                           salvar_lancamento, excluir_lancamento)
from datetime import date


def _fmt_brl(v):
    return f"R$ {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class GraficoBarras(QWidget):
    """Gráfico de barras simples receita x despesa."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)
        self.dados = []  # lista de dicts com receita, despesa, label

    def atualizar(self, dados):
        self.dados = dados
        self.update()

    def paintEvent(self, event):
        if not self.dados:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad_left = 60
        pad_right = 16
        pad_top = 16
        pad_bottom = 36
        area_w = w - pad_left - pad_right
        area_h = h - pad_top - pad_bottom

        # fundo
        p.fillRect(0, 0, w, h, QColor(COLORS["card_bg"]))

        # máximo para escala
        max_val = max((max(d["receita"], d["despesa"]) for d in self.dados), default=1)
        if max_val == 0:
            max_val = 1

        n = len(self.dados)
        group_w = area_w / n
        bar_w = max(6, group_w * 0.28)
        gap = bar_w * 0.3

        # linhas de grade
        p.setPen(QPen(QColor(COLORS["border"]), 1, Qt.PenStyle.DashLine))
        for frac in [0.25, 0.5, 0.75, 1.0]:
            y = pad_top + area_h - int(area_h * frac)
            p.drawLine(pad_left, y, w - pad_right, y)

        # barras
        for i, d in enumerate(self.dados):
            cx = pad_left + i * group_w + group_w / 2

            # Receita (verde)
            h_rec = int(area_h * d["receita"] / max_val)
            x_rec = int(cx - bar_w - gap / 2)
            y_rec = pad_top + area_h - h_rec
            p.setBrush(QBrush(QColor(COLORS["success"])))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x_rec, y_rec, int(bar_w), h_rec, 3, 3)

            # Despesa (vermelho)
            h_des = int(area_h * d["despesa"] / max_val)
            x_des = int(cx + gap / 2)
            y_des = pad_top + area_h - h_des
            p.setBrush(QBrush(QColor(COLORS["danger"])))
            p.drawRoundedRect(x_des, y_des, int(bar_w), h_des, 3, 3)

            # Label
            p.setPen(QPen(QColor(COLORS["text_muted"])))
            p.setFont(QFont("Segoe UI", 8))
            lbl = d.get("label", "")
            p.drawText(int(cx - 18), h - 6, lbl)

        # Legenda
        p.setBrush(QBrush(QColor(COLORS["success"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(pad_left, 2, 12, 10, 2, 2)
        p.setPen(QPen(QColor(COLORS["text_secondary"])))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(pad_left + 16, 11, "Receita")
        p.setBrush(QBrush(QColor(COLORS["danger"])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(pad_left + 75, 2, 12, 10, 2, 2)
        p.setPen(QPen(QColor(COLORS["text_secondary"])))
        p.drawText(pad_left + 91, 11, "Despesa")
        p.end()


class LancamentoDialog(QDialog):
    def __init__(self, parent=None, ano=None, mes=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Lançamento")
        self.setMinimumWidth(400)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        titulo = QLabel("Registrar Lançamento")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(titulo)
        layout.addWidget(separador_h())
        form = QFormLayout()
        form.setSpacing(10)
        data_default = f"{ano}-{mes:02d}-{date.today().day:02d}" if ano and mes else date.today().isoformat()
        self.txt_data = input_field(f"AAAA-MM-DD")
        self.txt_data.setText(data_default)
        self.txt_descricao = input_field("Descrição do lançamento")
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Receita", "Despesa"])
        self.cb_tipo.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.txt_valor = input_field("0,00")
        form.addRow(QLabel("<b>Data:</b>"), self.txt_data)
        form.addRow(QLabel("<b>Descrição:</b>"), self.txt_descricao)
        form.addRow(QLabel("<b>Tipo:</b>"), self.cb_tipo)
        form.addRow(QLabel("<b>Valor (R$):</b>"), self.txt_valor)
        layout.addLayout(form)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(
            f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_descricao.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe a descrição.")
            return
        try:
            float(self.txt_valor.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", "Informe um valor numérico válido.")
            return
        self.accept()

    def obter_dados(self):
        return {
            "data": self.txt_data.text().strip(),
            "descricao": self.txt_descricao.text().strip(),
            "tipo": self.cb_tipo.currentText(),
            "valor": float(self.txt_valor.text().replace(",", ".")),
        }


class FinanceiroPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mes_atual = None   # None = visão anual
        self._ano_atual = date.today().year
        self._dados = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── BARRA DE MESES (topo fixo) ──────────────────────────
        barra_meses = QWidget()
        barra_meses.setStyleSheet(f"background-color: {COLORS['white']}; border-bottom: 1px solid {COLORS['border']};")
        barra_meses.setFixedHeight(52)
        bm_layout = QHBoxLayout(barra_meses)
        bm_layout.setContentsMargins(20, 6, 20, 6)
        bm_layout.setSpacing(4)

        # Seletor de ano
        self.cb_ano = QComboBox()
        self.cb_ano.setFixedWidth(90)
        self.cb_ano.setStyleSheet(f"padding: 5px 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px; font-weight: 600;")
        self._preencher_anos()
        self.cb_ano.currentTextChanged.connect(self._trocar_ano)
        bm_layout.addWidget(self.cb_ano)
        bm_layout.addSpacing(8)

        # Botões dos meses
        self._btns_mes = []
        _meses_abrev = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        for i, abrev in enumerate(_meses_abrev):
            btn = QPushButton(abrev)
            btn.setFixedSize(46, 32)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, m=i+1: self._selecionar_mes(m))
            self._btns_mes.append(btn)
            bm_layout.addWidget(btn)

        bm_layout.addSpacing(4)
        # Botão Anual
        self.btn_anual = QPushButton("Anual")
        self.btn_anual.setFixedSize(58, 32)
        self.btn_anual.setCheckable(True)
        self.btn_anual.setChecked(True)
        self.btn_anual.clicked.connect(lambda: self._selecionar_mes(None))
        bm_layout.addWidget(self.btn_anual)
        bm_layout.addStretch()

        self._aplicar_estilo_btns_mes()
        layout.addWidget(barra_meses)

        # ── CONTEÚDO PRINCIPAL ──────────────────────────────────
        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COLORS['bg_main']};")
        c_layout = QVBoxLayout(conteudo)
        c_layout.setContentsMargins(32, 20, 32, 20)
        c_layout.setSpacing(14)

        # Cabeçalho
        cab = QHBoxLayout()
        self.lbl_titulo_periodo = label_titulo("Visão Anual")
        cab.addWidget(self.lbl_titulo_periodo)
        cab.addStretch()
        self.btn_novo = btn_primario("＋  Novo Lançamento")
        self.btn_novo.clicked.connect(self.abrir_novo)
        cab.addWidget(self.btn_novo)
        c_layout.addLayout(cab)
        c_layout.addWidget(separador_h())

        # Cards de totais
        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.card_rec = CardMetrica("📈", "Total Recebido",  "R$ 0,00", COLORS["success"])
        self.card_des = CardMetrica("📉", "Total Despesas",  "R$ 0,00", COLORS["danger"])
        self.card_sal = CardMetrica("💰", "Saldo Líquido",   "R$ 0,00", COLORS["blue"])
        for c in [self.card_rec, self.card_des, self.card_sal]:
            cards.addWidget(c)
        c_layout.addLayout(cards)

        # Gráfico
        self.grafico = GraficoBarras()
        self.grafico.setMinimumHeight(150)
        self.grafico.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        c_layout.addWidget(self.grafico)

        # Barra de busca e excluir
        barra = QHBoxLayout()
        self.busca = campo_busca("Buscar por descrição...")
        self.busca.textChanged.connect(self._filtrar_tabela)
        barra.addWidget(self.busca)
        barra.addStretch()
        self.btn_excluir = btn_perigo("🗑  Excluir")
        self.btn_excluir.clicked.connect(self.excluir_selecionado)
        barra.addWidget(self.btn_excluir)
        c_layout.addLayout(barra)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Data", "Descrição", "Tipo", "Valor"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        c_layout.addWidget(self.table)

        layout.addWidget(conteudo)
        self.carregar_dados_financeiros()

    def _preencher_anos(self):
        self.cb_ano.clear()
        anos = buscar_anos_disponiveis()
        for a in anos:
            self.cb_ano.addItem(str(a))
        # Selecionar ano atual
        idx = self.cb_ano.findText(str(self._ano_atual))
        if idx >= 0:
            self.cb_ano.setCurrentIndex(idx)

    def _trocar_ano(self, ano_str):
        try:
            self._ano_atual = int(ano_str)
            self.carregar_dados_financeiros()
        except ValueError:
            pass

    def _selecionar_mes(self, mes):
        self._mes_atual = mes
        self._aplicar_estilo_btns_mes()
        self.carregar_dados_financeiros()

    def _aplicar_estilo_btns_mes(self):
        btn_normal = f"""QPushButton {{
            background: {COLORS['white']}; color: {COLORS['text_secondary']};
            border: 1.5px solid {COLORS['border']}; border-radius: 6px;
            font-size: 11px; font-weight: 500;
        }} QPushButton:hover {{ background: {COLORS['accent_light']}; color: {COLORS['accent']}; }}"""
        btn_ativo = f"""QPushButton {{
            background: {COLORS['accent']}; color: white;
            border: 1.5px solid {COLORS['accent']}; border-radius: 6px;
            font-size: 11px; font-weight: 700;
        }}"""
        for i, btn in enumerate(self._btns_mes):
            btn.setStyleSheet(btn_ativo if self._mes_atual == i+1 else btn_normal)
            btn.setChecked(self._mes_atual == i+1)
        self.btn_anual.setStyleSheet(btn_ativo if self._mes_atual is None else btn_normal)
        self.btn_anual.setChecked(self._mes_atual is None)

    def carregar_dados_financeiros(self, filtro=""):
        if self._mes_atual is None:
            # Visão anual — mostra todos do ano
            todos = buscar_lancamentos()
            self._dados = [l for l in todos if l["data"].startswith(str(self._ano_atual))]
            self.lbl_titulo_periodo.setText(f"Visão Anual — {self._ano_atual}")
            # Gráfico anual: 12 barras
            resumo = buscar_resumo_mensal(self._ano_atual)
            abrevs = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
            dados_grafico = [{"label": abrevs[m["mes"]-1], "receita": m["receita"], "despesa": m["despesa"]} for m in resumo]
            self.grafico.atualizar(dados_grafico)
        else:
            self._dados = buscar_lancamentos_mes(self._ano_atual, self._mes_atual)
            nome_mes = MESES[self._mes_atual - 1]
            self.lbl_titulo_periodo.setText(f"{nome_mes} — {self._ano_atual}")
            # Gráfico do mês: 1 barra só
            rec = sum(l["valor"] for l in self._dados if l["tipo"] == "Receita")
            des = sum(l["valor"] for l in self._dados if l["tipo"] == "Despesa")
            self.grafico.atualizar([{"label": nome_mes[:3], "receita": rec, "despesa": des}])

        self._popular_tabela(self._dados, filtro)

    def _filtrar_tabela(self):
        filtro = self.busca.text().lower()
        dados_filtrados = [l for l in self._dados if filtro in l["descricao"].lower() or filtro in l["tipo"].lower()] if filtro else self._dados
        self._popular_tabela(dados_filtrados)

    def _popular_tabela(self, dados, filtro=""):
        self.table.setRowCount(len(dados))
        total_rec = 0.0
        total_des = 0.0
        for i, l in enumerate(dados):
            data_br = "/".join(l["data"].split("-")[::-1]) if "-" in l["data"] else l["data"]
            self.table.setItem(i, 0, QTableWidgetItem(data_br))
            self.table.setItem(i, 1, QTableWidgetItem(l["descricao"]))
            item_tipo = QTableWidgetItem(l["tipo"])
            if l["tipo"] == "Receita":
                item_tipo.setForeground(QColor(COLORS["success"]))
                item_tipo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                total_rec += l["valor"]
            else:
                item_tipo.setForeground(QColor(COLORS["danger"]))
                item_tipo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                total_des += l["valor"]
            self.table.setItem(i, 2, item_tipo)
            item_valor = QTableWidgetItem(_fmt_brl(l["valor"]))
            item_valor.setForeground(QColor(COLORS["success"]) if l["tipo"] == "Receita" else QColor(COLORS["danger"]))
            item_valor.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            item_valor.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 3, item_valor)

        self.card_rec.atualizar(_fmt_brl(total_rec))
        self.card_des.atualizar(_fmt_brl(total_des))
        saldo = total_rec - total_des
        self.card_sal.atualizar(_fmt_brl(saldo))
        cor = COLORS["success"] if saldo >= 0 else COLORS["danger"]
        self.card_sal.lbl_valor.setStyleSheet(f"color: {cor}; border: none;")

    def abrir_novo(self):
        dlg = LancamentoDialog(self, ano=self._ano_atual, mes=self._mes_atual)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            salvar_lancamento(dlg.obter_dados())
            self._preencher_anos()
            self.carregar_dados_financeiros()

    def excluir_selecionado(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um lançamento.")
            return
        idx = rows[0].row()
        if idx >= len(self._dados):
            return
        l = self._dados[idx]
        resp = QMessageBox.question(self, "Confirmar exclusão",
            f"Excluir:\n{l['descricao']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_lancamento(l["id"])
            self.carregar_dados_financeiros()
