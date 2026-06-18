# ui/chat_ia_page.py — Chat Jurídico estilo Claude
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QPushButton, QScrollArea, QFrame,
                             QSizePolicy, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut, QTextOption
from config import COLORS
from core.database import buscar_configuracoes


class ConsultaIAThread(QThread):
    resposta_pronta = pyqtSignal(str)
    erro = pyqtSignal(str)

    def __init__(self, pergunta, historico, plano, usar_rag=False):
        super().__init__()
        self.pergunta = pergunta
        self.historico = historico
        self.plano = plano
        self.usar_rag = usar_rag

    def run(self):
        try:
            from core.ai.legis_ai import LegisAI
            ia = LegisAI(plano_usuario=self.plano)
            resposta = ia.consultar(self.pergunta, historico=self.historico, usar_rag=self.usar_rag)
            self.resposta_pronta.emit(resposta)
        except Exception as e:
            self.erro.emit(str(e))


class Mensagem(QWidget):
    """Mensagem estilo Claude — avatar + nome + texto, largura total."""
    def __init__(self, texto, autor="ia", parent=None):
        super().__init__(parent)
        self.autor = autor
        self.setStyleSheet("background: transparent;")

        wrapper = QHBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)

        # Container centralizado (largura máxima como no Claude)
        container = QWidget()
        container.setMaximumWidth(760)
        container.setStyleSheet("background: transparent;")
        wrapper.addWidget(container, alignment=Qt.AlignmentFlag.AlignHCenter)

        if autor == "user":
            # Mensagem do usuário — card sutil à direita
            lay = QVBoxLayout(container)
            lay.setContentsMargins(0, 4, 0, 4)
            lay.setSpacing(0)
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['accent_light']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 14px;
                }}
            """)
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(16, 12, 16, 12)
            lbl = QLabel(texto)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; border: none; background: transparent; line-height: 1.6;")
            card_lay.addWidget(lbl)
            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(card)
            row.setStretch(0, 1)
            lay.addLayout(row)
        else:
            # Mensagem da IA — avatar + texto, largura total
            lay = QHBoxLayout(container)
            lay.setContentsMargins(0, 8, 0, 8)
            lay.setSpacing(14)
            lay.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Avatar
            avatar = QLabel("⚖️")
            avatar.setFixedSize(32, 32)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setStyleSheet(f"""
                background: {COLORS['accent']}; border-radius: 16px;
                font-size: 16px; border: none;
            """)
            lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignTop)

            # Bloco de texto
            bloco = QVBoxLayout()
            bloco.setSpacing(3)
            nome = QLabel("Assistente Jurídico")
            nome.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 700; border: none;")
            bloco.addWidget(nome)

            self.lbl_texto = QLabel(texto)
            self.lbl_texto.setWordWrap(True)
            self.lbl_texto.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.lbl_texto.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; border: none; background: transparent; line-height: 1.7;")
            self.lbl_texto.setTextFormat(Qt.TextFormat.MarkdownText)
            bloco.addWidget(self.lbl_texto)
            lay.addLayout(bloco, 1)

    def atualizar_texto(self, texto):
        if hasattr(self, "lbl_texto"):
            self.lbl_texto.setText(texto)


class ChatIAPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._historico = []
        self._thread = None
        self._msg_carregando = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── CABEÇALHO ──
        cab = QWidget()
        cab.setFixedHeight(60)
        cab.setStyleSheet(f"background: {COLORS['white']}; border-bottom: 1px solid {COLORS['border']};")
        cab_lay = QHBoxLayout(cab)
        cab_lay.setContentsMargins(24, 0, 24, 0)
        lbl = QLabel("Chat Jurídico")
        lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        cab_lay.addWidget(lbl)
        cab_lay.addStretch()
        self.cb_plano_chat = QComboBox()
        self.cb_plano_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_plano_chat.setStyleSheet(f"""
            QComboBox {{ padding: 5px 10px; border: 1px solid {COLORS['border']};
                border-radius: 8px; background: white; font-size: 11px;
                color: {COLORS['text_primary']}; min-width: 150px; }}
            QComboBox:hover {{ border-color: {COLORS['accent']}; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.cb_plano_chat.currentIndexChanged.connect(self._trocar_plano_chat)
        cab_lay.addWidget(self.cb_plano_chat)

        # Botão nova conversa
        btn_nova = QPushButton("✛  Nova conversa")
        btn_nova.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nova.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['accent']};
                border: 1px solid {COLORS['border']}; border-radius: 8px;
                padding: 7px 14px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLORS['accent_light']}; }}
        """)
        btn_nova.clicked.connect(self.nova_conversa)
        cab_lay.addWidget(btn_nova)
        layout.addWidget(cab)

        # ── ÁREA DE MENSAGENS ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {COLORS['bg_main']}; }}
            QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['border']}; border-radius: 5px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.area_msgs = QWidget()
        self.area_msgs.setStyleSheet(f"background: {COLORS['bg_main']};")
        self.lay_msgs = QVBoxLayout(self.area_msgs)
        self.lay_msgs.setContentsMargins(24, 24, 24, 24)
        self.lay_msgs.setSpacing(6)
        self.lay_msgs.addStretch()

        self.scroll.setWidget(self.area_msgs)
        layout.addWidget(self.scroll, 1)

        # Tela de boas-vindas
        self._mostrar_boas_vindas()

        # ── CAIXA DE ENTRADA (flutuante embaixo) ──
        rodape = QWidget()
        rodape.setStyleSheet(f"background: {COLORS['bg_main']};")
        rodape_lay = QVBoxLayout(rodape)
        rodape_lay.setContentsMargins(24, 8, 24, 16)
        rodape_lay.setSpacing(4)

        # Container da caixa centralizado
        caixa_container = QWidget()
        caixa_container.setMaximumWidth(760)
        caixa_lay = QVBoxLayout(caixa_container)
        caixa_lay.setContentsMargins(0, 0, 0, 0)
        caixa_lay.setSpacing(4)

        # Caixa de input estilo Claude — bordas arredondadas, botão dentro
        self.caixa = QFrame()
        self.caixa.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['white']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        caixa_inner = QHBoxLayout(self.caixa)
        caixa_inner.setContentsMargins(16, 8, 8, 8)
        caixa_inner.setSpacing(8)

        self.txt_pergunta = QTextEdit()
        self.txt_pergunta.setPlaceholderText("Pergunte algo sobre Direito...")
        self.txt_pergunta.setStyleSheet(f"""
            QTextEdit {{
                background: transparent; border: none;
                font-size: 14px; color: {COLORS['text_primary']};
            }}
        """)
        self.txt_pergunta.setFixedHeight(48)
        self.txt_pergunta.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.txt_pergunta.textChanged.connect(self._ajustar_altura)
        caixa_inner.addWidget(self.txt_pergunta)

        self.btn_enviar = QPushButton("➤")
        self.btn_enviar.setFixedSize(38, 38)
        self.btn_enviar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enviar.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']}; color: white;
                font-size: 16px; border-radius: 19px; border: none;
            }}
            QPushButton:hover {{ background: {COLORS['accent_hover']}; }}
            QPushButton:disabled {{ background: {COLORS['border']}; color: {COLORS['text_muted']}; }}
        """)
        self.btn_enviar.clicked.connect(self.enviar_pergunta)
        caixa_inner.addWidget(self.btn_enviar, alignment=Qt.AlignmentFlag.AlignBottom)

        caixa_lay.addWidget(self.caixa)

        # Checkbox para usar o acervo (RAG) — desligado por padrão para respostas rápidas
        from PyQt6.QtWidgets import QCheckBox
        self.cb_usar_acervo = QCheckBox("Consultar meu acervo de jurisprudência/doutrina (mais lento)")
        self.cb_usar_acervo.setChecked(False)
        self.cb_usar_acervo.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none; padding: 2px;")
        caixa_lay.addWidget(self.cb_usar_acervo, alignment=Qt.AlignmentFlag.AlignLeft)

        # Aviso pequeno embaixo
        aviso = QLabel("O assistente pode cometer erros. Revise informações importantes.")
        aviso.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; border: none;")
        aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caixa_lay.addWidget(aviso)

        rodape_lay.addWidget(caixa_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(rodape)

        # Atalho Ctrl+Enter
        atalho = QShortcut(QKeySequence("Ctrl+Return"), self.txt_pergunta)
        atalho.activated.connect(self.enviar_pergunta)

        self._atualizar_plano()

    def _ajustar_altura(self):
        doc_altura = self.txt_pergunta.document().size().height()
        nova = min(max(48, int(doc_altura) + 16), 160)
        self.txt_pergunta.setFixedHeight(nova)

    def _atualizar_plano(self):
        cfg = buscar_configuracoes()
        plano_atual = cfg.get("ia_plano", "gratuito")
        # Montar lista só com IAs que têm chave configurada
        opcoes = []
        if cfg.get("ia_gemini_key", "").strip():
            opcoes.append(("🆓 Gemini", "gratuito"))
        if cfg.get("ia_groq_key", "").strip():
            opcoes.append(("⚡ Groq", "groq"))
        if cfg.get("ia_deepseek_key", "").strip():
            opcoes.append(("🐋 DeepSeek", "deepseek"))
        if cfg.get("ia_anthropic_key", "").strip():
            opcoes.append(("⭐ Claude", "pro"))
        if not opcoes:
            opcoes.append(("⚠️ Configure uma IA", "gratuito"))

        self.cb_plano_chat.blockSignals(True)
        self.cb_plano_chat.clear()
        for label, valor in opcoes:
            self.cb_plano_chat.addItem(label, valor)
        # Selecionar o plano atual
        idx = self.cb_plano_chat.findData(plano_atual)
        if idx >= 0:
            self.cb_plano_chat.setCurrentIndex(idx)
        self.cb_plano_chat.blockSignals(False)

    def _trocar_plano_chat(self):
        """Troca o plano ativo e salva nas Configurações."""
        novo_plano = self.cb_plano_chat.currentData()
        if novo_plano:
            from core.database import salvar_configuracao
            salvar_configuracao("ia_plano", novo_plano)

    def _mostrar_boas_vindas(self):
        self._boas_vindas = QWidget()
        bv_lay = QVBoxLayout(self._boas_vindas)
        bv_lay.setContentsMargins(20, 60, 20, 20)
        bv_lay.setSpacing(12)
        bv_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icone = QLabel("⚖️")
        icone.setFont(QFont("Segoe UI", 40))
        icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icone.setStyleSheet("border: none;")
        bv_lay.addWidget(icone)

        titulo = QLabel("Assistente Jurídico Legis")
        titulo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv_lay.addWidget(titulo)

        sub = QLabel("Tire dúvidas jurídicas, peça ajuda com peças e estratégias processuais.\nComo posso ajudar você hoje?")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; border: none;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bv_lay.addWidget(sub)

        # Sugestões clicáveis
        sugestoes = [
            "Quais os requisitos da petição inicial no CPC?",
            "Explique a diferença entre prescrição e decadência",
            "Modelo de contestação trabalhista",
        ]
        sug_container = QWidget()
        sug_lay = QVBoxLayout(sug_container)
        sug_lay.setSpacing(8)
        sug_lay.setContentsMargins(0, 16, 0, 0)
        for s in sugestoes:
            btn = QPushButton(f"💬  {s}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['white']}; color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']}; border-radius: 10px;
                    padding: 12px 16px; font-size: 12px; text-align: left;
                }}
                QPushButton:hover {{ background: {COLORS['accent_light']}; color: {COLORS['accent']}; border-color: {COLORS['accent']}; }}
            """)
            btn.clicked.connect(lambda _, t=s: self._usar_sugestao(t))
            sug_lay.addWidget(btn)
        sug_container.setMaximumWidth(480)
        bv_lay.addWidget(sug_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.lay_msgs.insertWidget(self.lay_msgs.count() - 1, self._boas_vindas)

    def _usar_sugestao(self, texto):
        self.txt_pergunta.setPlainText(texto)
        self.enviar_pergunta()

    def _remover_boas_vindas(self):
        if hasattr(self, "_boas_vindas") and self._boas_vindas:
            self._boas_vindas.setParent(None)
            self._boas_vindas.deleteLater()
            self._boas_vindas = None

    def nova_conversa(self):
        # Limpar todas as mensagens
        while self.lay_msgs.count() > 1:
            item = self.lay_msgs.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._historico = []
        self._mostrar_boas_vindas()

    def enviar_pergunta(self):
        pergunta = self.txt_pergunta.toPlainText().strip()
        if not pergunta:
            return

        self._atualizar_plano()
        cfg = buscar_configuracoes()
        plano = cfg.get("ia_plano", "gratuito")
        chave = cfg.get("ia_anthropic_key" if plano == "pro" else "ia_gemini_key", "").strip()
        if not chave:
            self._remover_boas_vindas()
            self._adicionar_mensagem(
                f"⚠️ Nenhuma chave de API configurada para o plano "
                f"{'Pro (Claude)' if plano == 'pro' else 'Gratuito (Gemini)'}.\n\n"
                f"Acesse **Configurações → Inteligência Artificial** para configurar.",
                autor="ia")
            return

        self._remover_boas_vindas()
        self._adicionar_mensagem(pergunta, autor="user")
        self.txt_pergunta.clear()
        self._historico.append({"role": "user", "content": pergunta})

        # Mensagem de carregamento
        self._msg_carregando = self._adicionar_mensagem("_Pensando..._", autor="ia")

        self.btn_enviar.setEnabled(False)
        self._thread = ConsultaIAThread(pergunta, self._historico[:-1], plano, usar_rag=self.cb_usar_acervo.isChecked())
        self._thread.resposta_pronta.connect(self._resposta_recebida)
        self._thread.erro.connect(self._erro_recebido)
        self._thread.start()

    def _resposta_recebida(self, resposta):
        if self._msg_carregando:
            self._msg_carregando.atualizar_texto(resposta)
            self._msg_carregando = None
        self._historico.append({"role": "assistant", "content": resposta})
        self.btn_enviar.setEnabled(True)
        self._scroll_final()

    def _erro_recebido(self, erro_msg):
        if self._msg_carregando:
            self._msg_carregando.atualizar_texto(f"❌ **Erro ao consultar a IA:**\n\n{erro_msg}")
            self._msg_carregando = None
        self.btn_enviar.setEnabled(True)
        self._scroll_final()

    def _adicionar_mensagem(self, texto, autor="ia"):
        msg = Mensagem(texto, autor=autor)
        self.lay_msgs.insertWidget(self.lay_msgs.count() - 1, msg)
        self._scroll_final()
        return msg

    def _scroll_final(self):
        QTimer.singleShot(80, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))