# ui/doutrina_page.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QListWidget, QListWidgetItem, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QDialog, QFormLayout, QComboBox, QTextEdit,
                             QMessageBox, QDialogButtonBox, QSplitter, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from config import COLORS, AREAS_DIREITO
from ui.widgets import (btn_primario, btn_perigo, btn_secundario, input_field,
                        label_titulo, separador_h, estilo_tabela, estilo_dialog)
from core.database import (buscar_doutrina_temas, salvar_doutrina_tema,
                           excluir_doutrina_tema, buscar_doutrina_entradas,
                           salvar_doutrina_entrada, excluir_doutrina_entrada)


class NovoTemaDoutrinaDialog(QDialog):
    def __init__(self, parent=None, area_atual=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Tema de Doutrina")
        self.setMinimumWidth(420)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)
        titulo = QLabel("Criar Novo Tema")
        titulo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        layout.addWidget(separador_h())
        form = QFormLayout(); form.setSpacing(10)
        self.cb_area = QComboBox()
        self.cb_area.addItems(AREAS_DIREITO)
        self.cb_area.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        if area_atual:
            idx = self.cb_area.findText(area_atual)
            if idx >= 0: self.cb_area.setCurrentIndex(idx)
        self.txt_tema = input_field("Ex: Teoria do Crime, Responsabilidade Civil Objetiva")
        def lbl(t):
            l = QLabel(f"<b>{t}</b>"); l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;"); return l
        form.addRow(lbl("Área do Direito:"), self.cb_area)
        form.addRow(lbl("Nome do Tema:"), self.txt_tema)
        layout.addLayout(form)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Criar Tema")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar); botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_tema.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do tema.")
            return
        self.accept()

    def obter_dados(self):
        return self.cb_area.currentText(), self.txt_tema.text().strip()


class NovaEntradaDoutrinaDialog(QDialog):
    def __init__(self, parent=None, tema_nome=""):
        super().__init__(parent)
        self.setWindowTitle(f"Adicionar Doutrina — {tema_nome}")
        self.setMinimumSize(560, 500)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        titulo = QLabel("Nova Entrada Doutrinária")
        titulo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        if tema_nome:
            sub = QLabel(f"Tema: {tema_nome}")
            sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            layout.addWidget(sub)
        layout.addWidget(separador_h())
        form = QFormLayout(); form.setSpacing(10)
        self.txt_autor   = input_field("Ex: Rogério Greco, Nelson Nery Jr.")
        self.txt_obra    = input_field("Ex: Curso de Direito Penal, Vol. I")
        self.txt_editora = input_field("Ex: Impetus, RT, Forense")
        self.txt_ano     = input_field("Ex: 2023")
        self.txt_paginas = input_field("Ex: p. 245-248")
        def lbl(t):
            l = QLabel(f"<b>{t}</b>"); l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;"); return l
        form.addRow(lbl("Autor(es):"),    self.txt_autor)
        form.addRow(lbl("Obra / Título:"), self.txt_obra)
        form.addRow(lbl("Editora:"),      self.txt_editora)
        form.addRow(lbl("Ano:"),          self.txt_ano)
        form.addRow(lbl("Páginas:"),      self.txt_paginas)
        layout.addLayout(form)
        layout.addWidget(lbl("Trecho / Excerto Doutrinário:"))
        self.txt_trecho = QTextEdit()
        self.txt_trecho.setPlaceholderText('Cole ou digite o trecho relevante da doutrina...')
        self.txt_trecho.setStyleSheet(f"""
            QTextEdit {{
                padding: 10px; border: 1.5px solid {COLORS['border']};
                border-radius: 6px; background: white;
                font-size: 12px; font-family: 'Times New Roman', serif;
                color: {COLORS['text_primary']}; line-height: 1.6;
            }}
            QTextEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        layout.addWidget(self.txt_trecho)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar); botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_autor.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o autor."); return
        if not self.txt_trecho.toPlainText().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o trecho doutrinário."); return
        self.accept()

    def obter_dados(self):
        return {
            "autor":   self.txt_autor.text().strip(),
            "obra":    self.txt_obra.text().strip(),
            "editora": self.txt_editora.text().strip(),
            "ano":     self.txt_ano.text().strip(),
            "paginas": self.txt_paginas.text().strip(),
            "trecho":  self.txt_trecho.toPlainText().strip(),
        }


class DoutrinaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.area_selecionada = None
        self.tema_selecionado = None
        self._temas = []
        self._entradas = []
        self.init_ui()

    def init_ui(self):
        # Layout raiz sem margens — cabeçalho fixo
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
        lbl = QLabel("Doutrina")
        lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        sub = QLabel("Organize trechos doutrinários por área do direito e tema para consulta e uso em peças.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        cab_lay.addWidget(lbl)
        cab_lay.addWidget(sub)
        layout.addWidget(cab)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        layout.addWidget(sep)

        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COLORS['bg_main']};")
        cont_lay = QVBoxLayout(conteudo)
        cont_lay.setContentsMargins(32, 12, 32, 12)
        cont_lay.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── COLUNA 1: ÁREAS ──
        col1 = QWidget()
        col1.setStyleSheet(f"background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        lay1 = QVBoxLayout(col1); lay1.setContentsMargins(12, 12, 12, 12); lay1.setSpacing(8)
        lbl1 = QLabel("Área do Direito")
        lbl1.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl1.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        lay1.addWidget(lbl1); lay1.addWidget(separador_h())
        self.lista_areas = QListWidget()
        self.lista_areas.setStyleSheet(f"""
            QListWidget {{ border: none; background: transparent; font-size: 12px; }}
            QListWidget::item {{ padding: 9px 10px; border-radius: 5px; color: {COLORS['text_primary']}; }}
            QListWidget::item:selected {{ background: {COLORS['accent_light']}; color: {COLORS['accent']}; font-weight: bold; }}
            QListWidget::item:hover {{ background: {COLORS['bg_main']}; }}
        """)
        for area in AREAS_DIREITO:
            self.lista_areas.addItem(area)
        self.lista_areas.currentItemChanged.connect(self._selecionar_area)
        lay1.addWidget(self.lista_areas)
        splitter.addWidget(col1)

        # ── COLUNA 2: TEMAS ──
        col2 = QWidget()
        col2.setStyleSheet(f"background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        lay2 = QVBoxLayout(col2); lay2.setContentsMargins(12, 12, 12, 12); lay2.setSpacing(8)
        cab2 = QHBoxLayout()
        lbl2 = QLabel("Temas")
        lbl2.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl2.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        cab2.addWidget(lbl2); cab2.addStretch()
        self.btn_novo_tema = QPushButton("＋")
        self.btn_novo_tema.setFixedSize(28, 28)
        self.btn_novo_tema.setStyleSheet(f"QPushButton {{ background: {COLORS['accent']}; color: white; font-weight: bold; border-radius: 5px; border: none; font-size: 14px; }} QPushButton:hover {{ background: {COLORS['accent_hover']}; }}")
        self.btn_excluir_tema = QPushButton("🗑")
        self.btn_excluir_tema.setFixedSize(28, 28)
        self.btn_excluir_tema.setStyleSheet(f"QPushButton {{ background: {COLORS['danger_light']}; color: {COLORS['danger']}; border-radius: 5px; border: 1px solid {COLORS['danger']}; font-size: 12px; }} QPushButton:hover {{ background: {COLORS['danger']}; color: white; }}")
        self.btn_novo_tema.clicked.connect(self._novo_tema)
        self.btn_excluir_tema.clicked.connect(self._excluir_tema)
        cab2.addWidget(self.btn_novo_tema); cab2.addWidget(self.btn_excluir_tema)
        lay2.addLayout(cab2); lay2.addWidget(separador_h())
        self.lista_temas = QListWidget()
        self.lista_temas.setStyleSheet(f"""
            QListWidget {{ border: none; background: transparent; font-size: 12px; }}
            QListWidget::item {{ padding: 9px 10px; border-radius: 5px; color: {COLORS['text_primary']}; }}
            QListWidget::item:selected {{ background: {COLORS['accent_light']}; color: {COLORS['accent']}; font-weight: bold; }}
            QListWidget::item:hover {{ background: {COLORS['bg_main']}; }}
        """)
        self.lista_temas.currentItemChanged.connect(self._selecionar_tema)
        lay2.addWidget(self.lista_temas)
        splitter.addWidget(col2)

        # ── COLUNA 3: ENTRADAS ──
        col3 = QWidget()
        col3.setStyleSheet(f"background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        lay3 = QVBoxLayout(col3); lay3.setContentsMargins(12, 12, 12, 12); lay3.setSpacing(8)
        cab3 = QHBoxLayout()
        self.lbl_tema_atual = QLabel("Selecione um tema")
        self.lbl_tema_atual.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_tema_atual.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        cab3.addWidget(self.lbl_tema_atual); cab3.addStretch()
        self.btn_nova_entrada = btn_primario("＋  Adicionar")
        self.btn_nova_entrada.setEnabled(False)
        self.btn_nova_entrada.clicked.connect(self._nova_entrada)
        self.btn_excluir_entrada = btn_perigo("🗑  Excluir")
        self.btn_excluir_entrada.clicked.connect(self._excluir_entrada)
        cab3.addWidget(self.btn_nova_entrada); cab3.addWidget(self.btn_excluir_entrada)
        lay3.addLayout(cab3); lay3.addWidget(separador_h())

        self.table_entradas = QTableWidget()
        self.table_entradas.setColumnCount(4)
        self.table_entradas.setHorizontalHeaderLabels(["Autor", "Obra", "Ano", "Trecho (resumo)"])
        self.table_entradas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_entradas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_entradas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_entradas.setStyleSheet(estilo_tabela())
        self.table_entradas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_entradas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_entradas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_entradas.verticalHeader().setVisible(False)
        self.table_entradas.setAlternatingRowColors(True)
        self.table_entradas.selectionModel().selectionChanged.connect(self._exibir_trecho)
        lay3.addWidget(self.table_entradas)

        lay3.addWidget(QLabel("<b>Trecho Completo:</b>"))
        self.txt_trecho_view = QTextEdit()
        self.txt_trecho_view.setReadOnly(True)
        self.txt_trecho_view.setMaximumHeight(150)
        self.txt_trecho_view.setStyleSheet(f"""
            QTextEdit {{
                padding: 10px; border: 1.5px solid {COLORS['border']};
                border-radius: 6px; background: #FAFCFA;
                font-size: 12px; font-family: 'Times New Roman', serif;
                color: {COLORS['text_primary']}; line-height: 1.6;
            }}
        """)
        lay3.addWidget(self.txt_trecho_view)

        # Referência bibliográfica
        self.lbl_ref = QLabel("")
        self.lbl_ref.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        self.lbl_ref.setWordWrap(True)
        lay3.addWidget(self.lbl_ref)

        splitter.addWidget(col3)
        splitter.setSizes([200, 220, 560])
        cont_lay.addWidget(splitter)
        layout.addWidget(conteudo)

    def _selecionar_area(self, item):
        if not item: return
        self.area_selecionada = item.text()
        self._carregar_temas()
        self.table_entradas.setRowCount(0)
        self.txt_trecho_view.clear()
        self.lbl_tema_atual.setText("Selecione um tema")
        self.btn_nova_entrada.setEnabled(False)

    def _carregar_temas(self):
        self._temas = buscar_doutrina_temas(self.area_selecionada)
        self.lista_temas.clear()
        for t in self._temas:
            self.lista_temas.addItem(t["tema"])

    def _selecionar_tema(self, item):
        if not item: return
        idx = self.lista_temas.currentRow()
        if idx < 0 or idx >= len(self._temas): return
        self.tema_selecionado = self._temas[idx]
        self.lbl_tema_atual.setText(self.tema_selecionado["tema"])
        self.btn_nova_entrada.setEnabled(True)
        self._carregar_entradas()

    def _carregar_entradas(self):
        if not self.tema_selecionado: return
        self._entradas = buscar_doutrina_entradas(self.tema_selecionado["id"])
        self.table_entradas.setRowCount(len(self._entradas))
        for i, e in enumerate(self._entradas):
            item_autor = QTableWidgetItem(e["autor"])
            item_autor.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_autor.setForeground(QColor(COLORS["accent"]))
            self.table_entradas.setItem(i, 0, item_autor)
            self.table_entradas.setItem(i, 1, QTableWidgetItem(e["obra"]))
            self.table_entradas.setItem(i, 2, QTableWidgetItem(e.get("ano","")))
            resumo = e["trecho"][:100] + "..." if len(e["trecho"]) > 100 else e["trecho"]
            self.table_entradas.setItem(i, 3, QTableWidgetItem(resumo))
        self.txt_trecho_view.clear()
        self.lbl_ref.setText("")

    def _exibir_trecho(self):
        rows = self.table_entradas.selectionModel().selectedRows()
        if not rows: return
        e = self._entradas[rows[0].row()]
        self.txt_trecho_view.setPlainText(e["trecho"])
        # Referência ABNT
        ref_parts = [e["autor"]]
        if e.get("obra"): ref_parts.append(f"<i>{e['obra']}</i>")
        if e.get("editora"): ref_parts.append(e["editora"])
        if e.get("ano"): ref_parts.append(e["ano"])
        if e.get("paginas"): ref_parts.append(e["paginas"])
        self.lbl_ref.setText("📖 " + ". ".join(ref_parts))

    def _novo_tema(self):
        dlg = NovoTemaDoutrinaDialog(self, area_atual=self.area_selecionada)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            area, tema = dlg.obter_dados()
            salvar_doutrina_tema(area, tema)
            for i in range(self.lista_areas.count()):
                if self.lista_areas.item(i).text() == area:
                    self.lista_areas.setCurrentRow(i)
                    break
            self._carregar_temas()

    def _excluir_tema(self):
        idx = self.lista_temas.currentRow()
        if idx < 0 or idx >= len(self._temas):
            QMessageBox.information(self, "Selecione", "Selecione um tema."); return
        t = self._temas[idx]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir o tema '{t['tema']}' e todas as suas entradas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_doutrina_tema(t["id"])
            self._carregar_temas()
            self.table_entradas.setRowCount(0)
            self.txt_trecho_view.clear()
            self.btn_nova_entrada.setEnabled(False)
            self.lbl_tema_atual.setText("Selecione um tema")

    def _nova_entrada(self):
        if not self.tema_selecionado: return
        dlg = NovaEntradaDoutrinaDialog(self, tema_nome=self.tema_selecionado["tema"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.obter_dados()
            dados["tema_id"] = self.tema_selecionado["id"]
            salvar_doutrina_entrada(dados)
            self._carregar_entradas()

    def _excluir_entrada(self):
        rows = self.table_entradas.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione uma entrada."); return
        e = self._entradas[rows[0].row()]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir a entrada de {e['autor']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_doutrina_entrada(e["id"])
            self._carregar_entradas()
