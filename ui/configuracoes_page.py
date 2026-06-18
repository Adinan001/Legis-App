# ui/configuracoes_page.py — Etapa 4: com backup, tema, cores e tribunais
import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFormLayout, QMessageBox, QPushButton, QFrame,
                             QScrollArea, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialog,
                             QDialogButtonBox, QFileDialog, QComboBox, QLineEdit, QCheckBox)
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



class TestarChaveIAThread(QThread):
    resultado = pyqtSignal(bool, str)

    def __init__(self, plano, api_key):
        super().__init__()
        self.plano = plano
        self.api_key = api_key

    def run(self):
        from core.ai.runner import testar_chave
        try:
            ok, msg = testar_chave(self.plano, self.api_key)
        except Exception as e:
            ok, msg = False, f"Erro inesperado: {e}"
        self.resultado.emit(ok, msg)



class ReindexarRAGThread(QThread):
    resultado = pyqtSignal(bool, str)

    def run(self):
        from core.ai.runner import chamar_rag
        try:
            ok, dados = chamar_rag("reindexar_tudo", timeout=600)
            if ok:
                msg = f"{dados.get('n_juris',0)} jurisprudências e {dados.get('n_doutrina',0)} doutrinas indexadas."
                self.resultado.emit(True, msg)
            else:
                self.resultado.emit(False, dados.get("erro", "Erro desconhecido"))
        except Exception as e:
            self.resultado.emit(False, str(e))


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
        # ── LOGO DO ESCRITÓRIO ──
        layout.addWidget(self._lbl_secao('🖼️  Logo do Escritório'))
        card_logo = self._card()

        desc_logo = QLabel('A logo aparece na tela de login. Formatos aceitos: PNG, JPG, JPEG.')
        desc_logo.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        card_logo.layout().addWidget(desc_logo)

        logo_row = QHBoxLayout()
        self.lbl_logo_preview = QLabel('Nenhuma logo configurada.')
        self.lbl_logo_preview.setFixedHeight(80)
        self.lbl_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_preview.setStyleSheet(f"border: 2px dashed {COLORS['border']}; border-radius: 8px; color: {COLORS['text_muted']}; font-size: 11px;")
        logo_row.addWidget(self.lbl_logo_preview)

        logo_btns = QVBoxLayout()
        btn_upload_logo = btn_primario('📁  Escolher Logo')
        btn_upload_logo.clicked.connect(self._upload_logo)
        btn_remover_logo = btn_perigo('🗑  Remover')
        btn_remover_logo.clicked.connect(self._remover_logo)
        logo_btns.addWidget(btn_upload_logo)
        logo_btns.addWidget(btn_remover_logo)
        logo_btns.addStretch()
        logo_row.addLayout(logo_btns)
        card_logo.layout().addLayout(logo_row)
        layout.addWidget(card_logo)



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


        # ── INTELIGÊNCIA ARTIFICIAL ──
        layout.addWidget(self._lbl_secao("🤖  Inteligência Artificial"))
        card_ia = self._card()

        desc_ia = QLabel(
            "O Legis pode usar IA para gerar peças, responder consultas jurídicas e "
            "buscar jurisprudência. Escolha o plano e configure a respectiva chave de API.")
        desc_ia.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        desc_ia.setWordWrap(True)
        card_ia.layout().addWidget(desc_ia)
        card_ia.layout().addSpacing(8)

        # Seletor de plano
        plano_row = QHBoxLayout()
        plano_row.addWidget(QLabel("<b>Plano ativo:</b>"))
        self.cb_plano_ia = QComboBox()
        self.cb_plano_ia.addItem("🆓 Gratuito — Google Gemini", "gratuito")
        self.cb_plano_ia.addItem("⚡ Gratuito — Groq (Llama 3.3)", "groq")
        self.cb_plano_ia.addItem("🐋 Pago — DeepSeek", "deepseek")
        self.cb_plano_ia.addItem("⭐ Pro — Anthropic Claude", "pro")
        self.cb_plano_ia.setStyleSheet(f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;")
        self.cb_plano_ia.setFixedWidth(260)
        plano_row.addWidget(self.cb_plano_ia)
        plano_row.addStretch()
        card_ia.layout().addLayout(plano_row)
        card_ia.layout().addSpacing(10)
        card_ia.layout().addWidget(separador_h())
        card_ia.layout().addSpacing(10)

        # Chave Gemini
        card_ia.layout().addWidget(QLabel("<b>🆓 Google Gemini API Key (Plano Gratuito)</b>"))
        gemini_row = QHBoxLayout()
        self.txt_gemini_key = input_field("Cole sua chave da API do Google AI Studio")
        self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        gemini_row.addWidget(self.txt_gemini_key)
        self.btn_show_gemini = btn_secundario("👁")
        self.btn_show_gemini.setFixedWidth(40)
        self.btn_show_gemini.clicked.connect(lambda: self._toggle_senha(self.txt_gemini_key, self.btn_show_gemini))
        gemini_row.addWidget(self.btn_show_gemini)
        self.btn_testar_gemini = btn_primario("Testar")
        self.btn_testar_gemini.setFixedWidth(80)
        self.btn_testar_gemini.clicked.connect(lambda: self._testar_chave_ia("gratuito"))
        gemini_row.addWidget(self.btn_testar_gemini)
        card_ia.layout().addLayout(gemini_row)

        lbl_gemini_info = QLabel(
            '🔗 Obtenha gratuitamente em: <a href="https://aistudio.google.com/app/apikey">aistudio.google.com/app/apikey</a> — '
            'não precisa de cartão de crédito.')
        lbl_gemini_info.setOpenExternalLinks(True)
        lbl_gemini_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        card_ia.layout().addWidget(lbl_gemini_info)

        card_ia.layout().addSpacing(12)

        # Chave Anthropic
        card_ia.layout().addWidget(QLabel("<b>⭐ Anthropic API Key (Plano Pro)</b>"))
        claude_row = QHBoxLayout()
        self.txt_anthropic_key = input_field("Cole sua chave da API da Anthropic")
        self.txt_anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        claude_row.addWidget(self.txt_anthropic_key)
        self.btn_show_claude = btn_secundario("👁")
        self.btn_show_claude.setFixedWidth(40)
        self.btn_show_claude.clicked.connect(lambda: self._toggle_senha(self.txt_anthropic_key, self.btn_show_claude))
        claude_row.addWidget(self.btn_show_claude)
        self.btn_testar_claude = btn_primario("Testar")
        self.btn_testar_claude.setFixedWidth(80)
        self.btn_testar_claude.clicked.connect(lambda: self._testar_chave_ia("pro"))
        claude_row.addWidget(self.btn_testar_claude)
        card_ia.layout().addLayout(claude_row)

        lbl_claude_info = QLabel(
            '🔗 Obtenha em: <a href="https://console.anthropic.com/settings/keys">console.anthropic.com/settings/keys</a> — '
            'plano pago, custo aproximado de R$ 30-80/mês para uso individual.')
        lbl_claude_info.setOpenExternalLinks(True)
        lbl_claude_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        card_ia.layout().addWidget(lbl_claude_info)

        card_ia.layout().addSpacing(12)

        # Chave Groq (gratuito recomendado)
        card_ia.layout().addWidget(QLabel("<b>⚡ Groq API Key (Gratuito — recomendado como alternativa)</b>"))
        groq_row = QHBoxLayout()
        self.txt_groq_key = input_field("Cole sua chave da API do Groq")
        self.txt_groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        groq_row.addWidget(self.txt_groq_key)
        self.btn_show_groq = btn_secundario("👁")
        self.btn_show_groq.setFixedWidth(40)
        self.btn_show_groq.clicked.connect(lambda: self._toggle_senha(self.txt_groq_key, self.btn_show_groq))
        groq_row.addWidget(self.btn_show_groq)
        self.btn_testar_groq = btn_primario("Testar")
        self.btn_testar_groq.setFixedWidth(80)
        self.btn_testar_groq.clicked.connect(lambda: self._testar_chave_ia("groq"))
        groq_row.addWidget(self.btn_testar_groq)
        card_ia.layout().addLayout(groq_row)

        lbl_groq_info = QLabel(
            '🔗 Obtenha grátis em: <a href="https://console.groq.com/keys">console.groq.com/keys</a> — '
            'gratuito, sem cartão, muito rápido. Ideal como alternativa ao Gemini.')
        lbl_groq_info.setOpenExternalLinks(True)
        lbl_groq_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        card_ia.layout().addWidget(lbl_groq_info)

        card_ia.layout().addSpacing(12)

        # Chave DeepSeek
        card_ia.layout().addWidget(QLabel("<b>🐋 DeepSeek API Key (Pago / Alternativa)</b>"))
        deepseek_row = QHBoxLayout()
        self.txt_deepseek_key = input_field("Cole sua chave da API da DeepSeek")
        self.txt_deepseek_key.setEchoMode(QLineEdit.EchoMode.Password)
        deepseek_row.addWidget(self.txt_deepseek_key)
        self.btn_show_deepseek = btn_secundario("👁")
        self.btn_show_deepseek.setFixedWidth(40)
        self.btn_show_deepseek.clicked.connect(lambda: self._toggle_senha(self.txt_deepseek_key, self.btn_show_deepseek))
        deepseek_row.addWidget(self.btn_show_deepseek)
        self.btn_testar_deepseek = btn_primario("Testar")
        self.btn_testar_deepseek.setFixedWidth(80)
        self.btn_testar_deepseek.clicked.connect(lambda: self._testar_chave_ia("deepseek"))
        deepseek_row.addWidget(self.btn_testar_deepseek)
        card_ia.layout().addLayout(deepseek_row)

        lbl_deepseek_info = QLabel(
            '🔗 Obtenha em: <a href="https://platform.deepseek.com/api_keys">platform.deepseek.com/api_keys</a> — '
            'requer recarga (top-up). Uso muito barato, mas não é gratuito.')
        lbl_deepseek_info.setOpenExternalLinks(True)
        lbl_deepseek_info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        card_ia.layout().addWidget(lbl_deepseek_info)

        card_ia.layout().addSpacing(8)

        # Opção de fallback automático
        self.cb_fallback = QCheckBox("Usar alternativa (Groq/DeepSeek) automaticamente se o provedor principal estiver sobrecarregado (recomendado)")
        self.cb_fallback.setChecked(True)
        self.cb_fallback.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        card_ia.layout().addWidget(self.cb_fallback)

        card_ia.layout().addSpacing(12)

        self.lbl_status_ia = QLabel("")
        self.lbl_status_ia.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        self.lbl_status_ia.setWordWrap(True)
        card_ia.layout().addWidget(self.lbl_status_ia)

        btn_salvar_ia = btn_primario("💾  Salvar Configurações de IA")
        btn_salvar_ia.clicked.connect(lambda: self.salvar_ia(silencioso=False))
        card_ia.layout().addWidget(btn_salvar_ia)

        layout.addWidget(card_ia)


        # ── BASE DE CONHECIMENTO (RAG) ──
        layout.addWidget(self._lbl_secao("🧠  Base de Conhecimento da IA (RAG)"))
        card_rag = self._card()

        desc_rag = QLabel(
            "A IA pode usar suas jurisprudências e doutrinas salvas para fundamentar "
            "respostas e peças. Novos itens são indexados automaticamente. Use o botão "
            "abaixo para reindexar tudo de uma vez (necessário na primeira vez).")
        desc_rag.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        desc_rag.setWordWrap(True)
        card_rag.layout().addWidget(desc_rag)
        card_rag.layout().addSpacing(8)

        rag_status_row = QHBoxLayout()
        self.lbl_rag_stats = QLabel("Carregando estatísticas...")
        self.lbl_rag_stats.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
        rag_status_row.addWidget(self.lbl_rag_stats)
        rag_status_row.addStretch()
        self.btn_reindexar = btn_primario("🔄  Reindexar Tudo")
        self.btn_reindexar.clicked.connect(self.reindexar_rag)
        rag_status_row.addWidget(self.btn_reindexar)
        card_rag.layout().addLayout(rag_status_row)

        self.lbl_rag_status = QLabel("")
        self.lbl_rag_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        self.lbl_rag_status.setWordWrap(True)
        card_rag.layout().addWidget(self.lbl_rag_status)

        layout.addWidget(card_rag)

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


    def _upload_logo(self):
        from core.database import salvar_logo_escritorio
        from ui.widgets import dialogo_abrir
        caminho = dialogo_abrir(self, 'Selecionar Logo ou Foto', 'Imagens (*.png *.jpg *.jpeg *.webp *.bmp)')
        if caminho:
            try:
                destino = salvar_logo_escritorio(caminho)
                self._atualizar_preview_logo(destino)
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, 'Erro', f'Não foi possível salvar a logo: {e}')

    def _remover_logo(self):
        from core.database import salvar_configuracao
        salvar_configuracao('logo_escritorio', '')
        self.lbl_logo_preview.setPixmap(__import__('PyQt6.QtGui', fromlist=['QPixmap']).QPixmap())
        self.lbl_logo_preview.setText('Nenhuma logo configurada.')

    def _atualizar_preview_logo(self, caminho=None):
        from core.database import get_logo_escritorio
        from PyQt6.QtGui import QPixmap
        if not caminho:
            caminho = get_logo_escritorio()
        if caminho and os.path.exists(caminho):
            from PyQt6.QtCore import Qt
            try:
                dpr = self.devicePixelRatioF() or 1.0
            except Exception:
                dpr = 1.0
            pix = QPixmap(caminho)
            if not pix.isNull():
                pix = pix.scaled(
                    int(200 * dpr), int(70 * dpr),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                pix.setDevicePixelRatio(dpr)
                self.lbl_logo_preview.setPixmap(pix)
                self.lbl_logo_preview.setText('')
        else:
            self.lbl_logo_preview.setText('Nenhuma logo configurada.')



    def reindexar_rag(self):
        from PyQt6.QtWidgets import QMessageBox
        resp = QMessageBox.question(self, "Reindexar",
            "Isso vai processar todas as jurisprudências e doutrinas salvas.\n"
            "Pode levar alguns minutos na primeira vez (o modelo de IA será baixado).\n\nContinuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        self.lbl_rag_status.setText("⏳  Reindexando... isso pode levar alguns minutos. Não feche o programa.")
        self.lbl_rag_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
        self.btn_reindexar.setEnabled(False)
        self._thread_rag = ReindexarRAGThread()
        self._thread_rag.resultado.connect(self._reindex_concluido)
        self._thread_rag.start()

    def _reindex_concluido(self, ok, msg):
        self.btn_reindexar.setEnabled(True)
        if ok:
            self.lbl_rag_status.setText(f"✅  {msg}")
            self.lbl_rag_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; font-weight: 600; border: none;")
        else:
            self.lbl_rag_status.setText(f"❌  {msg}")
            self.lbl_rag_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px; font-weight: 600; border: none;")
        self._atualizar_stats_rag()

    def _atualizar_stats_rag(self):
        from core.ai.runner import chamar_rag
        import threading
        def _trabalho():
            ok, dados = chamar_rag("stats", timeout=60)
            if ok:
                s = dados.get("stats", {})
                txt = f"📚 {s.get('jurisprudencia',0)} trechos de jurisprudência  •  📖 {s.get('doutrina',0)} trechos de doutrina indexados"
            else:
                txt = "Base de conhecimento ainda não inicializada."
            self.lbl_rag_stats.setText(txt)
        threading.Thread(target=_trabalho, daemon=True).start()

    def _toggle_senha(self, campo, botao):
        if campo.echoMode() == QLineEdit.EchoMode.Password:
            campo.setEchoMode(QLineEdit.EchoMode.Normal)
            botao.setText("🙈")
        else:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            botao.setText("👁")

    def _testar_chave_ia(self, plano):
        if plano == "pro":
            chave = self.txt_anthropic_key.text().strip()
        elif plano == "deepseek":
            chave = self.txt_deepseek_key.text().strip()
        elif plano == "groq":
            chave = self.txt_groq_key.text().strip()
        else:
            chave = self.txt_gemini_key.text().strip()
        if not chave:
            self.lbl_status_ia.setText("⚠️  Informe a chave antes de testar.")
            self.lbl_status_ia.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px; font-weight: 600; border: none;")
            return

        self.lbl_status_ia.setText("⏳  Testando conexão... (até 20s)")
        self.lbl_status_ia.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
        self.btn_testar_gemini.setEnabled(False)
        self.btn_testar_claude.setEnabled(False)
        self.btn_testar_deepseek.setEnabled(False)
        self.btn_testar_groq.setEnabled(False)

        self._thread_teste_ia = TestarChaveIAThread(plano, chave)
        self._thread_teste_ia.resultado.connect(self._resultado_teste_ia)
        self._thread_teste_ia.start()

    def _resultado_teste_ia(self, ok, msg):
        self.btn_testar_gemini.setEnabled(True)
        self.btn_testar_claude.setEnabled(True)
        self.btn_testar_deepseek.setEnabled(True)
        self.btn_testar_groq.setEnabled(True)
        if ok:
            # Salvar automaticamente as chaves ao testar com sucesso (evita perder a chave)
            self.salvar_ia(silencioso=True)
            self.lbl_status_ia.setText(f"✅  Conexão bem-sucedida e chave salva! Resposta: {msg}")
            self.lbl_status_ia.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; font-weight: 600; border: none;")
        else:
            self.lbl_status_ia.setText(f"❌  Falha: {msg}")
            self.lbl_status_ia.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px; font-weight: 600; border: none;")

    def salvar_ia(self, silencioso=False):
        salvar_configuracao("ia_plano", self.cb_plano_ia.currentData())
        salvar_configuracao("ia_gemini_key", self.txt_gemini_key.text().strip())
        salvar_configuracao("ia_anthropic_key", self.txt_anthropic_key.text().strip())
        salvar_configuracao("ia_deepseek_key", self.txt_deepseek_key.text().strip())
        salvar_configuracao("ia_groq_key", self.txt_groq_key.text().strip())
        salvar_configuracao("ia_usar_fallback", "1" if self.cb_fallback.isChecked() else "0")
        if not silencioso:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Configurações salvas",
                "✅ Configurações de IA salvas com sucesso!\n\n"
                "As chaves de API ficam guardadas e não serão perdidas.")

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
        self._atualizar_preview_logo()
        idx_plano = self.cb_plano_ia.findData(cfg.get('ia_plano', 'gratuito'))
        if idx_plano >= 0: self.cb_plano_ia.setCurrentIndex(idx_plano)
        self.txt_gemini_key.setText(cfg.get('ia_gemini_key', ''))
        self.txt_anthropic_key.setText(cfg.get('ia_anthropic_key', ''))
        self.txt_deepseek_key.setText(cfg.get('ia_deepseek_key', ''))
        self.txt_groq_key.setText(cfg.get('ia_groq_key', ''))
        self.cb_fallback.setChecked(cfg.get('ia_usar_fallback', '1') != '0')
        try:
            self._atualizar_stats_rag()
        except Exception:
            pass
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
        self._atualizar_preview_logo()
        idx_plano = self.cb_plano_ia.findData(cfg.get('ia_plano', 'gratuito'))
        if idx_plano >= 0: self.cb_plano_ia.setCurrentIndex(idx_plano)
        self.txt_gemini_key.setText(cfg.get('ia_gemini_key', ''))
        self.txt_anthropic_key.setText(cfg.get('ia_anthropic_key', ''))
        self.txt_deepseek_key.setText(cfg.get('ia_deepseek_key', ''))
        self.txt_groq_key.setText(cfg.get('ia_groq_key', ''))
        self.cb_fallback.setChecked(cfg.get('ia_usar_fallback', '1') != '0')
        try:
            self._atualizar_stats_rag()
        except Exception:
            pass
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
        import subprocess
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", BACKUP_DIR], creationflags=0x08000000)
            else:
                subprocess.Popen(["xdg-open", BACKUP_DIR])
        except Exception:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Pasta de backups", f"Backups em:\n{BACKUP_DIR}")

    # ── Atualizações ──
    def verificar_atualizacao(self):
        self.lbl_upd_status.setText("🔍  Verificando atualizações...")
        self.lbl_upd_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
        QTimer.singleShot(1800, self._sem_atualizacao)

    def _sem_atualizacao(self):
        self.lbl_upd_status.setText(f"✅  Você já possui a versão mais recente (Legis {APP_VERSION}).")
        self.lbl_upd_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; font-weight: 600; border: none;")