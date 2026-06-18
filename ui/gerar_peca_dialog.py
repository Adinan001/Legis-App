# ui/gerar_peca_dialog.py — Diálogo de geração de peça com IA
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTextEdit, QLineEdit, QPushButton,
                             QFormLayout, QMessageBox, QFrame, QWidget,
                             QCheckBox, QProgressBar, QRadioButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from config import COLORS, AREAS_DIREITO
from ui.widgets import btn_primario, btn_secundario, input_field, separador_h, estilo_dialog
from core.database import buscar_processos, buscar_clientes, buscar_configuracoes

TIPOS_PECA = [
    "Petição Inicial",
    "Contestação",
    "Réplica",
    "Apelação",
    "Agravo de Instrumento",
    "Agravo Interno",
    "Embargos de Declaração",
    "Contrarrazões",
    "Memoriais",
    "Recurso Especial",
    "Recurso Extraordinário",
    "Habeas Corpus",
    "Mandado de Segurança",
    "Notificação Extrajudicial",
    "Contrato",
    "Parecer Jurídico",
]


class GerarPecaThread(QThread):
    pronto = pyqtSignal(str)
    erro = pyqtSignal(str)

    def __init__(self, tipo_peca, dados_caso, plano):
        super().__init__()
        self.tipo_peca = tipo_peca
        self.dados_caso = dados_caso
        self.plano = plano

    def run(self):
        try:
            from core.ai.legis_ai import LegisAI
            ia = LegisAI(plano_usuario=self.plano)
            texto = ia.gerar_peca(self.tipo_peca, self.dados_caso)
            self.pronto.emit(texto)
        except Exception as e:
            self.erro.emit(str(e))


class GerarPecaMultiAgenteThread(QThread):
    pronto = pyqtSignal(str)
    erro = pyqtSignal(str)
    progresso = pyqtSignal(str, str)  # (nome_agente, status)

    def __init__(self, tipo_peca, dados_caso, plano):
        super().__init__()
        self.tipo_peca = tipo_peca
        self.dados_caso = dados_caso
        self.plano = plano

    def run(self):
        try:
            from core.ai.legis_ai import LegisAI
            ia = LegisAI(plano_usuario=self.plano)
            def cb(agente, status):
                self.progresso.emit(agente, status)
            resultado = ia.gerar_peca_multiagente(self.tipo_peca, self.dados_caso, callback_progresso=cb)
            self.pronto.emit(resultado.get("peca", ""))
        except Exception as e:
            self.erro.emit(str(e))


class GerarPecaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerar Peça com IA")
        self.setMinimumSize(620, 720)
        self.setStyleSheet(estilo_dialog())
        self._resultado = None
        self._tipo_gerado = None
        self._thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        titulo = QLabel("🤖  Gerar Peça com Inteligência Artificial")
        titulo.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)

        sub = QLabel("Preencha os dados do caso. A IA usará sua jurisprudência e doutrina salvas na fundamentação.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)
        layout.addWidget(separador_h())

        # ── SELETOR DE MODO ──
        modo_box = QFrame()
        modo_box.setStyleSheet(f"QFrame {{ background: {COLORS['accent_light']}; border-radius: 8px; }}")
        modo_lay = QVBoxLayout(modo_box)
        modo_lay.setContentsMargins(14, 10, 14, 10)
        modo_lay.setSpacing(6)
        lbl_modo = QLabel("<b>Modo de geração:</b>")
        lbl_modo.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
        modo_lay.addWidget(lbl_modo)

        radios = QHBoxLayout()
        self.rb_simples = QRadioButton("⚡ Simples — rápido (1 chamada)")
        self.rb_multi = QRadioButton("🎯 Multi-Agente — 5 especialistas (mais lento, melhor)")
        self.rb_simples.setChecked(True)
        for rb in (self.rb_simples, self.rb_multi):
            rb.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; border: none;")
        radios.addWidget(self.rb_simples)
        radios.addWidget(self.rb_multi)
        radios.addStretch()
        modo_lay.addLayout(radios)
        layout.addWidget(modo_box)

        form = QFormLayout()
        form.setSpacing(10)
        form.setVerticalSpacing(16)
        form.setHorizontalSpacing(14)
        form.setContentsMargins(0, 6, 0, 6)

        def lbl(t):
            l = QLabel(f"<b>{t}</b>")
            l.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; border: none;")
            return l

        # Tipo de peça
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(TIPOS_PECA)
        self.cb_tipo.setStyleSheet(self._estilo_combo())
        form.addRow(lbl("Tipo de peça:"), self.cb_tipo)

        # Área
        self.cb_area = QComboBox()
        self.cb_area.addItems(AREAS_DIREITO)
        self.cb_area.setStyleSheet(self._estilo_combo())
        form.addRow(lbl("Área do direito:"), self.cb_area)

        # Vincular a processo existente (opcional)
        self.cb_processo = QComboBox()
        self.cb_processo.addItem("— Nenhum / Novo caso —", "")
        try:
            for p in buscar_processos():
                self.cb_processo.addItem(f"{p['numero']} — {p['cliente']}", p['numero'])
        except Exception:
            pass
        self.cb_processo.setStyleSheet(self._estilo_combo())
        self.cb_processo.currentIndexChanged.connect(self._preencher_do_processo)
        form.addRow(lbl("Vincular processo:"), self.cb_processo)

        # Vara / Comarca (opcional)
        self.txt_vara = input_field("Ex: 2ª Vara Cível da Comarca de Sorocaba/SP")
        form.addRow(lbl("Vara / Comarca:"), self.txt_vara)

        layout.addLayout(form)

        # Faixa com dados do escritório que serão usados automaticamente
        cfg = buscar_configuracoes()
        adv = cfg.get("responsavel", "")
        oab = cfg.get("oab", "")
        if adv or oab:
            # Evita duplicar "OAB" se o valor já contém
            oab_fmt = oab if oab.upper().startswith("OAB") else f"OAB {oab}"
            info_adv = QLabel(f"✓ Será assinada por: <b>{adv or '[advogado]'}</b>" + (f" — {oab_fmt}" if oab else ""))
            info_adv.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; border: none; background: {COLORS['accent_light']}; padding: 6px 10px; border-radius: 6px;")
        else:
            info_adv = QLabel("⚠️ Dados do advogado não preenchidos. Configure em Configurações → Escritório para a assinatura sair automática.")
            info_adv.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px; border: none;")
        info_adv.setWordWrap(True)
        layout.addWidget(info_adv)

        # Partes
        layout.addWidget(lbl("Partes (autor, réu, qualificação):"))
        self.txt_partes = QTextEdit()
        self.txt_partes.setMaximumHeight(70)
        self.txt_partes.setPlaceholderText("Ex: Autor: João da Silva, CPF 000.000.000-00...\nRéu: Empresa XYZ Ltda, CNPJ...")
        self.txt_partes.setStyleSheet(self._estilo_text())
        layout.addWidget(self.txt_partes)

        # Fatos
        layout.addWidget(lbl("Fatos do caso:"))
        self.txt_fatos = QTextEdit()
        self.txt_fatos.setPlaceholderText("Descreva os fatos relevantes do caso...")
        self.txt_fatos.setStyleSheet(self._estilo_text())
        layout.addWidget(self.txt_fatos)

        # Pedidos
        layout.addWidget(lbl("Pedidos pretendidos:"))
        self.txt_pedidos = QTextEdit()
        self.txt_pedidos.setMaximumHeight(70)
        self.txt_pedidos.setPlaceholderText("O que se pretende obter com a peça...")
        self.txt_pedidos.setStyleSheet(self._estilo_text())
        layout.addWidget(self.txt_pedidos)

        # Usar RAG
        self.cb_rag = QCheckBox("Usar minha jurisprudência e doutrina salvas na fundamentação")
        self.cb_rag.setChecked(True)
        self.cb_rag.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        layout.addWidget(self.cb_rag)

        # ── PAINEL DE AGENTES (multi-agente) ──
        self._painel_agentes = QFrame()
        self._painel_agentes.setMinimumHeight(170)
        self._painel_agentes.setStyleSheet(f"QFrame {{ background: {COLORS['bg_main']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        pa_lay = QVBoxLayout(self._painel_agentes)
        pa_lay.setContentsMargins(14, 10, 14, 10)
        pa_lay.setSpacing(8)
        titulo_pa = QLabel("<b>Agentes trabalhando:</b>")
        titulo_pa.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px; border: none;")
        pa_lay.addWidget(titulo_pa)
        self._labels_agentes = {}
        for chave, nome in self._AGENTES:
            lbl_ag = QLabel(f"⏳  {nome} — aguardando")
            lbl_ag.setMinimumHeight(20)
            lbl_ag.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; border: none; padding: 1px;")
            pa_lay.addWidget(lbl_ag)
            self._labels_agentes[chave] = lbl_ag
        self._painel_agentes.setVisible(False)
        layout.addWidget(self._painel_agentes)

        # Progresso
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminado
        self.progress.setVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid {COLORS['border']}; border-radius: 6px; height: 8px; background: {COLORS['bg_main']}; }}
            QProgressBar::chunk {{ background: {COLORS['accent']}; border-radius: 6px; }}
        """)
        layout.addWidget(self.progress)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        # Botões
        botoes = QHBoxLayout()
        botoes.addStretch()
        self.btn_cancelar = btn_secundario("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(self.btn_cancelar)
        self.btn_gerar = btn_primario("🤖  Gerar Peça")
        self.btn_gerar.clicked.connect(self.gerar)
        botoes.addWidget(self.btn_gerar)
        layout.addLayout(botoes)

    def _estilo_combo(self):
        return f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px;"

    def _estilo_text(self):
        return f"padding: 8px; border: 1.5px solid {COLORS['border']}; border-radius: 6px; background: white; font-size: 12px; color: {COLORS['text_primary']};"

    def _preencher_do_processo(self):
        numero = self.cb_processo.currentData()
        if not numero:
            return
        try:
            for p in buscar_processos():
                if p["numero"] == numero:
                    # Preenche partes com o cliente
                    self.txt_partes.setPlainText(f"Cliente: {p.get('cliente','')}")
                    # Ajusta área se houver
                    acao = p.get("acao", "")
                    idx = self.cb_area.findText(acao)
                    if idx >= 0:
                        self.cb_area.setCurrentIndex(idx)
                    break
        except Exception:
            pass

    def gerar(self):
        if not self.txt_fatos.toPlainText().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Descreva ao menos os fatos do caso.")
            return

        cfg = buscar_configuracoes()
        plano = cfg.get("ia_plano", "gratuito")
        chave = {
            "pro": cfg.get("ia_anthropic_key", ""),
            "deepseek": cfg.get("ia_deepseek_key", ""),
            "groq": cfg.get("ia_groq_key", ""),
        }.get(plano, cfg.get("ia_gemini_key", "")).strip()
        if not chave:
            QMessageBox.warning(self, "IA não configurada",
                "Configure a chave de API em Configurações → Inteligência Artificial.")
            return

        dados_caso = {
            "area": self.cb_area.currentText(),
            "vara_comarca": self.txt_vara.text().strip(),
            "partes": self.txt_partes.toPlainText().strip(),
            "fatos": self.txt_fatos.toPlainText().strip(),
            "pedidos": self.txt_pedidos.toPlainText().strip(),
            "processo": self.cb_processo.currentData() or "",
        }
        self._tipo_gerado = self.cb_tipo.currentText()
        self._modo_multi = self.rb_multi.isChecked()

        if self._thread is not None and self._thread.isRunning():
            return

        self.btn_gerar.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        self.progress.setVisible(True)

        # Limpar thread anterior
        if self._thread is not None:
            try:
                self._thread.pronto.disconnect()
                self._thread.erro.disconnect()
            except Exception:
                pass
            self._thread.deleteLater()

        if self._modo_multi:
            # Modo multi-agente: mostrar painel de agentes
            self._painel_agentes.setVisible(True)
            self._resetar_agentes()
            self.lbl_status.setText("🎯  Gerando com 5 agentes especializados... pode levar 2-3 minutos.")
            self.lbl_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
            self._thread = GerarPecaMultiAgenteThread(self._tipo_gerado, dados_caso, plano)
            self._thread.progresso.connect(self._atualizar_agente)
            self._thread.pronto.connect(self._peca_pronta)
            self._thread.erro.connect(self._peca_erro)
            self._thread.finished.connect(lambda: self.btn_gerar.setEnabled(True))
            self._thread.start()
        else:
            self._painel_agentes.setVisible(False)
            self.lbl_status.setText("⏳  Gerando peça... pode levar até 1 minuto.")
            self.lbl_status.setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: 600; border: none;")
            self._thread = GerarPecaThread(self._tipo_gerado, dados_caso, plano)
            self._thread.pronto.connect(self._peca_pronta)
            self._thread.erro.connect(self._peca_erro)
            self._thread.finished.connect(lambda: self.btn_gerar.setEnabled(True))
            self._thread.start()

    # ── Painel de agentes ──
    _AGENTES = [
        ("estrategico", "🧠 Estratégico"),
        ("jurisprudencia", "⚖️ Jurisprudência"),
        ("doutrina", "📖 Doutrina"),
        ("redator", "✍️ Redator"),
        ("revisor", "🔍 Revisor"),
    ]

    def _resetar_agentes(self):
        for chave, _ in self._AGENTES:
            lbl = self._labels_agentes.get(chave)
            if lbl:
                nome = dict(self._AGENTES)[chave]
                lbl.setText(f"⏳  {nome} — aguardando")
                lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; border: none;")

    def _atualizar_agente(self, agente, status):
        lbl = self._labels_agentes.get(agente)
        if not lbl:
            return
        nome = dict(self._AGENTES).get(agente, agente)
        if status == "trabalhando":
            lbl.setText(f"🔄  {nome} — trabalhando...")
            lbl.setStyleSheet(f"color: {COLORS['blue']}; font-size: 12px; font-weight: 600; border: none;")
        elif status == "concluido":
            lbl.setText(f"✅  {nome} — concluído")
            lbl.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: 600; border: none;")

    def _peca_pronta(self, texto):
        self._resultado = texto
        self.progress.setVisible(False)
        self.lbl_status.setText("✅  Peça gerada com sucesso!")
        self.lbl_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; font-weight: 600; border: none;")
        self.accept()

    def _peca_erro(self, msg):
        self.progress.setVisible(False)
        self.btn_gerar.setEnabled(True)
        self.btn_cancelar.setEnabled(True)
        self.lbl_status.setText(f"❌  Erro: {msg}")
        self.lbl_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px; font-weight: 600; border: none;")

    def obter_resultado(self):
        """Retorna (titulo, categoria, conteudo) para criar o documento."""
        if not self._resultado:
            return None
        titulo = f"{self._tipo_gerado} - {self.cb_area.currentText()}"
        categoria = self._mapear_categoria()
        return titulo, categoria, self._resultado

    def _mapear_categoria(self):
        tipo = self._tipo_gerado or ""
        mapa = {
            "Petição Inicial": "Petições", "Contestação": "Petições",
            "Réplica": "Petições", "Apelação": "Recursos",
            "Agravo de Instrumento": "Recursos", "Agravo Interno": "Recursos",
            "Embargos de Declaração": "Recursos", "Contrarrazões": "Recursos",
            "Recurso Especial": "Recursos", "Recurso Extraordinário": "Recursos",
            "Memoriais": "Petições", "Habeas Corpus": "Habeas Corpus",
            "Mandado de Segurança": "Mandado de Segurança",
            "Notificação Extrajudicial": "Administrativo",
            "Contrato": "Contratos", "Parecer Jurídico": "Pareceres",
        }
        return mapa.get(tipo, "Outro")
