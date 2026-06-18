# ui/processos_page.py — layout corrigido + honorários + andamentos
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialog,
                             QFormLayout, QComboBox, QTextEdit, QMessageBox,
                             QDialogButtonBox, QTabWidget, QSplitter, QFrame,
                             QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from datetime import date
from config import COLORS
from ui.widgets import (btn_primario, btn_secundario, btn_perigo, campo_busca,
                        input_field, label_titulo, estilo_tabela, separador_h,
                        estilo_dialog)
from core.database import (buscar_processos, salvar_processo, atualizar_processo,
                           excluir_processo, buscar_andamentos, salvar_andamento,
                           excluir_andamento, atualizar_honorarios,
                           buscar_agenda_por_processo, buscar_clientes)

STATUS_OPCOES = ["Em andamento", "Prazo Fatal", "Concluso para Sentença",
                 "Suspenso", "Arquivado"]
TIPOS_ANDAMENTO = ["Geral", "Despacho", "Decisão", "Sentença", "Acórdão",
                   "Intimação", "Citação", "Audiência", "Protocolo", "Recurso"]
CORES_STATUS = {
    "Em andamento":           QColor("#3A6B40"),
    "Prazo Fatal":            QColor("#C0392B"),
    "Concluso para Sentença": QColor("#D4A017"),
    "Suspenso":               QColor("#2563EB"),
    "Arquivado":              QColor("#8A9B8C"),
}

def _fmt_brl(v):
    return f"R$ {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")


# ──────────────────────────────────────────────
# Dialog de cadastro / edição
# ──────────────────────────────────────────────
class ProcessoDialog(QDialog):
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Processo" if not dados else "Editar Processo")
        self.setMinimumWidth(520)
        self.setStyleSheet(estilo_dialog())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo = QLabel("Novo Processo" if not dados else "Editar Processo")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        layout.addWidget(separador_h())

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_numero    = input_field("Ex: 1002345-67.2026.8.26.0000")
        self.txt_acao      = input_field("Ex: Cível, Trabalhista, Penal")
        self.txt_data_dist = input_field("DD/MM/AAAA")
        self.cb_status     = QComboBox()
        self.cb_status.addItems(STATUS_OPCOES)
        self.cb_status.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")

        self.cb_cliente = QComboBox()
        self.cb_cliente.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_cliente.addItem("— Selecione o cliente —", "")
        try:
            for c in buscar_clientes():
                self.cb_cliente.addItem(c["nome"], c["nome"])
        except Exception:
            pass

        self.txt_hon_total = input_field("0,00")
        self.txt_hon_pago  = input_field("0,00")

        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Observações sobre o processo...")
        self.txt_obs.setMaximumHeight(70)
        self.txt_obs.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")

        def lbl(t):
            l = QLabel(f"<b>{t}</b>")
            l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
            return l

        form.addRow(lbl("Nº Processo:"),  self.txt_numero)
        form.addRow(lbl("Cliente:"),      self.cb_cliente)
        form.addRow(lbl("Área / Ação:"),  self.txt_acao)
        form.addRow(lbl("Status:"),       self.cb_status)
        form.addRow(lbl("Distribuição:"), self.txt_data_dist)

        hon_row = QHBoxLayout()
        hon_row.setSpacing(8)
        hon_row.addWidget(QLabel("Total R$:"))
        hon_row.addWidget(self.txt_hon_total)
        hon_row.addWidget(QLabel("Pago R$:"))
        hon_row.addWidget(self.txt_hon_pago)
        w = QWidget(); w.setStyleSheet("background:transparent;border:none;"); w.setLayout(hon_row)
        form.addRow(lbl("Honorários:"), w)
        form.addRow(lbl("Observações:"), self.txt_obs)
        layout.addLayout(form)

        if dados:
            self.txt_numero.setText(dados.get("numero",""))
            idx = self.cb_cliente.findText(dados.get("cliente",""))
            if idx >= 0: self.cb_cliente.setCurrentIndex(idx)
            self.txt_acao.setText(dados.get("acao",""))
            idx2 = self.cb_status.findText(dados.get("status",""))
            if idx2 >= 0: self.cb_status.setCurrentIndex(idx2)
            self.txt_data_dist.setText(dados.get("data_distribuicao",""))
            self.txt_hon_total.setText(str(dados.get("honorarios_total",0) or 0).replace(".",","))
            self.txt_hon_pago.setText(str(dados.get("honorarios_pago",0) or 0).replace(".",","))
            self.txt_obs.setPlainText(dados.get("observacoes",""))

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
        if not self.txt_numero.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o número do processo.")
            return
        self.accept()

    def obter_dados(self):
        def parse_val(txt):
            try: return float(txt.replace(",","."))
            except: return 0.0
        return {
            "numero":            self.txt_numero.text().strip(),
            "cliente":           self.cb_cliente.currentText() if self.cb_cliente.currentData() else self.cb_cliente.currentText(),
            "acao":              self.txt_acao.text().strip(),
            "status":            self.cb_status.currentText(),
            "data_distribuicao": self.txt_data_dist.text().strip(),
            "honorarios_total":  parse_val(self.txt_hon_total.text()),
            "honorarios_pago":   parse_val(self.txt_hon_pago.text()),
            "observacoes":       self.txt_obs.toPlainText().strip(),
        }


# ──────────────────────────────────────────────
# Painel de detalhes
# ──────────────────────────────────────────────
class AndamentoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Andamento")
        self.setMinimumWidth(440)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        titulo = QLabel("Registrar Andamento")
        titulo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        layout.addWidget(separador_h())
        form = QFormLayout()
        form.setSpacing(10)
        self.txt_data = input_field("AAAA-MM-DD")
        self.txt_data.setText(date.today().isoformat())
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(TIPOS_ANDAMENTO)
        self.cb_tipo.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("Descreva o andamento processual...")
        self.txt_desc.setMaximumHeight(100)
        self.txt_desc.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        def lbl(t):
            l = QLabel(f"<b>{t}</b>"); l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;"); return l
        form.addRow(lbl("Data:"), self.txt_data)
        form.addRow(lbl("Tipo:"), self.cb_tipo)
        form.addRow(lbl("Descrição:"), self.txt_desc)
        layout.addLayout(form)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_desc.toPlainText().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Descreva o andamento.")
            return
        self.accept()

    def obter_dados(self):
        return {"data": self.txt_data.text().strip(),
                "tipo": self.cb_tipo.currentText(),
                "descricao": self.txt_desc.toPlainText().strip()}


class PainelDetalhes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._processo = None
        self._andamentos = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho
        self.frame_cab = QFrame()
        self.frame_cab.setStyleSheet(f"background: {COLORS['white']}; border-bottom: 1px solid {COLORS['border']};")
        cab_lay = QVBoxLayout(self.frame_cab)
        cab_lay.setContentsMargins(20, 14, 20, 12)
        cab_lay.setSpacing(4)
        self.lbl_numero = QLabel("Selecione um processo")
        self.lbl_numero.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_numero.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        self.lbl_meta = QLabel("")
        self.lbl_meta.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        self.lbl_meta.setWordWrap(True)
        cab_lay.addWidget(self.lbl_numero)
        cab_lay.addWidget(self.lbl_meta)

        # Cards honorários
        hon_row = QHBoxLayout()
        hon_row.setSpacing(8)
        self.card_total  = self._mini_card("💼 Honorários",  "R$ 0,00", COLORS["text_primary"])
        self.card_pago   = self._mini_card("✔ Recebido",     "R$ 0,00", COLORS["success"])
        self.card_saldo  = self._mini_card("⏳ A Receber",   "R$ 0,00", COLORS["warning"])
        hon_row.addWidget(self.card_total)
        hon_row.addWidget(self.card_pago)
        hon_row.addWidget(self.card_saldo)
        hon_row.addStretch()
        cab_lay.addSpacing(6)
        cab_lay.addLayout(hon_row)
        layout.addWidget(self.frame_cab)

        # Abas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {COLORS['bg_main']}; }}
            QTabBar::tab {{
                padding: 9px 18px; font-size: 12px; font-weight: 600;
                color: {COLORS['text_muted']}; border: none;
                background: transparent; border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{ color: {COLORS['accent']}; border-bottom: 2px solid {COLORS['accent']}; }}
            QTabBar::tab:hover {{ color: {COLORS['text_primary']}; }}
        """)

        # Aba Andamentos
        tab_and = QWidget(); tab_and.setStyleSheet(f"background: {COLORS['bg_main']};")
        lay_and = QVBoxLayout(tab_and); lay_and.setContentsMargins(14, 10, 14, 10); lay_and.setSpacing(8)
        barra_and = QHBoxLayout()
        barra_and.addWidget(QLabel("<b>Histórico de Andamentos</b>"))
        barra_and.addStretch()
        self.btn_add_and = btn_primario("＋ Andamento")
        self.btn_del_and = btn_perigo("🗑"); self.btn_del_and.setFixedWidth(36)
        self.btn_add_and.clicked.connect(self.adicionar_andamento)
        self.btn_del_and.clicked.connect(self.excluir_andamento)
        barra_and.addWidget(self.btn_add_and); barra_and.addWidget(self.btn_del_and)
        lay_and.addLayout(barra_and)
        self.table_and = QTableWidget()
        self.table_and.setColumnCount(3)
        self.table_and.setHorizontalHeaderLabels(["Data", "Tipo", "Descrição"])
        self.table_and.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_and.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_and.setStyleSheet(estilo_tabela())
        self.table_and.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_and.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_and.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_and.verticalHeader().setVisible(False)
        self.table_and.setAlternatingRowColors(True)
        lay_and.addWidget(self.table_and)
        self.tabs.addTab(tab_and, "📋  Andamentos")

        # Aba Agenda
        tab_ag = QWidget(); tab_ag.setStyleSheet(f"background: {COLORS['bg_main']};")
        lay_ag = QVBoxLayout(tab_ag); lay_ag.setContentsMargins(14, 10, 14, 10); lay_ag.setSpacing(8)
        lay_ag.addWidget(QLabel("<b>Compromissos Vinculados</b>"))
        self.table_ag = QTableWidget()
        self.table_ag.setColumnCount(4)
        self.table_ag.setHorizontalHeaderLabels(["Data", "Hora", "Tipo", "Compromisso"])
        self.table_ag.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_ag.setStyleSheet(estilo_tabela())
        self.table_ag.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_ag.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_ag.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_ag.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_ag.verticalHeader().setVisible(False)
        self.table_ag.setAlternatingRowColors(True)
        lay_ag.addWidget(self.table_ag)
        self.tabs.addTab(tab_ag, "📅  Agenda")

        # Aba Observações
        tab_obs = QWidget(); tab_obs.setStyleSheet(f"background: {COLORS['bg_main']};")
        lay_obs = QVBoxLayout(tab_obs); lay_obs.setContentsMargins(14, 10, 14, 10)
        lay_obs.addWidget(QLabel("<b>Observações do Processo</b>"))
        self.txt_obs_view = QTextEdit()
        self.txt_obs_view.setReadOnly(True)
        self.txt_obs_view.setStyleSheet(f"padding: 12px; border: 1px solid {COLORS['border']}; border-radius: 8px; background: {COLORS['white']}; font-size: 12px;")
        lay_obs.addWidget(self.txt_obs_view)
        self.tabs.addTab(tab_obs, "📝  Observações")

        layout.addWidget(self.tabs)

    def _mini_card(self, titulo, valor, cor):
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        frame.setFixedHeight(58); frame.setMinimumWidth(130)
        lay = QVBoxLayout(frame); lay.setContentsMargins(12, 6, 12, 6); lay.setSpacing(2)
        lbl_t = QLabel(titulo); lbl_t.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        lbl_v = QLabel(valor); lbl_v.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_v.setStyleSheet(f"color: {cor}; border: none;")
        lay.addWidget(lbl_t); lay.addWidget(lbl_v)
        frame._lbl_valor = lbl_v
        return frame

    def carregar_processo(self, processo):
        try:
            from PyQt6 import sip
            if sip.isdeleted(self):
                return
        except Exception:
            pass
        try:
            self._processo = processo
            self.lbl_numero.setText(processo["numero"])
            self.lbl_meta.setText(
                f"👤 {processo.get('cliente','')}  •  ⚖️ {processo.get('acao','')}  •  📌 {processo.get('status','')}  •  📅 {processo.get('data_distribuicao','')}")
            total = processo.get("honorarios_total", 0) or 0
            pago  = processo.get("honorarios_pago",  0) or 0
            saldo = total - pago
            self.card_total._lbl_valor.setText(_fmt_brl(total))
            self.card_pago._lbl_valor.setText(_fmt_brl(pago))
            self.card_saldo._lbl_valor.setText(_fmt_brl(saldo))
            self.card_saldo._lbl_valor.setStyleSheet(f"color: {COLORS['success'] if saldo <= 0 else COLORS['warning']}; border: none;")
            self.txt_obs_view.setPlainText(processo.get("observacoes",""))
            self._carregar_andamentos()
            self._carregar_agenda()
        except RuntimeError:
            return  # widget destruído durante o carregamento; ignora com segurança

    def _carregar_andamentos(self):
        if not self._processo: return
        try:
            from PyQt6 import sip
            if sip.isdeleted(self) or sip.isdeleted(self.table_and):
                return
        except Exception:
            pass
        try:
            self._andamentos = buscar_andamentos(self._processo["id"])
            self.table_and.setRowCount(len(self._andamentos))
            for i, a in enumerate(self._andamentos):
                data_br = "/".join(a["data"].split("-")[::-1]) if "-" in a["data"] else a["data"]
                self.table_and.setItem(i, 0, QTableWidgetItem(data_br))
                item_tipo = QTableWidgetItem(a["tipo"])
                item_tipo.setForeground(QColor(COLORS["accent"]))
                item_tipo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table_and.setItem(i, 1, item_tipo)
                self.table_and.setItem(i, 2, QTableWidgetItem(a["descricao"]))
        except RuntimeError:
            return

    def _carregar_agenda(self):
        if not self._processo: return
        try:
            from PyQt6 import sip
            if sip.isdeleted(self) or sip.isdeleted(self.table_ag):
                return
        except Exception:
            pass
        try:
            compromissos = buscar_agenda_por_processo(self._processo["id"])
            self.table_ag.setRowCount(len(compromissos))
            for i, ag in enumerate(compromissos):
                data_br = "/".join(ag["data"].split("-")[::-1]) if "-" in ag["data"] else ag["data"]
                self.table_ag.setItem(i, 0, QTableWidgetItem(data_br))
                self.table_ag.setItem(i, 1, QTableWidgetItem(ag["hora"]))
                self.table_ag.setItem(i, 2, QTableWidgetItem(ag["tipo"]))
                self.table_ag.setItem(i, 3, QTableWidgetItem(ag["titulo"]))
        except RuntimeError:
            return

    def adicionar_andamento(self):
        if not self._processo: return
        dlg = AndamentoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.obter_dados()
            dados["processo_id"] = self._processo["id"]
            salvar_andamento(dados)
            self._carregar_andamentos()

    def excluir_andamento(self):
        rows = self.table_and.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um andamento.")
            return
        a = self._andamentos[rows[0].row()]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir este andamento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_andamento(a["id"])
            self._carregar_andamentos()


# ──────────────────────────────────────────────
# Página principal — layout corrigido
# ──────────────────────────────────────────────
class ProcessosPage(QWidget):
    def __init__(self, parent=None, ao_atualizar=None):
        super().__init__(parent)
        self.ao_atualizar = ao_atualizar
        self._dados = []
        self.init_ui()

    def init_ui(self):
        # Layout principal sem margens excessivas
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── TOPO COMPACTO ──
        topo = QWidget()
        topo.setStyleSheet(f"background: {COLORS['bg_main']};")
        topo.setFixedHeight(120)
        topo_lay = QVBoxLayout(topo)
        topo_lay.setContentsMargins(32, 16, 32, 8)
        topo_lay.setSpacing(8)

        # Linha 1: título + botão novo
        linha1 = QHBoxLayout()
        linha1.addWidget(label_titulo("Processos"))
        linha1.addStretch()
        btn_novo = btn_primario("＋  Novo Processo")
        btn_novo.clicked.connect(self.abrir_novo)
        linha1.addWidget(btn_novo)
        topo_lay.addLayout(linha1)

        # Linha 2: busca + editar + excluir
        linha2 = QHBoxLayout()
        linha2.setSpacing(8)
        self.busca = campo_busca("Buscar por número, cliente, área ou status...")
        self.busca.setMinimumWidth(320)
        self.busca.textChanged.connect(self.filtrar)
        linha2.addWidget(self.busca)
        linha2.addStretch()
        self.btn_editar  = btn_secundario("✏️  Editar")
        self.btn_excluir = btn_perigo("🗑  Excluir")
        self.btn_editar.clicked.connect(self.editar_selecionado)
        self.btn_excluir.clicked.connect(self.excluir_selecionado)
        linha2.addWidget(self.btn_editar)
        linha2.addWidget(self.btn_excluir)
        topo_lay.addLayout(linha2)

        layout.addWidget(topo)

        # Linha separadora
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        # ── SPLITTER: tabela | painel ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORS['border']}; width: 1px; }}")

        # Tabela
        tabela_widget = QWidget()
        tabela_widget.setStyleSheet(f"background: {COLORS['bg_main']};")
        tabela_lay = QVBoxLayout(tabela_widget)
        tabela_lay.setContentsMargins(32, 12, 8, 16)
        tabela_lay.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nº Processo", "Cliente", "Área", "Status"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.clicked.connect(self._abrir_detalhes)
        tabela_lay.addWidget(self.table)
        splitter.addWidget(tabela_widget)

        # Painel de detalhes
        self.painel = PainelDetalhes()
        splitter.addWidget(self.painel)
        splitter.setSizes([500, 580])

        # ── ABAS INTERNAS: Meus Processos | Monitorados (Datajud) ──
        from PyQt6.QtWidgets import QTabWidget
        self.tabs_proc = QTabWidget()
        self.tabs_proc.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{ padding: 8px 18px; font-size: 12px; color: {COLORS['text_secondary']};
                background: {COLORS['bg_main']}; border: none; }}
            QTabBar::tab:selected {{ color: {COLORS['accent']}; font-weight: 700;
                border-bottom: 2px solid {COLORS['accent']}; }}
        """)

        aba_meus = QWidget()
        aba_meus_lay = QVBoxLayout(aba_meus)
        aba_meus_lay.setContentsMargins(0, 0, 0, 0)
        aba_meus_lay.addWidget(splitter)
        self.tabs_proc.addTab(aba_meus, "📁 Meus Processos")

        # Aba de monitorados
        self.aba_monitorados = self._criar_aba_monitorados()
        self.tabs_proc.addTab(self.aba_monitorados, "🔄 Monitorados (Datajud)")

        layout.addWidget(self.tabs_proc)
        self.carregar_dados_processos()
        self.carregar_monitorados()

    def _criar_aba_monitorados(self):
        from PyQt6.QtWidgets import QTabWidget
        w = QWidget()
        w.setStyleSheet(f"background: {COLORS['bg_main']};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(32, 16, 32, 16)
        lay.setSpacing(10)

        topo = QHBoxLayout()
        info = QLabel("Processos cadastrados para monitoramento automático via Datajud. "
                      "Atualizados ao abrir o Legis.")
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; border: none;")
        info.setWordWrap(True)
        topo.addWidget(info, 1)
        self.btn_atualizar_mon = btn_secundario("🔄  Atualizar Agora")
        self.btn_atualizar_mon.clicked.connect(self.atualizar_monitorados_manual)
        topo.addWidget(self.btn_atualizar_mon)
        self.btn_remover_mon = btn_perigo("🗑  Remover")
        self.btn_remover_mon.clicked.connect(self.remover_monitorado_selecionado)
        topo.addWidget(self.btn_remover_mon)
        lay.addLayout(topo)

        self.table_mon = QTableWidget()
        self.table_mon.setColumnCount(6)
        self.table_mon.setHorizontalHeaderLabels(
            ["", "Nº Processo", "Cliente", "Última Movimentação", "Data", "Tribunal"])
        self.table_mon.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_mon.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_mon.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_mon.setStyleSheet(estilo_tabela())
        self.table_mon.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_mon.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_mon.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_mon.verticalHeader().setVisible(False)
        self.table_mon.setAlternatingRowColors(True)
        self.table_mon.clicked.connect(self._ver_movimentacao_monitorada)
        lay.addWidget(self.table_mon)
        return w

    def carregar_monitorados(self):
        from core.database import listar_processos_monitorados
        from PyQt6.QtGui import QColor
        procs = listar_processos_monitorados()
        self.table_mon.setRowCount(len(procs))
        self._monitorados_cache = procs
        for i, p in enumerate(procs):
            # Indicador de novidade
            novidade = "🔴" if p.get("tem_novidade") else "✅"
            item_nov = QTableWidgetItem(novidade)
            from PyQt6.QtCore import Qt as _Qt
            item_nov.setTextAlignment(_Qt.AlignmentFlag.AlignCenter)
            self.table_mon.setItem(i, 0, item_nov)
            # Formatar número
            num = p["numero_processo"]
            num_fmt = num
            if len(num) == 20:
                num_fmt = f"{num[:7]}-{num[7:9]}.{num[9:13]}.{num[13:14]}.{num[14:16]}.{num[16:20]}"
            self.table_mon.setItem(i, 1, QTableWidgetItem(num_fmt))
            self.table_mon.setItem(i, 2, QTableWidgetItem(p.get("cliente", "")))
            mov = p.get("ultima_movimentacao", "")
            item_mov = QTableWidgetItem(mov)
            if p.get("tem_novidade"):
                item_mov.setForeground(QColor(COLORS["danger"]))
            self.table_mon.setItem(i, 3, item_mov)
            # Data formatada
            data_iso = p.get("data_ultima_mov", "")
            data_fmt = data_iso
            if "T" in data_iso:
                partes = data_iso.split("T")
                data_fmt = "/".join(partes[0].split("-")[::-1]) + " " + partes[1][:5]
            self.table_mon.setItem(i, 4, QTableWidgetItem(data_fmt))
            self.table_mon.setItem(i, 5, QTableWidgetItem(p.get("tribunal", "").upper()))

    def _ver_movimentacao_monitorada(self):
        # Ao clicar, marca como visto (tira o vermelho)
        rows = self.table_mon.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        if idx < len(getattr(self, "_monitorados_cache", [])):
            from core.database import marcar_processo_visto
            p = self._monitorados_cache[idx]
            if p.get("tem_novidade"):
                marcar_processo_visto(p["numero_processo"])
                self.carregar_monitorados()

    def remover_monitorado_selecionado(self):
        from PyQt6.QtWidgets import QMessageBox
        from core.database import remover_processo_monitorado
        rows = self.table_mon.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Remover", "Selecione um processo para remover.")
            return
        idx = rows[0].row()
        p = self._monitorados_cache[idx]
        resp = QMessageBox.question(self, "Remover monitoramento",
            f"Remover o processo de {p.get('cliente','')} do monitoramento automático?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            remover_processo_monitorado(p["numero_processo"])
            self.carregar_monitorados()

    def atualizar_monitorados_manual(self):
        from ui.atualizador_processos import AtualizadorProcessosThread
        self.btn_atualizar_mon.setEnabled(False)
        self.btn_atualizar_mon.setText("🔄  Atualizando...")
        self._atualizador = AtualizadorProcessosThread()
        self._atualizador.concluido.connect(self._fim_atualizacao_manual)
        self._atualizador.start()

    def _fim_atualizacao_manual(self, qtd_novidades):
        from PyQt6.QtWidgets import QMessageBox
        self.btn_atualizar_mon.setEnabled(True)
        self.btn_atualizar_mon.setText("🔄  Atualizar Agora")
        self.carregar_monitorados()
        QMessageBox.information(self, "Atualização concluída",
            f"Processos atualizados.\n{qtd_novidades} processo(s) com movimentação nova.")

    def carregar_dados_processos(self, filtro=""):
        self._dados = buscar_processos(filtro)
        # Bloquear sinais durante a recarga evita disparo fantasma de 'clicked'
        # que tentaria acessar o painel enquanto a tabela é reconstruída
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._dados))
        for i, p in enumerate(self._dados):
            self.table.setItem(i, 0, QTableWidgetItem(p["numero"]))
            self.table.setItem(i, 1, QTableWidgetItem(p["cliente"]))
            self.table.setItem(i, 2, QTableWidgetItem(p["acao"]))
            item_st = QTableWidgetItem(p["status"])
            cor = CORES_STATUS.get(p["status"])
            if cor:
                item_st.setForeground(cor)
                item_st.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(i, 3, item_st)
        self.table.blockSignals(False)

    def filtrar(self):
        self.carregar_dados_processos(self.busca.text())

    def _abrir_detalhes(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        idx = rows[0].row()
        if idx >= len(self._dados):
            return
        try:
            from PyQt6 import sip
            if sip.isdeleted(self.painel):
                return
        except Exception:
            pass
        try:
            self.painel.carregar_processo(self._dados[idx])
        except RuntimeError:
            return

    def abrir_novo(self):
        dlg = ProcessoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.obter_dados()
            salvar_processo(dados)
            procs = buscar_processos()
            if procs:
                atualizar_honorarios(procs[0]["id"],
                                     dados["honorarios_total"],
                                     dados["honorarios_pago"])
            self.carregar_dados_processos()
            if self.ao_atualizar: self.ao_atualizar()

    def _linha_selecionada(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um processo.")
            return None
        return rows[0].row()

    def editar_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        p = self._dados[row]
        dlg = ProcessoDialog(self, dados=p)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.obter_dados()
            atualizar_processo(p["id"], dados)
            atualizar_honorarios(p["id"], dados["honorarios_total"], dados["honorarios_pago"])
            self.carregar_dados_processos()
            if self.ao_atualizar: self.ao_atualizar()

    def excluir_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        p = self._dados[row]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir o processo\n{p['numero']}?\n\nEssa ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_processo(p["id"])
            self.carregar_dados_processos()
            if self.ao_atualizar: self.ao_atualizar()
