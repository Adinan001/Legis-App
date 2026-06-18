# ui/clientes_page.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QDialog, QFormLayout,
                             QComboBox, QMessageBox, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import COLORS
from ui.widgets import (btn_primario, btn_secundario, btn_perigo, campo_busca,
                        input_field, label_titulo, estilo_tabela, separador_h, estilo_dialog)
from core.database import buscar_clientes, salvar_cliente, atualizar_cliente, excluir_cliente


class ClienteDialog(QDialog):
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Cliente" if not dados else "Editar Cliente")
        self.setMinimumWidth(460)
        self.setStyleSheet(estilo_dialog())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo = QLabel("Novo Cliente" if not dados else "Editar Cliente")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(titulo)
        layout.addWidget(separador_h())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.txt_nome = input_field("Nome Completo ou Razão Social")
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Pessoa Física", "Pessoa Jurídica"])
        self.cb_tipo.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.txt_documento = input_field("CPF ou CNPJ")
        self.txt_contato = input_field("(DDD) 9 9999-9999")
        self.txt_email = input_field("email@exemplo.com")
        self.txt_endereco = input_field("Endereço completo (opcional)")

        form.addRow(QLabel("<b>Nome / Razão:</b>"), self.txt_nome)
        form.addRow(QLabel("<b>Tipo:</b>"), self.cb_tipo)
        form.addRow(QLabel("<b>CPF / CNPJ:</b>"), self.txt_documento)
        form.addRow(QLabel("<b>Telefone:</b>"), self.txt_contato)
        form.addRow(QLabel("<b>E-mail:</b>"), self.txt_email)
        form.addRow(QLabel("<b>Endereço:</b>"), self.txt_endereco)
        layout.addLayout(form)

        if dados:
            self.txt_nome.setText(dados.get("nome",""))
            idx = self.cb_tipo.findText(dados.get("tipo",""))
            if idx >= 0: self.cb_tipo.setCurrentIndex(idx)
            self.txt_documento.setText(dados.get("documento",""))
            self.txt_contato.setText(dados.get("contato",""))
            self.txt_email.setText(dados.get("email",""))
            self.txt_endereco.setText(dados.get("endereco",""))

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
        if not self.txt_nome.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do cliente.")
            return
        self.accept()

    def obter_dados(self):
        return {
            "nome": self.txt_nome.text().strip(),
            "tipo": self.cb_tipo.currentText(),
            "documento": self.txt_documento.text().strip(),
            "contato": self.txt_contato.text().strip(),
            "email": self.txt_email.text().strip(),
            "endereco": self.txt_endereco.text().strip(),
        }


class ClientesPage(QWidget):
    def __init__(self, parent=None, ao_atualizar=None):
        super().__init__(parent)
        self.ao_atualizar = ao_atualizar
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        cab = QHBoxLayout()
        cab.addWidget(label_titulo("Clientes"))
        cab.addStretch()
        btn_novo = btn_primario("＋  Novo Cliente")
        btn_novo.clicked.connect(self.abrir_novo)
        cab.addWidget(btn_novo)
        layout.addLayout(cab)
        layout.addWidget(separador_h())

        barra = QHBoxLayout()
        self.busca = campo_busca("Buscar por nome, CPF/CNPJ ou telefone...")
        self.busca.setMinimumWidth(300)
        self.busca.textChanged.connect(self.filtrar)
        barra.addWidget(self.busca)
        barra.addStretch()
        self.btn_editar = btn_secundario("✏️  Editar")
        self.btn_excluir = btn_perigo("🗑  Excluir")
        self.btn_editar.clicked.connect(self.editar_selecionado)
        self.btn_excluir.clicked.connect(self.excluir_selecionado)
        barra.addWidget(self.btn_editar)
        barra.addWidget(self.btn_excluir)
        layout.addLayout(barra)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nome / Razão Social", "Tipo", "CPF / CNPJ", "Telefone", "E-mail"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self._dados = []
        self.carregar_dados_clientes()

    def carregar_dados_clientes(self, filtro=""):
        self._dados = buscar_clientes(filtro)
        self.table.setRowCount(len(self._dados))
        for i, c in enumerate(self._dados):
            self.table.setItem(i, 0, QTableWidgetItem(c["nome"]))
            item_tipo = QTableWidgetItem(c["tipo"])
            if c["tipo"] == "Pessoa Jurídica":
                item_tipo.setForeground(__import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(COLORS["blue"]))
            self.table.setItem(i, 1, item_tipo)
            self.table.setItem(i, 2, QTableWidgetItem(c["documento"]))
            self.table.setItem(i, 3, QTableWidgetItem(c["contato"]))
            self.table.setItem(i, 4, QTableWidgetItem(c.get("email","")))

    def filtrar(self):
        self.carregar_dados_clientes(self.busca.text())

    def abrir_novo(self):
        dlg = ClienteDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            salvar_cliente(dlg.obter_dados())
            self.carregar_dados_clientes()
            if self.ao_atualizar: self.ao_atualizar()

    def _linha_selecionada(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um cliente na tabela.")
            return None
        return rows[0].row()

    def editar_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        dlg = ClienteDialog(self, dados=self._dados[row])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            atualizar_cliente(self._dados[row]["id"], dlg.obter_dados())
            self.carregar_dados_clientes()
            if self.ao_atualizar: self.ao_atualizar()

    def excluir_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        c = self._dados[row]
        resp = QMessageBox.question(self, "Confirmar exclusão",
            f"Excluir o cliente\n{c['nome']}?\n\nEssa ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_cliente(c["id"])
            self.carregar_dados_clientes()
            if self.ao_atualizar: self.ao_atualizar()
