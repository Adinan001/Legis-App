# ui/main_window.py — Legis Beta
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
from ui.busca_global          import BuscaGlobalDialog
from ui.alertas_widget        import BotaoAlertas, PainelAlertas

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
]
MENU_RODAPE = [
    ("⚙️",  "Configurações",     11),
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
    def __init__(self):
        super().__init__()
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

        # Marca
        self.lbl_marca = QLabel(APP_NAME)
        self.lbl_marca.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        self.lbl_marca.setStyleSheet("color: white; padding-left: 6px;")
        sb.addWidget(self.lbl_marca)
        lbl_beta = QLabel("Beta")
        lbl_beta.setFont(QFont("Segoe UI", 9))
        lbl_beta.setStyleSheet(f"color: {COLORS['accent']}; padding-left: 6px; font-weight: 700;")
        sb.addWidget(lbl_beta)
        sb.addSpacing(8)

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

        # Botão de alertas
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
            sb.addWidget(btn)

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
        ]:
            self.stack.addWidget(page)

        self._root.addWidget(self.stack)
        self.mudar_tela(0)


    def mudar_tela(self, indice):
        self._indice_atual = indice
        self.stack.setCurrentIndex(indice)
        reload_map = {
            0:  self.page_dashboard.atualizar_dados,
            1:  self.page_processos.carregar_dados_processos,
            3:  self.page_clientes.carregar_dados_clientes,
            4:  self.page_financeiro.carregar_dados_financeiros,
            5:  self.page_agenda.carregar_dados_agenda,
            6:  self.page_documentos.carregar_documentos,
            9:  self.page_consultas.carregar_consultas,
            11: self.page_config.carregar_dados,
        }
        if indice in reload_map:
            reload_map[indice]()
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
        """Abre o painel de alertas automaticamente se houver prazos urgentes."""
        from core.database import buscar_resumo_alertas
        resumo = buscar_resumo_alertas()
        if resumo["total"] > 0:
            self.btn_alertas.atualizar_contagem()
            dlg = PainelAlertas(self)
            dlg.exec()

    def _reaplicar_tema(self):
        self.sidebar.setStyleSheet(f"background-color: {COLORS['bg_sidebar']};")
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_main']}; }}")
        for idx, btn in self._botoes.items():
            btn.setStyleSheet(_btn_style(idx == self._indice_atual))
        self.mudar_tela(self._indice_atual)
