# ui/usuarios_page.py — Gerenciamento de usuários (só Administrador)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QDialog, QFormLayout,
                             QComboBox, QLineEdit, QMessageBox, QDialogButtonBox,
                             QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from config import COLORS
from ui.widgets import (btn_primario, btn_secundario, btn_perigo, label_titulo,
                        input_field, estilo_tabela, separador_h, estilo_dialog)
from core.database import (buscar_usuarios, salvar_usuario, atualizar_usuario,
                           excluir_usuario, alterar_senha)

PERFIS = ["Administrador", "Advogado", "Estagiário"]
CORES_PERFIL = {
    "Administrador": COLORS["danger"],
    "Advogado":      COLORS["accent"],
    "Estagiário":    COLORS["blue"],
}
PERMISSOES = {
    "Administrador": "Acesso total ao sistema",
    "Advogado":      "Acesso a tudo exceto Configurações do sistema",
    "Estagiário":    "Acesso apenas a Processos e Agenda",
}


class UsuarioDialog(QDialog):
    def __init__(self, parent=None, dados=None, modo="novo"):
        super().__init__(parent)
        self.modo = modo
        self.setWindowTitle("Novo Usuário" if modo == "novo" else "Editar Usuário")
        self.setMinimumWidth(440)
        self.setStyleSheet(estilo_dialog())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        titulo = QLabel("Novo Usuário" if modo == "novo" else "Editar Usuário")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        layout.addWidget(separador_h())

        form = QFormLayout(); form.setSpacing(10)

        self.txt_nome  = input_field("Nome completo")
        self.txt_login = input_field("Nome de usuário (sem espaços)")
        self.cb_perfil = QComboBox()
        self.cb_perfil.addItems(PERFIS)
        self.cb_perfil.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_perfil.currentTextChanged.connect(self._mostrar_permissoes)

        self.lbl_perm = QLabel("")
        self.lbl_perm.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")

        self.txt_senha = input_field("Mínimo 6 caracteres")
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_conf = input_field("Confirme a senha")
        self.txt_conf.setEchoMode(QLineEdit.EchoMode.Password)

        self.cb_ativo = QCheckBox("Usuário ativo")
        self.cb_ativo.setChecked(True)
        self.cb_ativo.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")

        def lbl(t):
            l = QLabel(f"<b>{t}</b>")
            l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
            return l

        form.addRow(lbl("Nome:"),    self.txt_nome)
        form.addRow(lbl("Usuário:"), self.txt_login)
        form.addRow(lbl("Perfil:"),  self.cb_perfil)
        form.addRow("",              self.lbl_perm)

        if modo == "novo":
            form.addRow(lbl("Senha:"),    self.txt_senha)
            form.addRow(lbl("Confirmar:"), self.txt_conf)
        else:
            lbl_obs = QLabel("Deixe em branco para não alterar a senha")
            lbl_obs.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
            form.addRow(lbl("Nova Senha:"), self.txt_senha)
            form.addRow("", lbl_obs)

        form.addRow("", self.cb_ativo)
        layout.addLayout(form)

        if dados:
            self.txt_nome.setText(dados.get("nome", ""))
            self.txt_login.setText(dados.get("login", ""))
            idx = self.cb_perfil.findText(dados.get("perfil", ""))
            if idx >= 0: self.cb_perfil.setCurrentIndex(idx)
            self.cb_ativo.setChecked(bool(dados.get("ativo", 1)))

        self._mostrar_permissoes(self.cb_perfil.currentText())

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def _mostrar_permissoes(self, perfil):
        self.lbl_perm.setText(f"ℹ️  {PERMISSOES.get(perfil, '')}")

    def validar(self):
        if not self.txt_nome.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome."); return
        if not self.txt_login.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o usuário."); return
        if " " in self.txt_login.text():
            QMessageBox.warning(self, "Inválido", "O usuário não pode ter espaços."); return
        senha = self.txt_senha.text()
        if self.modo == "novo":
            if len(senha) < 6:
                QMessageBox.warning(self, "Senha fraca", "A senha deve ter no mínimo 6 caracteres."); return
            if senha != self.txt_conf.text():
                QMessageBox.warning(self, "Senhas diferentes", "As senhas não coincidem."); return
        elif senha and len(senha) < 6:
            QMessageBox.warning(self, "Senha fraca", "A senha deve ter no mínimo 6 caracteres."); return
        self.accept()

    def obter_dados(self):
        return {
            "nome":   self.txt_nome.text().strip(),
            "login":  self.txt_login.text().strip().lower(),
            "senha":  self.txt_senha.text(),
            "perfil": self.cb_perfil.currentText(),
            "ativo":  1 if self.cb_ativo.isChecked() else 0,
        }


class UsuariosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dados = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho fixo
        cab = QWidget()
        cab.setFixedHeight(72)
        cab.setStyleSheet(f"background: {COLORS['bg_main']};")
        cab_lay = QVBoxLayout(cab)
        cab_lay.setContentsMargins(32, 10, 32, 6)
        cab_lay.setSpacing(2)
        lbl = QLabel("Usuários do Sistema")
        lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        sub = QLabel("Gerencie os usuários e seus níveis de acesso.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        cab_lay.addWidget(lbl)
        cab_lay.addWidget(sub)
        layout.addWidget(cab)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLORS['border']};")
        layout.addWidget(sep)

        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COLORS['bg_main']};")
        cont_lay = QVBoxLayout(conteudo)
        cont_lay.setContentsMargins(32, 16, 32, 16)
        cont_lay.setSpacing(12)

        # Legenda de perfis
        leg_row = QHBoxLayout()
        for perfil, cor in CORES_PERFIL.items():
            lbl_leg = QLabel(f"● {perfil} — {PERMISSOES[perfil]}")
            lbl_leg.setStyleSheet(f"color: {cor}; font-size: 11px; border: none;")
            leg_row.addWidget(lbl_leg)
        leg_row.addStretch()
        cont_lay.addLayout(leg_row)

        # Barra de ações
        barra = QHBoxLayout()
        btn_novo = btn_primario("＋  Novo Usuário")
        btn_novo.clicked.connect(self.abrir_novo)
        barra.addWidget(btn_novo)
        barra.addStretch()
        self.btn_editar  = btn_secundario("✏️  Editar")
        self.btn_excluir = btn_perigo("🗑  Excluir")
        self.btn_editar.clicked.connect(self.editar_selecionado)
        self.btn_excluir.clicked.connect(self.excluir_selecionado)
        barra.addWidget(self.btn_editar)
        barra.addWidget(self.btn_excluir)
        cont_lay.addLayout(barra)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nome", "Usuário", "Perfil", "Status", "Criado em"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        cont_lay.addWidget(self.table)

        layout.addWidget(conteudo)
        self.carregar_usuarios()

    def carregar_usuarios(self):
        self._dados = buscar_usuarios()
        self.table.setRowCount(len(self._dados))
        for i, u in enumerate(self._dados):
            self.table.setItem(i, 0, QTableWidgetItem(u["nome"]))
            self.table.setItem(i, 1, QTableWidgetItem(u["login"]))
            item_perfil = QTableWidgetItem(u["perfil"])
            item_perfil.setForeground(QColor(CORES_PERFIL.get(u["perfil"], COLORS["text_primary"])))
            item_perfil.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(i, 2, item_perfil)
            status = "✔ Ativo" if u.get("ativo", 1) else "✗ Inativo"
            item_st = QTableWidgetItem(status)
            item_st.setForeground(QColor(COLORS["success"] if u.get("ativo", 1) else COLORS["danger"]))
            self.table.setItem(i, 3, item_st)
            data_br = "/".join(u.get("data_criacao","").split("-")[::-1]) if u.get("data_criacao") else "—"
            self.table.setItem(i, 4, QTableWidgetItem(data_br))

    def abrir_novo(self):
        dlg = UsuarioDialog(self, modo="novo")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                salvar_usuario(dlg.obter_dados())
                self.carregar_usuarios()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível criar o usuário.\nO login pode já estar em uso.\n{e}")

    def _linha_selecionada(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um usuário."); return None
        return rows[0].row()

    def editar_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        u = self._dados[row]
        dlg = UsuarioDialog(self, dados=u, modo="editar")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.obter_dados()
            atualizar_usuario(u["id"], dados)
            if dados.get("senha"):
                alterar_senha(u["id"], dados["senha"])
            self.carregar_usuarios()

    def excluir_selecionado(self):
        row = self._linha_selecionada()
        if row is None: return
        u = self._dados[row]
        if u["login"] == "admin":
            QMessageBox.warning(self, "Não permitido", "O administrador padrão não pode ser excluído."); return
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir o usuário '{u['nome']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_usuario(u["id"])
            self.carregar_usuarios()
