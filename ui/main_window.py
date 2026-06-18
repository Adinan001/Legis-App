# ui/main_window.py — Legis Beta com login e permissões
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QCursor, QKeySequence, QShortcut
import config
from config import COLORS, APP_NAME, APP_SUBTITLE
from ui.dashboard_page        import DashboardPage
from ui.processos_page        import ProcessosPage
from ui.clientes_page         import ClientesPage
from ui.financeiro_page       import FinanceiroPage
from ui.agenda_page           import AgendaPage
from ui.documentos_page       import DocumentosPage
from ui.jurisprudencia_page   import JurisprudenciaPage
from ui.doutrina_page         import DoutrinaPage
from ui.consulta_datajud_page import ConsultaDatajudPage
from ui.consultas_page        import ConsultasPage
from ui.relatorios_page       import RelatoriosPage
from ui.configuracoes_page    import ConfiguracoesPage
from ui.usuarios_page         import UsuariosPage
from ui.chat_ia_page          import ChatIAPage
from ui.busca_global          import BuscaGlobalDialog
from ui.alertas_widget        import BotaoAlertas, PainelAlertas

# Permissões por perfil
PERMISSOES_PERFIL = {
    "Administrador": [0,1,2,3,4,5,6,7,8,9,10,11,12,13],  # tudo
    "Advogado":      [0,1,2,3,4,5,6,7,8,9,10,13],       # sem usuários(12) e config(11)
    "Estagiário":    [0,1,5],                             # dashboard, processos, agenda
}

MENU_ITENS = [
    ("📊", "Dashboard",          0),
    ("⚖️",  "Processos",          1),
    ("🤖", "Proc. Automáticos",  2),
    ("👥", "Clientes",            3),
    ("💰", "Financeiro",          4),
    ("📅", "Agenda & Prazos",     5),
    ("📄", "Documentos",          6),
    ("📚", "Jurisprudência",      7),
    ("📖", "Doutrina",            8),
    ("💬", "Consultas",           9),
    ("📋", "Relatórios",         10),
    ("🤖", "Chat Jurídico (IA)",  13),
]
MENU_RODAPE = [
    ("⚙️",  "Configurações",     11),
    ("👤", "Usuários",           12),
]

def _btn_style(ativo=False):
    if ativo:
        return f"""QPushButton {{
            text-align: left; padding: 9px 14px;
            background-color: {COLORS['bg_active']};
            border: none; font-size: 12px; color: white;
            font-weight: 700; border-radius: 7px;
        }}"""
    return f"""QPushButton {{
        text-align: left; padding: 9px 14px;
        background: transparent; border: none;
        font-size: 12px; color: {COLORS['sidebar_text']};
        font-weight: 500; border-radius: 7px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_sidebar_hover']}; color: white;
    }}"""

def _btn_menu(icone, texto):
    b = QPushButton(f"  {icone}  {texto}")
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setStyleSheet(_btn_style(False))
    b.setMinimumHeight(38)
    return b


class MainWindow(QMainWindow):
    def __init__(self, usuario=None):
        super().__init__()
        self._usuario = usuario or {"nome": "Admin", "perfil": "Administrador"}
        self._perfil = self._usuario.get("perfil", "Administrador")
        self._permissoes = PERMISSOES_PERFIL.get(self._perfil, [0])
        self.setWindowTitle(f"{APP_NAME} Beta — {APP_SUBTITLE}")
        self.resize(1320, 800)
        self.setMinimumSize(1024, 640)
        self._indice_atual = 0
        self._construir_ui()
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.abrir_busca_global)

    def _construir_ui(self):
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_main']}; }}")
        central = QWidget()
        self.setCentralWidget(central)
        self._root = QHBoxLayout(central)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(0)

        # ── SIDEBAR ──
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(232)
        self.sidebar.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(14, 16, 14, 14)
        sb.setSpacing(2)

        self.lbl_marca = QLabel(APP_NAME)
        self.lbl_marca.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        self.lbl_marca.setStyleSheet("color: white; padding-left: 6px;")
        sb.addWidget(self.lbl_marca)
        lbl_beta = QLabel("Beta")
        lbl_beta.setFont(QFont("Segoe UI", 9))
        lbl_beta.setStyleSheet(f"color: {COLORS['accent']}; padding-left: 6px; font-weight: 700;")
        sb.addWidget(lbl_beta)
        sb.addSpacing(6)

        # Info do usuário logado
        info_user = QWidget()
        info_user.setStyleSheet(f"background: rgba(255,255,255,0.06); border-radius: 7px;")
        info_lay = QVBoxLayout(info_user)
        info_lay.setContentsMargins(10, 8, 10, 8)
        info_lay.setSpacing(2)
        lbl_user = QLabel(f"👤  {self._usuario.get('nome', '')}")
        lbl_user.setStyleSheet(f"color: white; font-size: 12px; font-weight: 600; border: none;")
        lbl_perfil = QLabel(self._perfil)
        lbl_perfil.setStyleSheet(f"color: {COLORS['sidebar_text']}; font-size: 10px; border: none;")
        info_lay.addWidget(lbl_user)
        info_lay.addWidget(lbl_perfil)
        sb.addWidget(info_user)
        sb.addSpacing(6)

        # Pesquisa global
        btn_busca = QPushButton("  🔍  Pesquisar  (Ctrl+F)")
        btn_busca.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_busca.setMinimumHeight(36)
        btn_busca.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 7px 14px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 7px; font-size: 12px;
                color: {COLORS['sidebar_text']};
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.15); color: white; }}
        """)
        btn_busca.clicked.connect(self.abrir_busca_global)
        sb.addWidget(btn_busca)

        # Botão alertas
        self.btn_alertas = BotaoAlertas()
        self.btn_alertas.clicked.connect(self.abrir_alertas)
        sb.addWidget(self.btn_alertas)
        sb.addSpacing(4)

        linha = QFrame()
        linha.setFrameShape(QFrame.Shape.HLine)
        linha.setStyleSheet("background: #2E4A32; border: none; max-height: 1px;")
        sb.addWidget(linha)
        sb.addSpacing(4)

        self._botoes = {}
        for icone, texto, idx in MENU_ITENS:
            btn = _btn_menu(icone, texto)
            btn.clicked.connect(lambda _, i=idx: self.mudar_tela(i))
            self._botoes[idx] = btn
            # Ocultar itens sem permissão
            if idx not in self._permissoes:
                btn.setVisible(False)
            sb.addWidget(btn)

        sb.addStretch()
        linha2 = QFrame()
        linha2.setFrameShape(QFrame.Shape.HLine)
        linha2.setStyleSheet("background: #2E4A32; border: none; max-height: 1px;")
        sb.addWidget(linha2)
        sb.addSpacing(4)

        for icone, texto, idx in MENU_RODAPE:
            btn = _btn_menu(icone, texto)
            btn.clicked.connect(lambda _, i=idx: self.mudar_tela(i))
            self._botoes[idx] = btn
            if idx not in self._permissoes:
                btn.setVisible(False)
            sb.addWidget(btn)

        # Botão sair
        btn_sair = QPushButton("  🚪  Sair")
        btn_sair.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_sair.setMinimumHeight(36)
        btn_sair.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 7px 14px;
                background: transparent; border: none;
                font-size: 12px; color: {COLORS['danger']};
                font-weight: 500; border-radius: 7px;
            }}
            QPushButton:hover {{ background: rgba(192,57,43,0.15); }}
        """)
        btn_sair.clicked.connect(self.fazer_logout)
        sb.addWidget(btn_sair)

        self._root.addWidget(self.sidebar)

        # ── STACK ──
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_main']};")

        self.page_dashboard  = DashboardPage()
        self.page_processos  = ProcessosPage(ao_atualizar=self.page_dashboard.atualizar_dados)
        self.page_datajud    = ConsultaDatajudPage()
        self.page_clientes   = ClientesPage(ao_atualizar=self.page_dashboard.atualizar_dados)
        self.page_financeiro = FinanceiroPage()
        self.page_agenda     = AgendaPage(ao_atualizar=self.page_dashboard.atualizar_dados)
        self.page_documentos = DocumentosPage()
        self.page_juris      = JurisprudenciaPage()
        self.page_doutrina   = DoutrinaPage()
        self.page_consultas  = ConsultasPage()
        self.page_relatorios = RelatoriosPage()
        self.page_config     = ConfiguracoesPage()
        self.page_config.tema_alterado.connect(self._reaplicar_tema)
        self.page_usuarios   = UsuariosPage()
        self.page_chat_ia    = ChatIAPage()

        for page in [
            self.page_dashboard,   # 0
            self.page_processos,   # 1
            self.page_datajud,     # 2
            self.page_clientes,    # 3
            self.page_financeiro,  # 4
            self.page_agenda,      # 5
            self.page_documentos,  # 6
            self.page_juris,       # 7
            self.page_doutrina,    # 8
            self.page_consultas,   # 9
            self.page_relatorios,  # 10
            self.page_config,      # 11
            self.page_usuarios,    # 12
            self.page_chat_ia,      # 13
        ]:
            self.stack.addWidget(page)

        self._root.addWidget(self.stack)

        # Navegar para primeira aba permitida
        primeiro = self._permissoes[0] if self._permissoes else 0
        self.mudar_tela(primeiro)
        QTimer.singleShot(1000, self._verificar_alertas_iniciais)
        # Atualização automática dos processos monitorados (Datajud) ao abrir
        QTimer.singleShot(5000, self._atualizar_processos_monitorados)

    def _recarregar_aba_processos(self):
        """Recarrega tanto os processos próprios quanto os monitorados."""
        try:
            self.page_processos.carregar_dados_processos()
        except Exception:
            pass
        try:
            self.page_processos.carregar_monitorados()
        except Exception:
            pass

    def _atualizar_processos_monitorados(self):
        """Dispara a atualização em background dos processos monitorados."""
        try:
            from core.database import listar_processos_monitorados
            procs = listar_processos_monitorados()
            if not procs:
                print("[Datajud] Varredura automática: nenhum processo monitorado cadastrado.")
                return
            print(f"[Datajud] Varredura automática iniciada — consultando {len(procs)} processo(s)...")
            from ui.atualizador_processos import AtualizadorProcessosThread
            self._thread_atualiza_proc = AtualizadorProcessosThread()
            self._thread_atualiza_proc.concluido.connect(self._fim_atualizacao_auto)
            self._thread_atualiza_proc.start()
        except Exception as e:
            print(f"[Datajud] Erro ao iniciar varredura: {e}")

    def _fim_atualizacao_auto(self, novidades):
        """Quando a varredura termina: recarrega listas e mostra Últimas Movimentações."""
        print(f"[Datajud] Varredura concluída — {len(novidades)} processo(s) com movimentação nova.")
        try:
            from PyQt6 import sip
            if not sip.isdeleted(self.page_processos):
                self.page_processos.carregar_monitorados()
        except Exception:
            pass
        try:
            from PyQt6 import sip
            if not sip.isdeleted(self.page_dashboard):
                self.page_dashboard.atualizar_dados()
        except Exception:
            pass
        # Mostrar a janela de Últimas Movimentações SOMENTE se houver novidades
        try:
            if novidades:
                from ui.movimentacoes_dialog import MovimentacoesDialog
                dlg = MovimentacoesDialog(self, novidades=novidades)
                dlg.exec()
        except Exception:
            pass

    def mudar_tela(self, indice):
        if indice not in self._permissoes:
            return
        self._indice_atual = indice
        self.stack.setCurrentIndex(indice)
        reload_map = {
            0:  self.page_dashboard.atualizar_dados,
            1:  self._recarregar_aba_processos,
            3:  self.page_clientes.carregar_dados_clientes,
            4:  self.page_financeiro.carregar_dados_financeiros,
            5:  self.page_agenda.carregar_dados_agenda,
            6:  self.page_documentos.carregar_documentos,
            9:  self.page_consultas.carregar_consultas,
            11: self.page_config.carregar_dados,
            12: self.page_usuarios.carregar_usuarios,
            13: self.page_chat_ia._atualizar_plano,
        }
        if indice in reload_map:
            try:
                reload_map[indice]()
            except RuntimeError:
                pass  # widget pode ter sido recriado; ignora com segurança
        for idx, btn in self._botoes.items():
            btn.setStyleSheet(_btn_style(idx == indice))

    def abrir_busca_global(self):
        dlg = BuscaGlobalDialog(self)
        dlg.navegar.connect(self.mudar_tela)
        dlg.exec()

    def abrir_alertas(self):
        dlg = PainelAlertas(self)
        dlg.exec()
        self.btn_alertas.atualizar_contagem()

    def _verificar_alertas_iniciais(self):
        # Apenas atualiza a contagem do botão de alertas (não abre janela automática).
        # A janela de início agora é a de Últimas Movimentações, mostrada após a varredura.
        try:
            self.btn_alertas.atualizar_contagem()
        except Exception:
            pass

    def fazer_logout(self):
        from PyQt6.QtWidgets import QMessageBox
        resp = QMessageBox.question(self, "Sair",
            "Deseja sair do sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            self.close()
            # Reinicia o processo para mostrar o login novamente
            import sys, os
            os.execl(sys.executable, sys.executable, *sys.argv)

    def _reaplicar_tema(self):
        self.sidebar.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_main']}; }}")
        for idx, btn in self._botoes.items():
            btn.setStyleSheet(_btn_style(idx == self._indice_atual))
        self.mudar_tela(self._indice_atual)
