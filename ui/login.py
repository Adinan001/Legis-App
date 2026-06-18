# ui/login.py — Tela de login corrigida
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QCheckBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from config import COLORS, APP_NAME, APP_VERSION
from core.database import autenticar, get_logo_escritorio, buscar_configuracoes


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Login")
        self.setFixedSize(420, 560)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("QDialog { background: #0D1810; }")
        self._usuario = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── TOPO escuro com logo ──────────────────────────
        topo = QWidget()
        topo.setStyleSheet("background: #0D1810;")
        topo.setFixedHeight(200)
        topo_lay = QVBoxLayout(topo)
        topo_lay.setContentsMargins(40, 24, 40, 16)
        topo_lay.setSpacing(10)
        topo_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setFixedSize(100, 100)
        self.lbl_logo.setStyleSheet("border: none; background: transparent;")
        self._carregar_logo()
        topo_lay.addWidget(self.lbl_logo, alignment=Qt.AlignmentFlag.AlignCenter)

        # Nome do escritório
        cfg = buscar_configuracoes()
        nome_esc = cfg.get("nome_escritorio", APP_NAME)
        lbl_nome = QLabel(nome_esc)
        lbl_nome.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_nome.setStyleSheet("color: #C8A96E; border: none; background: transparent;")
        lbl_nome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_nome.setWordWrap(True)
        topo_lay.addWidget(lbl_nome)

        layout.addWidget(topo)

        # ── FORMULÁRIO branco ────────────────────────────
        form_widget = QWidget()
        form_widget.setStyleSheet(f"background: {COLORS['white']};")
        form_lay = QVBoxLayout(form_widget)
        form_lay.setContentsMargins(40, 28, 40, 28)
        form_lay.setSpacing(10)

        lbl_acesso = QLabel("Acesse sua conta")
        lbl_acesso.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_acesso.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        form_lay.addWidget(lbl_acesso)
        form_lay.addSpacing(6)

        # Campo usuário
        lbl_u = QLabel("Usuário")
        lbl_u.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600; border: none;")
        form_lay.addWidget(lbl_u)
        self.txt_login = QLineEdit()
        self.txt_login.setPlaceholderText("Digite seu usuário")
        self.txt_login.setFixedHeight(44)
        self.txt_login.setStyleSheet(self._estilo_campo())
        form_lay.addWidget(self.txt_login)

        form_lay.addSpacing(4)

        # Campo senha
        lbl_s = QLabel("Senha")
        lbl_s.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600; border: none;")
        form_lay.addWidget(lbl_s)
        self.txt_senha = QLineEdit()
        self.txt_senha.setPlaceholderText("Digite sua senha")
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_senha.setFixedHeight(44)
        self.txt_senha.setStyleSheet(self._estilo_campo())
        self.txt_senha.returnPressed.connect(self.fazer_login)
        form_lay.addWidget(self.txt_senha)

        # Mostrar senha
        self.cb_mostrar = QCheckBox("Mostrar senha")
        self.cb_mostrar.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        self.cb_mostrar.toggled.connect(
            lambda v: self.txt_senha.setEchoMode(
                QLineEdit.EchoMode.Normal if v else QLineEdit.EchoMode.Password))
        form_lay.addWidget(self.cb_mostrar)

        form_lay.addSpacing(10)

        # Botão entrar
        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.setFixedHeight(46)
        self.btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_entrar.setStyleSheet("""
            QPushButton {
                background: #1C2B1E;
                color: #C8A96E;
                font-size: 14px;
                font-weight: 700;
                border-radius: 8px;
                border: 2px solid #C8A96E50;
                letter-spacing: 1px;
            }
            QPushButton:hover { background: #2E4A32; border-color: #C8A96E; }
            QPushButton:pressed { background: #0D1810; }
        """)
        self.btn_entrar.clicked.connect(self.fazer_login)
        form_lay.addWidget(self.btn_entrar)

        # Mensagem de erro
        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px; border: none;")
        self.lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_lay.addWidget(self.lbl_erro)

        layout.addWidget(form_widget)

        # ── RODAPÉ ───────────────────────────────────────
        rodape = QWidget()
        rodape.setStyleSheet("background: #0A0F0B;")
        rodape.setFixedHeight(36)
        rod_lay = QHBoxLayout(rodape)
        rod_lay.setContentsMargins(20, 0, 20, 0)
        lbl_ver = QLabel(f"Legis {APP_VERSION}")
        lbl_ver.setStyleSheet("color: #3A5A3C; font-size: 10px; border: none;")
        rod_lay.addWidget(lbl_ver)
        rod_lay.addStretch()
        lbl_dev = QLabel("Lima & Paixão Advocacia")
        lbl_dev.setStyleSheet("color: #3A5A3C; font-size: 10px; border: none;")
        rod_lay.addWidget(lbl_dev)
        layout.addWidget(rodape)

    def _carregar_logo(self):
        # Tenta logo do escritório primeiro
        logo_path = get_logo_escritorio()
        if logo_path and os.path.exists(logo_path):
            self._aplicar_logo_nitido(logo_path)
            return

        # Fallback: ícone do Legis
        for ico in ["legis.ico", "icon.png", "splash.png"]:
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ico)
            if os.path.exists(ico_path):
                self._aplicar_logo_nitido(ico_path)
                return

        # Fallback texto
        self.lbl_logo.setText("⚖️")
        self.lbl_logo.setFont(QFont("Segoe UI", 42))
        self.lbl_logo.setStyleSheet("color: #C8A96E; border: none; background: transparent;")

    def _aplicar_logo_nitido(self, caminho):
        """Carrega o logo em alta resolução, respeitando o DPI da tela (sem borrar)."""
        tamanho = self.lbl_logo.width()  # tamanho lógico do label
        # Fator de escala da tela (ex: 1.25, 1.5, 2.0 em telas HiDPI)
        try:
            dpr = self.devicePixelRatioF() or 1.0
        except Exception:
            dpr = 1.0
        pix = QPixmap(caminho)
        if pix.isNull():
            return
        # Renderiza no tamanho físico real (tamanho lógico x escala), depois
        # informa ao Qt o device pixel ratio para exibir nítido
        alvo = int(tamanho * dpr)
        pix = pix.scaled(
            alvo, alvo,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        pix.setDevicePixelRatio(dpr)
        self.lbl_logo.setPixmap(pix)

    def _estilo_campo(self):
        return f"""
            QLineEdit {{
                padding: 10px 14px;
                border: 1.5px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['bg_main']};
                font-size: 13px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: #1C2B1E;
                background: white;
            }}
        """

    def fazer_login(self):
        login = self.txt_login.text().strip()
        senha = self.txt_senha.text()
        if not login or not senha:
            self.lbl_erro.setText("Preencha usuário e senha.")
            return
        usuario = autenticar(login, senha)
        if usuario:
            self._usuario = usuario
            self.accept()
        else:
            self.lbl_erro.setText("Usuário ou senha incorretos.")
            self.txt_senha.clear()
            self.txt_senha.setFocus()

    def get_usuario(self):
        return self._usuario