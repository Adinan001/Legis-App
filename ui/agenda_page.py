# ui/agenda_page.py — com cálculo automático de prazo
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QDialog, QFormLayout,
                             QComboBox, QTextEdit, QMessageBox, QDialogButtonBox,
                             QSpinBox, QCheckBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from datetime import date, timedelta
from config import COLORS
from ui.widgets import (btn_primario, btn_secundario, btn_perigo, campo_busca,
                        input_field, label_titulo, estilo_tabela, separador_h,
                        estilo_dialog)
from core.database import (buscar_agenda, salvar_compromisso, concluir_compromisso,
                           excluir_compromisso, calcular_data_prazo)

TIPOS = ["Audiência", "Prazo Fatal", "Reunião", "Diligência",
         "Protocolo", "Intimação", "Recurso", "Outro"]

CORES_TIPO = {
    "Audiência":  "#2563EB",
    "Prazo Fatal":"#C0392B",
    "Reunião":    "#3A6B40",
    "Diligência": "#D4A017",
    "Protocolo":  "#7C3AED",
    "Intimação":  "#D4A017",
    "Recurso":    "#C0392B",
    "Outro":      "#5A6B5C",
}


def _dias_restantes(data_iso):
    try:
        return (date.fromisoformat(data_iso) - date.today()).days
    except Exception:
        return None


class CompromissoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Compromisso / Prazo")
        self.setMinimumWidth(480)
        self.setStyleSheet(estilo_dialog())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo_lbl = QLabel("Agendar Compromisso")
        titulo_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo_lbl)
        layout.addWidget(separador_h())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def lbl(t):
            l = QLabel(f"<b>{t}</b>")
            l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
            return l

        self.txt_titulo = input_field("Título do compromisso")
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(TIPOS)
        self.cb_tipo.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_tipo.currentTextChanged.connect(self._tipo_alterado)

        # Data manual
        self.txt_data = input_field(f"AAAA-MM-DD")
        self.txt_data.setText(date.today().isoformat())
        self.txt_hora = input_field("HH:MM")
        self.txt_hora.setText("09:00")
        self.txt_processo = input_field("Nº do processo vinculado (opcional)")

        # Cálculo automático de prazo
        self.frame_prazo = QFrame()
        self.frame_prazo.setStyleSheet(f"background: {COLORS['accent_light']}; border: 1px solid {COLORS['accent']}40; border-radius: 8px;")
        prazo_lay = QVBoxLayout(self.frame_prazo)
        prazo_lay.setContentsMargins(12, 10, 12, 10)
        prazo_lay.setSpacing(8)

        prazo_tit = QLabel("⚡  Calcular prazo automaticamente")
        prazo_tit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        prazo_tit.setStyleSheet(f"color: {COLORS['accent']}; border: none; background: transparent;")
        prazo_lay.addWidget(prazo_tit)

        prazo_row = QHBoxLayout()
        prazo_row.addWidget(QLabel("Data da intimação:"))
        self.txt_intimacao = input_field("AAAA-MM-DD")
        self.txt_intimacao.setPlaceholderText(date.today().isoformat())
        prazo_row.addWidget(self.txt_intimacao)
        prazo_row.addWidget(QLabel("Prazo (dias):"))
        self.spin_dias = QSpinBox()
        self.spin_dias.setRange(1, 365)
        self.spin_dias.setValue(15)
        self.spin_dias.setStyleSheet(f"padding: 6px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        prazo_row.addWidget(self.spin_dias)
        btn_calc = btn_primario("Calcular")
        btn_calc.setFixedHeight(32)
        btn_calc.clicked.connect(self._calcular_prazo)
        prazo_row.addWidget(btn_calc)
        prazo_lay.addLayout(prazo_row)

        self.lbl_prazo_resultado = QLabel("")
        self.lbl_prazo_resultado.setStyleSheet(f"color: {COLORS['accent']}; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        prazo_lay.addWidget(self.lbl_prazo_resultado)

        self.txt_descricao = QTextEdit()
        self.txt_descricao.setPlaceholderText("Detalhes adicionais (opcional)...")
        self.txt_descricao.setMaximumHeight(60)
        self.txt_descricao.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")

        form.addRow(lbl("Título:"),    self.txt_titulo)
        form.addRow(lbl("Tipo:"),      self.cb_tipo)
        form.addRow(lbl("Data:"),      self.txt_data)
        form.addRow(lbl("Hora:"),      self.txt_hora)
        form.addRow(lbl("Processo:"),  self.txt_processo)
        form.addRow(lbl("Detalhes:"),  self.txt_descricao)
        layout.addLayout(form)
        layout.addWidget(self.frame_prazo)

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

    def _tipo_alterado(self, tipo):
        # Pré-define prazos comuns
        prazos_padrão = {
            "Prazo Fatal": 15,
            "Recurso":     15,
            "Intimação":   5,
            "Protocolo":   3,
        }
        if tipo in prazos_padrão:
            self.spin_dias.setValue(prazos_padrão[tipo])

    def _calcular_prazo(self):
        data_ini = self.txt_intimacao.text().strip() or date.today().isoformat()
        dias = self.spin_dias.value()
        data_fim = calcular_data_prazo(data_ini, dias)
        if data_fim:
            data_br = "/".join(data_fim.split("-")[::-1])
            self.txt_data.setText(data_fim)
            dias_rest = _dias_restantes(data_fim)
            self.lbl_prazo_resultado.setText(
                f"✅  Prazo calculado: {data_br}  ({dias_rest} dias a partir de hoje)")
        else:
            self.lbl_prazo_resultado.setText("❌  Data de intimação inválida.")

    def validar(self):
        if not self.txt_titulo.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o título.")
            return
        self.accept()

    def obter_dados(self):
        return {
            "titulo":             self.txt_titulo.text().strip(),
            "data":               self.txt_data.text().strip(),
            "hora":               self.txt_hora.text().strip() or "00:00",
            "tipo":               self.cb_tipo.currentText(),
            "processo_vinculado": self.txt_processo.text().strip(),
            "descricao":          self.txt_descricao.toPlainText().strip(),
        }


class AgendaPage(QWidget):
    def __init__(self, parent=None, ao_atualizar=None):
        super().__init__(parent)
        self.ao_atualizar = ao_atualizar
        self._dados = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(10)

        cab = QHBoxLayout()
        cab.addWidget(label_titulo("Agenda & Prazos"))
        cab.addStretch()
        btn_novo = btn_primario("＋  Novo Compromisso")
        btn_novo.clicked.connect(self.abrir_novo)
        cab.addWidget(btn_novo)
        layout.addLayout(cab)
        layout.addWidget(separador_h())

        # Filtros rápidos
        filtros_row = QHBoxLayout()
        filtros_row.setSpacing(8)
        self.busca = campo_busca("Buscar compromisso...")
        self.busca.textChanged.connect(self.filtrar)
        filtros_row.addWidget(self.busca)

        self.cb_filtro = QComboBox()
        self.cb_filtro.setFixedWidth(160)
        self.cb_filtro.addItems(["Todos", "Hoje", "Esta semana", "Pendentes", "Vencidos", "Concluídos"])
        self.cb_filtro.setStyleSheet(f"padding: 7px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_filtro.currentIndexChanged.connect(self.filtrar)
        filtros_row.addWidget(self.cb_filtro)

        filtros_row.addStretch()
        self.btn_concluir = btn_secundario("✔  Concluído")
        self.btn_excluir  = btn_perigo("🗑  Excluir")
        self.btn_concluir.clicked.connect(self.concluir_selecionado)
        self.btn_excluir.clicked.connect(self.excluir_selecionado)
        filtros_row.addWidget(self.btn_concluir)
        filtros_row.addWidget(self.btn_excluir)
        layout.addLayout(filtros_row)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Data", "Hora", "Tipo", "Compromisso", "Processo", "Restam", "Situação"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.carregar_dados_agenda()

    def carregar_dados_agenda(self, filtro=""):
        todos = buscar_agenda()
        hoje = date.today().isoformat()
        semana = (date.today() + timedelta(days=7)).isoformat()

        filtro_tipo = self.cb_filtro.currentText() if hasattr(self, 'cb_filtro') else "Todos"
        texto = self.busca.text().lower() if hasattr(self, 'busca') else ""

        dados = todos
        if filtro_tipo == "Hoje":
            dados = [a for a in todos if a["data"] == hoje]
        elif filtro_tipo == "Esta semana":
            dados = [a for a in todos if hoje <= a["data"] <= semana]
        elif filtro_tipo == "Pendentes":
            dados = [a for a in todos if not a["concluido"] and a["data"] >= hoje]
        elif filtro_tipo == "Vencidos":
            dados = [a for a in todos if not a["concluido"] and a["data"] < hoje]
        elif filtro_tipo == "Concluídos":
            dados = [a for a in todos if a["concluido"]]

        if texto:
            dados = [a for a in dados if texto in a["titulo"].lower()
                     or texto in a.get("processo_vinculado","").lower()]

        self._dados = dados
        self.table.setRowCount(len(self._dados))

        for i, a in enumerate(self._dados):
            data_br = "/".join(a["data"].split("-")[::-1]) if "-" in a["data"] else a["data"]
            self.table.setItem(i, 0, QTableWidgetItem(data_br))
            self.table.setItem(i, 1, QTableWidgetItem(a["hora"]))

            item_tipo = QTableWidgetItem(a["tipo"])
            cor_tipo = CORES_TIPO.get(a["tipo"], COLORS["text_secondary"])
            item_tipo.setForeground(QColor(cor_tipo))
            item_tipo.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(i, 2, item_tipo)

            self.table.setItem(i, 3, QTableWidgetItem(a["titulo"]))
            self.table.setItem(i, 4, QTableWidgetItem(a.get("processo_vinculado","")))

            # Contagem regressiva
            dias = _dias_restantes(a["data"])
            if a["concluido"]:
                item_dias = QTableWidgetItem("—")
                item_dias.setForeground(QColor(COLORS["text_muted"]))
            elif dias is None:
                item_dias = QTableWidgetItem("?")
            elif dias < 0:
                item_dias = QTableWidgetItem(f"⛔ {abs(dias)}d atrás")
                item_dias.setForeground(QColor(COLORS["danger"]))
                item_dias.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif dias == 0:
                item_dias = QTableWidgetItem("🔴 Hoje")
                item_dias.setForeground(QColor(COLORS["warning"]))
                item_dias.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif dias <= 3:
                item_dias = QTableWidgetItem(f"⚠️ {dias}d")
                item_dias.setForeground(QColor(COLORS["warning"]))
            elif dias <= 7:
                item_dias = QTableWidgetItem(f"📅 {dias}d")
                item_dias.setForeground(QColor(COLORS["blue"]))
            else:
                item_dias = QTableWidgetItem(f"{dias}d")
                item_dias.setForeground(QColor(COLORS["text_muted"]))
            self.table.setItem(i, 5, item_dias)

            # Situação
            if a["concluido"]:
                item_sit = QTableWidgetItem("✔ Concluído")
                item_sit.setForeground(QColor(COLORS["success"]))
            elif dias is not None and dias < 0:
                item_sit = QTableWidgetItem("⛔ Vencido")
                item_sit.setForeground(QColor(COLORS["danger"]))
                item_sit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif dias == 0:
                item_sit = QTableWidgetItem("🔴 Hoje")
                item_sit.setForeground(QColor(COLORS["warning"]))
                item_sit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            else:
                item_sit = QTableWidgetItem("Pendente")
                item_sit.setForeground(QColor(COLORS["text_secondary"]))
            self.table.setItem(i, 6, item_sit)

    def filtrar(self):
        self.carregar_dados_agenda()

    def abrir_novo(self):
        dlg = CompromissoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            salvar_compromisso(dlg.obter_dados())
            self.carregar_dados_agenda()
            if self.ao_atualizar: self.ao_atualizar()

    def _linha_selecionada(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um compromisso.")
            return None
        return rows[0].row()

    def concluir_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        concluir_compromisso(self._dados[row]["id"])
        self.carregar_dados_agenda()
        if self.ao_atualizar: self.ao_atualizar()

    def excluir_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir:\n{self._dados[row]['titulo']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_compromisso(self._dados[row]["id"])
            self.carregar_dados_agenda()
            if self.ao_atualizar: self.ao_atualizar()
