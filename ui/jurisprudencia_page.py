# ui/jurisprudencia_page.py — layout corrigido definitivamente
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialog, QFormLayout,
                             QComboBox, QTextEdit, QMessageBox, QDialogButtonBox,
                             QSplitter, QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QDesktopServices
from PyQt6.QtCore import QUrl
from config import COLORS, AREAS_DIREITO
from ui.widgets import (btn_primario, btn_perigo, btn_secundario, input_field,
                        separador_h, estilo_tabela, estilo_dialog)
from core.database import (buscar_temas, salvar_tema, excluir_tema,
                           buscar_entradas, salvar_entrada, excluir_entrada)


class NovoTemaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Tema")
        self.setMinimumWidth(420)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        titulo = QLabel("Criar Novo Tema")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        layout.addWidget(separador_h())
        form = QFormLayout(); form.setSpacing(10)
        self.cb_area = QComboBox()
        self.cb_area.addItems(AREAS_DIREITO)
        self.cb_area.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.txt_tema = input_field("Ex: Homicídio Doloso, Usucapião, Horas Extras")
        def lbl(t):
            l = QLabel(f"<b>{t}</b>"); l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;"); return l
        form.addRow(lbl("Área:"), self.cb_area)
        form.addRow(lbl("Tema:"), self.txt_tema)
        layout.addLayout(form)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Criar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar); botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_tema.text().strip():
            QMessageBox.warning(self, "Obrigatório", "Informe o tema."); return
        self.accept()

    def obter_dados(self):
        return self.cb_area.currentText(), self.txt_tema.text().strip()


class NovaEntradaDialog(QDialog):
    def __init__(self, parent=None, tema_nome=""):
        super().__init__(parent)
        self.setWindowTitle(f"Adicionar Jurisprudência")
        self.setMinimumSize(580, 480)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        titulo = QLabel("Nova Entrada de Jurisprudência")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        if tema_nome:
            sub = QLabel(f"Tema: {tema_nome}")
            sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            layout.addWidget(sub)
        layout.addWidget(separador_h())
        form = QFormLayout(); form.setSpacing(10)
        self.txt_tribunal  = input_field("Ex: STJ, STF, TJSP")
        self.txt_acordao   = input_field("Ex: HC 123456/SP")
        self.txt_data      = input_field("AAAA-MM-DD")
        self.txt_link      = input_field("https://...")
        def lbl(t):
            l = QLabel(f"<b>{t}</b>"); l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;"); return l
        form.addRow(lbl("Tribunal:"),        self.txt_tribunal)
        form.addRow(lbl("Nº Acórdão:"),      self.txt_acordao)
        form.addRow(lbl("Data:"),            self.txt_data)
        form.addRow(lbl("Link Oficial:"),    self.txt_link)
        layout.addLayout(form)
        layout.addWidget(lbl("Ementa:"))
        self.txt_ementa = QTextEdit()
        self.txt_ementa.setPlaceholderText("Cole ou digite a ementa do acórdão aqui...")
        self.txt_ementa.setStyleSheet(f"padding: 10px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        layout.addWidget(self.txt_ementa)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar); botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_tribunal.text().strip():
            QMessageBox.warning(self, "Obrigatório", "Informe o tribunal."); return
        if not self.txt_ementa.toPlainText().strip():
            QMessageBox.warning(self, "Obrigatório", "Informe a ementa."); return
        self.accept()

    def obter_dados(self):
        return {
            "tribunal":        self.txt_tribunal.text().strip().upper(),
            "numero_acordao":  self.txt_acordao.text().strip(),
            "data_julgamento": self.txt_data.text().strip(),
            "link":            self.txt_link.text().strip(),
            "ementa":          self.txt_ementa.toPlainText().strip(),
        }


def _lista_style():
    return f"""
        QListWidget {{ border: none; background: transparent; font-size: 12px; outline: none; }}
        QListWidget::item {{ padding: 8px 10px; border-radius: 5px; color: {COLORS['text_primary']}; }}
        QListWidget::item:selected {{ background: {COLORS['accent_light']}; color: {COLORS['accent']}; font-weight: bold; }}
        QListWidget::item:hover {{ background: {COLORS['bg_main']}; }}
    """


class JurisprudenciaPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.area_selecionada = None
        self.tema_selecionado = None
        self._temas    = []
        self._entradas = []
        self.init_ui()

    def init_ui(self):
        # Layout raiz sem margens — o cabeçalho fica num widget separado de altura fixa
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── CABEÇALHO FIXO ──────────────────────────────────
        cab = QWidget()
        cab.setFixedHeight(72)
        cab.setStyleSheet(f"background: {COLORS['bg_main']};")
        cab_lay = QVBoxLayout(cab)
        cab_lay.setContentsMargins(32, 10, 32, 6)
        cab_lay.setSpacing(2)
        lbl = QLabel("Jurisprudência")
        lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        sub = QLabel("Organize acórdãos por área do direito e tema para consulta rápida.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        cab_lay.addWidget(lbl)
        cab_lay.addWidget(sub)
        layout.addWidget(cab)

        # Linha separadora
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        layout.addWidget(sep)

        # ── CONTEÚDO (splitter 3 colunas) ───────────────────
        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COLORS['bg_main']};")
        cont_lay = QVBoxLayout(conteudo)
        cont_lay.setContentsMargins(32, 12, 32, 12)
        cont_lay.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Col 1 — Áreas
        col1 = QWidget()
        col1.setStyleSheet(f"background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        lay1 = QVBoxLayout(col1); lay1.setContentsMargins(12, 10, 12, 10); lay1.setSpacing(6)
        lbl1 = QLabel("Área do Direito")
        lbl1.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl1.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        lay1.addWidget(lbl1); lay1.addWidget(separador_h())
        self.lista_areas = QListWidget()
        self.lista_areas.setStyleSheet(_lista_style())
        for area in AREAS_DIREITO:
            self.lista_areas.addItem(area)
        self.lista_areas.currentItemChanged.connect(self.selecionar_area)
        lay1.addWidget(self.lista_areas)
        splitter.addWidget(col1)

        # Col 2 — Temas
        col2 = QWidget()
        col2.setStyleSheet(f"background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        lay2 = QVBoxLayout(col2); lay2.setContentsMargins(12, 10, 12, 10); lay2.setSpacing(6)
        cab2 = QHBoxLayout()
        lbl2 = QLabel("Temas")
        lbl2.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl2.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        cab2.addWidget(lbl2); cab2.addStretch()
        self.btn_novo_tema = QPushButton("＋")
        self.btn_excluir_tema = QPushButton("🗑")
        self.btn_novo_tema.setFixedSize(28, 28)
        self.btn_excluir_tema.setFixedSize(28, 28)
        self.btn_novo_tema.setStyleSheet(f"QPushButton {{ background:{COLORS['accent']}; color:white; font-weight:bold; border-radius:5px; border:none; font-size:14px; }} QPushButton:hover {{ background:{COLORS['accent_hover']}; }}")
        self.btn_excluir_tema.setStyleSheet(f"QPushButton {{ background:{COLORS['danger_light']}; color:{COLORS['danger']}; border-radius:5px; border:1px solid {COLORS['danger']}; }} QPushButton:hover {{ background:{COLORS['danger']}; color:white; }}")
        self.btn_novo_tema.clicked.connect(self.novo_tema)
        self.btn_excluir_tema.clicked.connect(self.excluir_tema_selecionado)
        cab2.addWidget(self.btn_novo_tema); cab2.addWidget(self.btn_excluir_tema)
        lay2.addLayout(cab2); lay2.addWidget(separador_h())
        self.lista_temas = QListWidget()
        self.lista_temas.setStyleSheet(_lista_style())
        self.lista_temas.currentItemChanged.connect(self.selecionar_tema)
        lay2.addWidget(self.lista_temas)
        splitter.addWidget(col2)

        # Col 3 — Ementas
        col3 = QWidget()
        col3.setStyleSheet(f"background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 8px;")
        lay3 = QVBoxLayout(col3); lay3.setContentsMargins(12, 10, 12, 10); lay3.setSpacing(8)
        cab3 = QHBoxLayout()
        self.lbl_tema_atual = QLabel("Selecione um tema")
        self.lbl_tema_atual.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_tema_atual.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        cab3.addWidget(self.lbl_tema_atual); cab3.addStretch()
        self.btn_nova_entrada = btn_primario("＋  Adicionar")
        self.btn_nova_entrada.setEnabled(False)
        self.btn_nova_entrada.clicked.connect(self.nova_entrada)
        self.btn_excluir_entrada = btn_perigo("🗑  Excluir")
        self.btn_excluir_entrada.clicked.connect(self.excluir_entrada_selecionada)
        cab3.addWidget(self.btn_nova_entrada); cab3.addWidget(self.btn_excluir_entrada)
        lay3.addLayout(cab3); lay3.addWidget(separador_h())

        self.table_entradas = QTableWidget()
        self.table_entradas.setColumnCount(4)
        self.table_entradas.setHorizontalHeaderLabels(["Tribunal", "Acórdão", "Data", "Ementa (resumo)"])
        self.table_entradas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_entradas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_entradas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_entradas.setStyleSheet(estilo_tabela())
        self.table_entradas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_entradas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_entradas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_entradas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_entradas.verticalHeader().setVisible(False)
        self.table_entradas.setAlternatingRowColors(True)
        self.table_entradas.selectionModel().selectionChanged.connect(self.exibir_ementa)
        lay3.addWidget(self.table_entradas)

        lay3.addWidget(QLabel("<b>Ementa Completa:</b>"))
        self.txt_ementa_view = QTextEdit()
        self.txt_ementa_view.setReadOnly(True)
        self.txt_ementa_view.setMaximumHeight(130)
        self.txt_ementa_view.setStyleSheet(f"padding: 10px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: #FAFCFA; font-size: 12px;")
        lay3.addWidget(self.txt_ementa_view)

        self.btn_abrir_link = btn_secundario("🔗  Abrir no Tribunal")
        self.btn_abrir_link.clicked.connect(self.abrir_link)
        self.btn_abrir_link.setEnabled(False)
        lay3.addWidget(self.btn_abrir_link)
        splitter.addWidget(col3)
        splitter.setSizes([200, 220, 560])

        cont_lay.addWidget(splitter)
        layout.addWidget(conteudo)

    def selecionar_area(self, item):
        if not item: return
        self.area_selecionada = item.text()
        self._carregar_temas()
        self.table_entradas.setRowCount(0)
        self.txt_ementa_view.clear()
        self.lbl_tema_atual.setText("Selecione um tema")
        self.btn_nova_entrada.setEnabled(False)

    def _carregar_temas(self):
        self._temas = buscar_temas(self.area_selecionada)
        self.lista_temas.clear()
        for t in self._temas:
            self.lista_temas.addItem(t["tema"])

    def selecionar_tema(self, item):
        if not item: return
        idx = self.lista_temas.currentRow()
        if idx < 0 or idx >= len(self._temas): return
        self.tema_selecionado = self._temas[idx]
        self.lbl_tema_atual.setText(self.tema_selecionado["tema"])
        self.btn_nova_entrada.setEnabled(True)
        self._carregar_entradas()

    def _carregar_entradas(self):
        if not self.tema_selecionado: return
        self._entradas = buscar_entradas(self.tema_selecionado["id"])
        self.table_entradas.setRowCount(len(self._entradas))
        for i, e in enumerate(self._entradas):
            item_trib = QTableWidgetItem(e["tribunal"])
            item_trib.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            item_trib.setForeground(QColor(COLORS["accent"]))
            self.table_entradas.setItem(i, 0, item_trib)
            self.table_entradas.setItem(i, 1, QTableWidgetItem(e["numero_acordao"]))
            data_br = "/".join(e["data_julgamento"].split("-")[::-1]) if "-" in e.get("data_julgamento","") else e.get("data_julgamento","")
            self.table_entradas.setItem(i, 2, QTableWidgetItem(data_br))
            resumo = e["ementa"][:120] + "..." if len(e["ementa"]) > 120 else e["ementa"]
            self.table_entradas.setItem(i, 3, QTableWidgetItem(resumo))
        self.txt_ementa_view.clear()
        self.btn_abrir_link.setEnabled(False)

    def exibir_ementa(self):
        rows = self.table_entradas.selectionModel().selectedRows()
        if not rows: return
        e = self._entradas[rows[0].row()]
        self.txt_ementa_view.setPlainText(e["ementa"])
        self.btn_abrir_link.setEnabled(bool(e.get("link","").strip()))

    def abrir_link(self):
        rows = self.table_entradas.selectionModel().selectedRows()
        if not rows: return
        link = self._entradas[rows[0].row()].get("link","").strip()
        if link: QDesktopServices.openUrl(QUrl(link))

    def novo_tema(self):
        dlg = NovoTemaDialog(self)
        if self.area_selecionada:
            idx = dlg.cb_area.findText(self.area_selecionada)
            if idx >= 0: dlg.cb_area.setCurrentIndex(idx)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            area, tema = dlg.obter_dados()
            salvar_tema(area, tema)
            for i in range(self.lista_areas.count()):
                if self.lista_areas.item(i).text() == area:
                    self.lista_areas.setCurrentRow(i); break
            self._carregar_temas()

    def excluir_tema_selecionado(self):
        idx = self.lista_temas.currentRow()
        if idx < 0 or idx >= len(self._temas):
            QMessageBox.information(self, "Selecione", "Selecione um tema."); return
        t = self._temas[idx]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir '{t['tema']}' e todas as jurisprudências?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_tema(t["id"])
            self._carregar_temas()
            self.table_entradas.setRowCount(0)
            self.txt_ementa_view.clear()
            self.btn_nova_entrada.setEnabled(False)
            self.lbl_tema_atual.setText("Selecione um tema")

    def nova_entrada(self):
        if not self.tema_selecionado: return
        dlg = NovaEntradaDialog(self, tema_nome=self.tema_selecionado["tema"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dados = dlg.obter_dados()
            dados["tema_id"] = self.tema_selecionado["id"]
            salvar_entrada(dados)
            self._carregar_entradas()
            # Indexar no RAG em background
            try:
                from core.ai.runner import rag_indexar_juris_async, analisar_tese_async
                novas = buscar_entradas(self.tema_selecionado["id"])
                if novas:
                    nova = novas[0]
                    rag_indexar_juris_async(nova["id"], nova.get("tribunal",""),
                        nova.get("numero_acordao",""), nova.get("ementa",""),
                        self.tema_selecionado["tema"])
                    # Etapa 5: análise inteligente (resumo, área, palavras-chave)
                    texto_tese = f"{nova.get('tribunal','')} {nova.get('numero_acordao','')}. {nova.get('ementa','')}"
                    analisar_tese_async("jurisprudencia", nova["id"], texto_tese)
            except Exception:
                pass

    def excluir_entrada_selecionada(self):
        rows = self.table_entradas.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione uma entrada."); return
        e = self._entradas[rows[0].row()]
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir {e['numero_acordao']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            excluir_entrada(e["id"])
            self._carregar_entradas()
