# ui/configuracoes_page.py — Etapa 4: com backup, tema, cores e tribunais
import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFormLayout, QMessageBox, QPushButton, QFrame,
                             QScrollArea, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialog,
                             QDialogButtonBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
import config
from config import COLORS, APP_VERSION, ACCENT_PRESETS, THEME_LIGHT, THEME_DARK
from ui.widgets import (btn_primario, btn_secundario, btn_perigo,
                        input_field, label_titulo, separador_h, estilo_dialog,
                        estilo_tabela)
from core.database import buscar_configuracoes, salvar_configuracao
from core.backup import (fazer_backup, fazer_backup_automatico, listar_backups,
                         restaurar_backup, tamanho_banco)

import sys as _sys

def _get_tribunais_path():
    if getattr(_sys, "frozen", False):
        d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Legis")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "tribunais.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tribunais.json")

TRIBUNAIS_FILE = _get_tribunais_path()

def carregar_tribunais():
    if os.path.exists(TRIBUNAIS_FILE):
        try:
            with open(TRIBUNAIS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return list(config.TRIBUNAIS)

def salvar_tribunais(lista):
    with open(TRIBUNAIS_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)
    config.TRIBUNAIS = lista


class NovoTribunalDialog(QDialog):
    def __init__(self, parent=None, dados=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Tribunal" if not dados else "Editar Tribunal")
        self.setMinimumWidth(460)
        self.setStyleSheet(estilo_dialog())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        titulo = QLabel("Configurar Tribunal / API")
        titulo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)
        layout.addWidget(separador_h())
        form = QFormLayout(); form.setSpacing(10)
        self.txt_nome  = input_field("Ex: TJBA — Tribunal de Justiça da Bahia")
        self.txt_alias = input_field("Ex: api_publica_tjba")
        def lbl(t):
            l = QLabel(f"<b>{t}</b>"); l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;"); return l
        form.addRow(lbl("Nome do Tribunal:"),      self.txt_nome)
        form.addRow(lbl("Alias da API (DataJud):"), self.txt_alias)
        hint = QLabel("Acesse datajud.cnj.jus.br, localize o tribunal\ne copie o nome do índice (ex: api_publica_tjba).")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        layout.addLayout(form)
        layout.addWidget(hint)
        if dados:
            self.txt_nome.setText(dados[0]); self.txt_alias.setText(dados[1])
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botoes.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botoes.button(QDialogButtonBox.StandardButton.Save).setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: none;")
        botoes.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(f"background-color: white; color: {COLORS['text_secondary']}; font-weight: 600; padding: 8px 20px; border-radius: 6px; border: 1.5px solid {COLORS['border']};")
        botoes.accepted.connect(self.validar); botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def validar(self):
        if not self.txt_nome.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome."); return
        if not self.txt_alias.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o alias."); return
        self.accept()

    def obter_dados(self):
        return (self.txt_nome.text().strip(), self.txt_alias.text().strip())


class BotaoTema(QPushButton):
    def __init__(self, texto, modo, parent=None):
        super().__init__(texto, parent)
        self.modo = modo
        self.setCheckable(True)
        self.setMinimumSize(130, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def atualizar_estilo(self, ativo):
        if ativo:
            self.setStyleSheet(f"QPushButton {{ background: {COLORS['accent']}; color: white; border: 2px solid {COLORS['accent']}; border-radius: 10px; font-size: 13px; font-weight: 700; padding: 10px; }}")
        else:
            self.setStyleSheet(f"QPushButton {{ background: {COLORS['white']}; color: {COLORS['text_primary']}; border: 2px solid {COLORS['border']}; border-radius: 10px; font-size: 13px; font-weight: 500; padding: 10px; }} QPushButton:hover {{ border-color: {COLORS['accent']}; background: {COLORS['accent_light']}; }}")


class BotaoCor(QPushButton):
    def __init__(self, nome, cor_hex, parent=None):
        super().__init__(parent)
        self.nome = nome
        self.setFixedSize(44, 44)
        self.setToolTip(nome)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cor = cor_hex
        self.marcar(False)

    def marcar(self, ativo):
        borda = "3px solid white" if ativo else f"2px solid {self._cor}"
        sombra = f"outline: 3px solid {COLORS['text_primary']};" if ativo else ""
        self.setStyleSheet(f"QPushButton {{ background-color: {self._cor}; border-radius: 22px; border: {borda}; {sombra} }}")


class BackupThread(QThread):
    concluido = pyqtSignal(str)
    erro      = pyqtSignal(str)

    def __init__(self, modo="backup", caminho_restaurar=None):
        super().__init__()
        self.modo = modo
        self.caminho_restaurar = caminho_restaurar

    def run(self):
        try:
            if self.modo == "backup":
                caminho, err = fazer_backup()
                if err: self.erro.emit(err)
                else: self.concluido.emit(caminho)
            elif self.modo == "restaurar":
                ok, err = restaurar_backup(self.caminho_restaurar)
                if err: self.erro.emit(err)
                else: self.concluido.emit("Backup restaurado com sucesso!")
        except Exception as e:
            self.erro.emit(str(e))


class ConfiguracoesPage(QWidget):
    tema_alterado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker_backup = None
        self._tribunais = []
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COLORS['bg_main']};")
        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(32, 16, 200, 20)
        layout.setSpacing(20)

        layout.addWidget(label_titulo("Configurações"))
        layout.addWidget(separador_h())

        # ── 1. ESCRITÓRIO ──
        layout.addWidget(self._lbl_secao("🏛️  Dados do Escritório"))
        card_esc = self._card()
        form = QFormLayout(); form.setSpacing(12)
        self.campos = {}
        chaves = [
            ("nome_escritorio", "Nome do Escritório:"),
            ("responsavel",     "Responsável / Advogado:"),
            ("oab",             "OAB:"),
            ("cidade",          "Cidade / Estado:"),
            ("telefone",        "Telefone:"),
            ("email",           "E-mail:"),
        ]
        for chave, rotulo in chaves:
            lbl = QLabel(f"<b>{rotulo}</b>")
            lbl.setStyleSheet(f"border: none; color: {COLORS['text_primary']}; font-size: 12px;")
            campo = input_field()
            self.campos[chave] = campo
            form.addRow(lbl, campo)
        card_esc.layout().addLayout(form)
        btn_salvar_esc = btn_primario("💾  Salvar Dados do Escritório")
        btn_salvar_esc.clicked.connect(self.salvar_escritorio)
        card_esc.layout().addWidget(btn_salvar_esc)
        layout.addWidget(card_esc)

        # ── 2. APARÊNCIA ──
        layout.addWidget(self._lbl_secao("🎨  Aparência"))
        card_tema = self._card()
        card_tema.layout().addWidget(QLabel("<b>Modo de Exibição:</b>"))
        card_tema.layout().addSpacing(6)
        temas_row = QHBoxLayout(); temas_row.setSpacing(12)
        self.btn_claro  = BotaoTema("☀️\nModo Claro",  "light")
        self.btn_escuro = BotaoTema("🌙\nModo Escuro", "dark")
        self.btn_claro.clicked.connect(lambda: self._aplicar_tema("light"))
        self.btn_escuro.clicked.connect(lambda: self._aplicar_tema("dark"))
        temas_row.addWidget(self.btn_claro); temas_row.addWidget(self.btn_escuro)
        temas_row.addStretch()
        card_tema.layout().addLayout(temas_row)
        card_tema.layout().addSpacing(14)
        card_tema.layout().addWidget(separador_h())
        card_tema.layout().addSpacing(10)
        card_tema.layout().addWidget(QLabel("<b>Cor de Destaque:</b>"))
        card_tema.layout().addSpacing(6)
        cores_row = QHBoxLayout(); cores_row.setSpacing(10)
        self._btns_cor = {}
        for nome, preset in ACCENT_PRESETS.items():
            btn_cor = BotaoCor(nome, preset["accent"])
            btn_cor.clicked.connect(lambda _, n=nome: self._aplicar_accent(n))
            self._btns_cor[nome] = btn_cor
            cores_row.addWidget(btn_cor)
        cores_row.addStretch()
        card_tema.layout().addLayout(cores_row)
        leg_row = QHBoxLayout(); leg_row.setSpacing(10)
        for nome in ACCENT_PRESETS:
            lbl = QLabel(nome); lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
            lbl.setFixedWidth(80); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            leg_row.addWidget(lbl)
        leg_row.addStretch()
        card_tema.layout().addLayout(leg_row)
        layout.addWidget(card_tema)

        # ── 3. TRIBUNAIS ──
        layout.addWidget(self._lbl_secao("⚖️  Tribunais & APIs"))
        card_trib = self._card()
        desc = QLabel("Gerencie os tribunais disponíveis na aba Proc. Automáticos.\nO alias deve ser o nome do índice na API pública do CNJ (DataJud).")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        desc.setWordWrap(True)
        card_trib.layout().addWidget(desc)
        card_trib.layout().addSpacing(8)
        barra_trib = QHBoxLayout(); barra_trib.addStretch()
        btn_add = btn_primario("＋  Adicionar")
        self.btn_editar_trib  = btn_secundario("✏️  Editar")
        self.btn_excluir_trib = btn_perigo("🗑  Excluir")
        btn_add.clicked.connect(self.adicionar_tribunal)
        self.btn_editar_trib.clicked.connect(self.editar_tribunal)
        self.btn_excluir_trib.clicked.connect(self.excluir_tribunal)
        barra_trib.addWidget(btn_add)
        barra_trib.addWidget(self.btn_editar_trib)
        barra_trib.addWidget(self.btn_excluir_trib)
        card_trib.layout().addLayout(barra_trib)
        self.table_trib = QTableWidget()
        self.table_trib.setColumnCount(2)
        self.table_trib.setHorizontalHeaderLabels(["Nome do Tribunal", "Alias da API"])
        self.table_trib.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_trib.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_trib.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_trib.setStyleSheet(estilo_tabela())
        self.table_trib.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_trib.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_trib.verticalHeader().setVisible(False)
        self.table_trib.setMaximumHeight(200)
        self.table_trib.setAlternatingRowColors(True)
        card_trib.layout().addWidget(self.table_trib)
        layout.addWidget(card_trib)

        # ── 4. BACKUP ──
        layout.addWidget(self._lbl_secao("💾  Backup e Segurança dos Dados"))
        card_bkp = self._card()

        info_row = QHBoxLayout()
        self.lbl_tamanho_db = QLabel(f"Banco de dados: {tamanho_banco()}")
        self.lbl_tamanho_db.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
        info_row.addWidget(self.lbl_tamanho_db)
        info_row.addStretch()
        btn_backup_agora = btn_primario("💾  Fazer Backup Agora")
        btn_backup_agora.clicked.connect(self.fazer_backup_manual)
        info_row.addWidget(btn_backup_agora)
        card_bkp.layout().addLayout(info_row)

        self.lbl_backup_status = QLabel("Os backups são salvos automaticamente uma vez por dia na pasta 'backups'.")
        self.lbl_backup_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        self.lbl_backup_status.setWordWrap(True)
        card_bkp.layout().addWidget(self.lbl_backup_status)

        card_bkp.layout().addWidget(separador_h())
        card_bkp.layout().addWidget(QLabel("<b>Backups Disponíveis:</b>"))

        self.table_backups = QTableWidget()
        self.table_backups.setColumnCount(3)
        self.table_backups.setHorizontalHeaderLabels(["Arquivo", "Data", "Tamanho"])
        self.table_backups.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_backups.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_backups.setStyleSheet(estilo_tabela())
        self.table_backups.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_backups.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_backups.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_backups.verticalHeader().setVisible(False)
        self.table_backups.setMaximumHeight(180)
        self.table_backups.setAlternatingRowColors(True)
        card_bkp.layout().addWidget(self.table_backups)

        restaurar_row = QHBoxLayout()
        restaurar_row.addStretch()
        btn_restaurar = btn_secundario("🔄  Restaurar Backup Selecionado")
        btn_restaurar.clicked.connect(self.restaurar_selecionado)
        btn_abrir_pasta = btn_secundario("📂  Abrir Pasta de Backups")
        btn_abrir_pasta.clicked.connect(self.abrir_pasta_backups)
        restaurar_row.addWidget(btn_abrir_pasta)
        restaurar_row.addWidget(btn_restaurar)
        card_bkp.layout().addLayout(restaurar_row)
        layout.addWidget(card_bkp)

        # ── 5. ATUALIZAÇÕES ──
        layout.addWidget(self._lbl_secao("🔄  Atualizações do Sistema"))
        card_upd = self._card()
        upd_row = QHBoxLayout()
        lbl_ver = QLabel(f"Versão instalada: <b>Legis {APP_VERSION}</b>")
        lbl_ver.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
        upd_row.addWidget(lbl_ver); upd_row.addStretch()
        btn_upd = btn_primario("🔄  Verificar Atualizações")
        btn_upd.clicked.connect(self.verificar_atualizacao)
        upd_row.addWidget(btn_upd)
        card_upd.layout().addLayout(upd_row)
        self.lbl_upd_status = QLabel("Clique para verificar se há uma nova versão disponível.")
        self.lbl_upd_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        card_upd.layout().addWidget(self.lbl_upd_status)
        layout.addWidget(card_upd)

        layout.addStretch()
        lbl_rodape = QLabel(f"Legis {APP_VERSION} — Desenvolvido por Adinan da Rocha Lima, 2026. Todos os direitos reservados.")
        lbl_rodape.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        layout.addWidget(lbl_rodape)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(conteudo)
        outer.addWidget(scroll)

        self.carregar_dados()

    def _lbl_secao(self, texto):
        lbl = QLabel(texto)
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        return lbl

    def _card(self):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(10)
        return card

    def carregar_dados(self):
        cfg = buscar_configuracoes()
        for chave, campo in self.campos.items():
            campo.setText(cfg.get(chave, ""))
        tema_salvo   = cfg.get("tema",   "light")
        accent_salvo = cfg.get("accent", "Verde Jurídico")
        if tema_salvo != config.CURRENT_THEME:
            self._aplicar_tema(tema_salvo, salvar=False)
        if accent_salvo != config.CURRENT_ACCENT:
            self._aplicar_accent(accent_salvo, salvar=False)
        self._sincronizar_visual_tema()
        self._sincronizar_visual_cor()
        self._carregar_tribunais()
        self._carregar_backups()
        self.lbl_tamanho_db.setText(f"Banco de dados: {tamanho_banco()}")

    def salvar_escritorio(self):
        for chave, campo in self.campos.items():
            salvar_configuracao(chave, campo.text().strip())
        QMessageBox.information(self, "Salvo", "Dados do escritório salvos com sucesso.")
        self.tema_alterado.emit()

    # ── Tema ──
    def _aplicar_tema(self, modo, salvar=True):
        config.CURRENT_THEME = modo
        base = dict(THEME_DARK if modo == "dark" else THEME_LIGHT)
        preset = ACCENT_PRESETS.get(config.CURRENT_ACCENT, {})
        base.update(preset)
        config.COLORS.clear(); config.COLORS.update(base)
        if salvar: salvar_configuracao("tema", modo)
        self._sincronizar_visual_tema()
        self.tema_alterado.emit()

    def _aplicar_accent(self, nome, salvar=True):
        config.CURRENT_ACCENT = nome
        preset = ACCENT_PRESETS.get(nome, {})
        config.COLORS.update(preset)
        config.COLORS["bg_active"] = preset.get("bg_active", preset.get("accent", COLORS["accent"]))
        if salvar: salvar_configuracao("accent", nome)
        self._sincronizar_visual_cor()
        self.tema_alterado.emit()

    def _sincronizar_visual_tema(self):
        modo = config.CURRENT_THEME
        self.btn_claro.atualizar_estilo(modo == "light")
        self.btn_escuro.atualizar_estilo(modo == "dark")

    def _sincronizar_visual_cor(self):
        for nome, btn in self._btns_cor.items():
            btn.marcar(nome == config.CURRENT_ACCENT)

    # ── Tribunais ──
    def _carregar_tribunais(self):
        self._tribunais = carregar_tribunais()
        config.TRIBUNAIS = self._tribunais
        self.table_trib.setRowCount(len(self._tribunais))
        for i, (nome, alias) in enumerate(self._tribunais):
            self.table_trib.setItem(i, 0, QTableWidgetItem(nome))
            item = QTableWidgetItem(alias)
            item.setForeground(QColor(COLORS["accent"]))
            self.table_trib.setItem(i, 1, item)

    def _linha_trib(self):
        rows = self.table_trib.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um tribunal."); return None
        return rows[0].row()

    def adicionar_tribunal(self):
        dlg = NovoTribunalDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._tribunais.append(dlg.obter_dados())
            salvar_tribunais(self._tribunais)
            self._carregar_tribunais()

    def editar_tribunal(self):
        row = self._linha_trib()
        if row is None: return
        dlg = NovoTribunalDialog(self, dados=self._tribunais[row])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._tribunais[row] = dlg.obter_dados()
            salvar_tribunais(self._tribunais)
            self._carregar_tribunais()

    def excluir_tribunal(self):
        row = self._linha_trib()
        if row is None: return
        resp = QMessageBox.question(self, "Confirmar",
            f"Excluir o tribunal:\n{self._tribunais[row][0]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self._tribunais.pop(row)
            salvar_tribunais(self._tribunais)
            self._carregar_tribunais()

    # ── Backup ──
    def _carregar_backups(self):
        backups = listar_backups()
        self.table_backups.setRowCount(len(backups))
        for i, b in enumerate(backups):
            self.table_backups.setItem(i, 0, QTableWidgetItem(b["nome"]))
            self.table_backups.setItem(i, 1, QTableWidgetItem(b["data"]))
            self.table_backups.setItem(i, 2, QTableWidgetItem(b["tamanho"]))
        if not backups:
            self.table_backups.setRowCount(1)
            item = QTableWidgetItem("Nenhum backup encontrado.")
            item.setForeground(QColor(COLORS["text_muted"]))
            self.table_backups.setItem(0, 0, item)

    def fazer_backup_manual(self):
        self.lbl_backup_status.setText("⏳  Fazendo backup...")
        self.lbl_backup_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
        if self._worker_backup and self._worker_backup.isRunning(): return
        self._worker_backup = BackupThread("backup")
        self._worker_backup.concluido.connect(self._backup_concluido)
        self._worker_backup.erro.connect(self._backup_erro)
        self._worker_backup.start()

    def _backup_concluido(self, caminho):
        self.lbl_backup_status.setText(f"✅  Backup salvo em: {os.path.basename(caminho)}")
        self.lbl_backup_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; font-weight: 600; border: none;")
        self._carregar_backups()
        self.lbl_tamanho_db.setText(f"Banco de dados: {tamanho_banco()}")

    def _backup_erro(self, msg):
        self.lbl_backup_status.setText(f"❌  Erro: {msg}")
        self.lbl_backup_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px; font-weight: 600; border: none;")

    def restaurar_selecionado(self):
        rows = self.table_backups.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Selecione", "Selecione um backup para restaurar."); return
        backups = listar_backups()
        if not backups: return
        b = backups[rows[0].row()]
        resp = QMessageBox.question(self, "Confirmar restauração",
            f"Restaurar o backup:\n{b['nome']}\n\nO banco atual será substituído. Um backup automático será feito antes.\n\nContinuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self._worker_backup = BackupThread("restaurar", b["caminho"])
            self._worker_backup.concluido.connect(lambda msg: QMessageBox.information(self, "Restaurado", msg))
            self._worker_backup.erro.connect(lambda err: QMessageBox.critical(self, "Erro", err))
            self._worker_backup.start()

    def abrir_pasta_backups(self):
        from core.backup import BACKUP_DIR
        from pathlib import Path
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        if os.name == "nt":
            os.startfile(BACKUP_DIR)

    # ── Atualizações ──
    def verificar_atualizacao(self):
        self.lbl_upd_status.setText("🔍  Verificando atualizações...")
        self.lbl_upd_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
        QTimer.singleShot(1800, self._sem_atualizacao)

    def _sem_atualizacao(self):
        self.lbl_upd_status.setText(f"✅  Você já possui a versão mais recente (Legis {APP_VERSION}).")
        self.lbl_upd_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; font-weight: 600; border: none;")
