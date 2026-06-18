# ui/consultas_page.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QDialog, QFormLayout,
                             QComboBox, QTextEdit, QMessageBox, QDialogButtonBox,
                             QSplitter, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from datetime import date, datetime
from config import COLORS
from ui.widgets import (btn_primario, btn_secundario, btn_perigo, campo_busca,
                        input_field, label_titulo, estilo_tabela, separador_h, estilo_dialog)
from core.database import (buscar_consultas, salvar_consulta, atualizar_status_consulta,
                           excluir_consulta, buscar_clientes)

STATUS_CONSULTA = ["Pendente", "Em Análise", "Respondido", "Arquivado"]
CORES_STATUS = {
    "Pendente":    ("#FEF9E7", "#D4A017"),
    "Em Análise":  ("#EFF6FF", "#2563EB"),
    "Respondido":  ("#EAFAF1", "#27AE60"),
    "Arquivado":   ("#F1F5F9", "#5A6B5C"),
}


class NovaConsultaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Consulta Jurídica")
        self.setMinimumSize(500, 420)
        self.setStyleSheet(estilo_dialog())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo_lbl = QLabel("Registrar Consulta Jurídica")
        titulo_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo_lbl)
        layout.addWidget(separador_h())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.txt_titulo = input_field("Assunto da consulta — Ex: Rescisão contratual")
        hoje = date.today()
        self.txt_data = input_field(f"AAAA-MM-DD")
        self.txt_data.setText(hoje.isoformat())
        self.txt_hora = input_field("HH:MM")
        self.txt_hora.setText(datetime.now().strftime("%H:%M"))

        # Dropdown com clientes cadastrados
        self.cb_cliente = QComboBox()
        self.cb_cliente.addItem("— Sem vínculo com cliente —", "")
        try:
            clientes = buscar_clientes()
            for c in clientes:
                self.cb_cliente.addItem(c["nome"], c["nome"])
        except Exception:
            pass
        self.cb_cliente.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")

        self.txt_descricao = QTextEdit()
        self.txt_descricao.setPlaceholderText(
            "Descreva a consulta jurídica em detalhes...\n\n"
            "Ex: Cliente solicita orientação sobre rescisão do contrato de trabalho após 2 anos de serviço, "
            "questionando direito a FGTS e aviso prévio."
        )
        self.txt_descricao.setMinimumHeight(140)
        self.txt_descricao.setStyleSheet(f"""
            QTextEdit {{
                padding: 10px; border: 1.5px solid {COLORS['border']};
                border-radius: 6px; background: white;
                font-size: 12px; color: {COLORS['text_primary']};
                line-height: 1.6;
            }}
            QTextEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)

        form.addRow(QLabel("<b>Assunto:</b>"),    self.txt_titulo)
        form.addRow(QLabel("<b>Data:</b>"),        self.txt_data)
        form.addRow(QLabel("<b>Hora:</b>"),        self.txt_hora)
        form.addRow(QLabel("<b>Cliente:</b>"),     self.cb_cliente)
        form.addRow(QLabel("<b>Descrição:</b>"),   self.txt_descricao)
        layout.addLayout(form)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Registrar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(
            f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_titulo.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o assunto da consulta.")
            return
        if not self.txt_descricao.toPlainText().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Descreva a consulta.")
            return
        self.accept()

    def obter_dados(self):
        return {
            "titulo":    self.txt_titulo.text().strip(),
            "data":      self.txt_data.text().strip(),
            "hora":      self.txt_hora.text().strip(),
            "cliente":   self.cb_cliente.currentData() or "",
            "descricao": self.txt_descricao.toPlainText().strip(),
        }


class ResponderDialog(QDialog):
    def __init__(self, consulta, parent=None):
        super().__init__(parent)
        self.consulta = consulta
        self.setWindowTitle(f"Consulta — {consulta['titulo']}")
        self.setMinimumSize(560, 500)
        self.setStyleSheet(estilo_dialog())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        lbl_tit = QLabel(consulta["titulo"])
        lbl_tit.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_tit.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(lbl_tit)

        data_br = "/".join(consulta["data"].split("-")[::-1]) if "-" in consulta["data"] else consulta["data"]
        info = f"📅 {data_br}  🕐 {consulta['hora']}"
        if consulta.get("cliente"):
            info += f"  👤 {consulta['cliente']}"
        lbl_info = QLabel(info)
        lbl_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(lbl_info)
        layout.addWidget(separador_h())

        # Consulta original
        layout.addWidget(QLabel("<b>Consulta:</b>"))
        txt_cons = QTextEdit()
        txt_cons.setPlainText(consulta["descricao"])
        txt_cons.setReadOnly(True)
        txt_cons.setMaximumHeight(120)
        txt_cons.setStyleSheet(f"padding: 10px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: #FAFCFA; font-size: 12px;")
        layout.addWidget(txt_cons)

        # Status
        form = QFormLayout()
        self.cb_status = QComboBox()
        self.cb_status.addItems(STATUS_CONSULTA)
        idx = self.cb_status.findText(consulta.get("status", "Pendente"))
        if idx >= 0: self.cb_status.setCurrentIndex(idx)
        self.cb_status.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        form.addRow(QLabel("<b>Status:</b>"), self.cb_status)
        layout.addLayout(form)

        # Resposta
        layout.addWidget(QLabel("<b>Resposta / Orientação Jurídica:</b>"))
        self.txt_resposta = QTextEdit()
        self.txt_resposta.setPlaceholderText("Digite aqui a orientação jurídica para o cliente...")
        self.txt_resposta.setPlainText(consulta.get("resposta", ""))
        self.txt_resposta.setStyleSheet(f"""
            QTextEdit {{
                padding: 10px; border: 1.5px solid {COLORS['border']};
                border-radius: 6px; background: white;
                font-size: 12px; color: {COLORS['text_primary']};
            }}
            QTextEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        layout.addWidget(self.txt_resposta)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Fechar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(
            f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def obter_dados(self):
        return self.cb_status.currentText(), self.txt_resposta.toPlainText().strip()


class ConsultasPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dados = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        cab = QHBoxLayout()
        cab.addWidget(label_titulo("Consultas Jurídicas"))
        cab.addStretch()
        btn_novo = btn_primario("＋  Nova Consulta")
        btn_novo.clicked.connect(self.abrir_nova)
        cab.addWidget(btn_novo)
        layout.addLayout(cab)

        sub = QLabel("Registre consultas e orientações jurídicas vinculadas aos clientes.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(sub)
        layout.addWidget(separador_h())

        # Barra de ações
        barra = QHBoxLayout()
        self.busca = campo_busca("Buscar por assunto, cliente ou status...")
        self.busca.textChanged.connect(self.filtrar)
        barra.addWidget(self.busca)

        self.cb_filtro_status = QComboBox()
        self.cb_filtro_status.addItem("Todos os status", "")
        for s in STATUS_CONSULTA:
            self.cb_filtro_status.addItem(s, s)
        self.cb_filtro_status.setFixedWidth(160)
        self.cb_filtro_status.setStyleSheet(f"padding: 7px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_filtro_status.currentIndexChanged.connect(self.filtrar)
        barra.addWidget(self.cb_filtro_status)
        barra.addStretch()

        self.btn_responder = btn_secundario("📝  Abrir / Responder")
        self.btn_excluir   = btn_perigo("🗑  Excluir")
        self.btn_responder.clicked.connect(self.abrir_responder)
        self.btn_excluir.clicked.connect(self.excluir_selecionado)
        barra.addWidget(self.btn_responder)
        barra.addWidget(self.btn_excluir)
        layout.addLayout(barra)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Data", "Hora", "Assunto", "Cliente", "Status", "Resposta"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.abrir_responder)
        layout.addWidget(self.table)

        self.carregar_consultas()

    def carregar_consultas(self, filtro="", status_filtro=""):
        todos = buscar_consultas(filtro)
        if status_filtro:
            todos = [c for c in todos if c["status"] == status_filtro]
        self._dados = todos
        self.table.setRowCount(len(self._dados))

        for i, c in enumerate(self._dados):
            data_br = "/".join(c["data"].split("-")[::-1]) if "-" in c["data"] else c["data"]
            self.table.setItem(i, 0, QTableWidgetItem(data_br))
            self.table.setItem(i, 1, QTableWidgetItem(c["hora"]))
            self.table.setItem(i, 2, QTableWidgetItem(c["titulo"]))
            self.table.setItem(i, 3, QTableWidgetItem(c.get("cliente", "") or "—"))

            # Badge de status colorido
            status = c.get("status", "Pendente")
            item_st = QTableWidgetItem(f"  {status}  ")
            bg, fg = CORES_STATUS.get(status, ("#F1F5F9", "#5A6B5C"))
            item_st.setForeground(QColor(fg))
            item_st.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(i, 4, item_st)

            resp = c.get("resposta", "")
            item_resp = QTableWidgetItem("✔ Sim" if resp else "—")
            item_resp.setForeground(QColor(COLORS["success"]) if resp else QColor(COLORS["text_muted"]))
            self.table.setItem(i, 5, item_resp)

    def filtrar(self):
        filtro = self.busca.text()
        status = self.cb_filtro_status.currentData() or ""
        self.carregar_consultas(filtro, status)

    def abrir_nova(self):
        dlg = NovaConsultaDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            salvar_consulta(dlg.obter_dados())
            self.carregar_consultas()

    def _linha_selecionada(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione uma consulta.")
            return None
        return rows[0].row()

    def abrir_responder(self):
        row = self._linha_selecionada()
        if row is None: return
        c = self._dados[row]
        dlg = ResponderDialog(c, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            status, resposta = dlg.obter_dados()
            atualizar_status_consulta(c["id"], status, resposta)
            self.carregar_consultas()

    def excluir_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        c = self._dados[row]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir a consulta:\n{c['titulo']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_consulta(c["id"])
            self.carregar_consultas()
