# ui/avaliar_peca_dialog.py — Diálogo de avaliação de peça (nota + observações)
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QPushButton, QFrame, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config import COLORS
from ui.widgets import btn_primario, btn_secundario, separador_h, estilo_dialog


class EstrelaWidget(QWidget):
    """Seletor de nota 1-5 com estrelas clicáveis."""
    nota_mudou = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nota = 0
        self._botoes = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for i in range(1, 6):
            b = QPushButton("☆")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedSize(48, 48)
            b.setStyleSheet(self._estilo(False))
            b.clicked.connect(lambda _, n=i: self.set_nota(n))
            self._botoes.append(b)
            lay.addWidget(b)

    def _estilo(self, ativa):
        cor = COLORS["accent"] if ativa else COLORS["border"]
        return f"""
            QPushButton {{
                font-size: 32px; border: none; background: transparent;
                color: {cor};
            }}
            QPushButton:hover {{ color: {COLORS['accent']}; }}
        """

    def set_nota(self, nota):
        self._nota = nota
        for i, b in enumerate(self._botoes):
            ativa = (i < nota)
            b.setText("★" if ativa else "☆")
            b.setStyleSheet(self._estilo(ativa))
        self.nota_mudou.emit(nota)

    def nota(self):
        return self._nota


class AvaliarPecaDialog(QDialog):
    def __init__(self, parent=None, titulo_peca="", nota_atual=0, obs_atual=""):
        super().__init__(parent)
        self.setWindowTitle("Avaliar Peça")
        self.setMinimumWidth(480)
        self.setStyleSheet(estilo_dialog())
        self.init_ui(titulo_peca, nota_atual, obs_atual)

    def init_ui(self, titulo_peca, nota_atual, obs_atual):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        titulo = QLabel("⭐  Avaliar Peça Gerada")
        titulo.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(titulo)

        if titulo_peca:
            sub = QLabel(f"📄 {titulo_peca}")
            sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            sub.setWordWrap(True)
            layout.addWidget(sub)

        layout.addWidget(separador_h())

        # Explicação
        info = QLabel(
            "Sua avaliação ajuda a IA a aprender. Peças com nota alta (4-5) viram "
            "modelo para as próximas; peças com nota baixa (1-2) indicam o que evitar.")
        info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Estrelas
        lbl_nota = QLabel("Sua nota:")
        lbl_nota.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600; border: none;")
        lbl_nota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_nota)

        self.estrelas = EstrelaWidget()
        layout.addWidget(self.estrelas)

        self.lbl_nota_texto = QLabel("")
        self.lbl_nota_texto.setStyleSheet(f"color: {COLORS['accent']}; font-size: 12px; font-weight: 700; border: none;")
        self.lbl_nota_texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_nota_texto)
        self.estrelas.nota_mudou.connect(self._atualizar_texto_nota)

        # Observações
        lbl_obs = QLabel("Observações (opcional):")
        lbl_obs.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 600; border: none;")
        layout.addWidget(lbl_obs)

        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText(
            "O que achou boa ou ruim? Ex: 'Fundamentação excelente, mas faltou citar o art. X' "
            "ou 'Estrutura de pedidos ficou perfeita'")
        self.txt_obs.setMaximumHeight(120)
        self.txt_obs.setStyleSheet(f"""
            QTextEdit {{ padding: 10px; border: 1.5px solid {COLORS['border']};
                border-radius: 8px; background: white; font-size: 12px;
                color: {COLORS['text_primary']}; }}
            QTextEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        layout.addWidget(self.txt_obs)

        # Pré-preencher se já houver avaliação
        if nota_atual:
            self.estrelas.set_nota(nota_atual)
        if obs_atual:
            self.txt_obs.setPlainText(obs_atual)

        # Botões
        botoes = QHBoxLayout()
        botoes.addStretch()
        btn_cancelar = btn_secundario("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)
        self.btn_salvar = btn_primario("💾  Salvar Avaliação")
        self.btn_salvar.clicked.connect(self._validar)
        botoes.addWidget(self.btn_salvar)
        layout.addLayout(botoes)

    def _atualizar_texto_nota(self, nota):
        textos = {1: "❌ Ruim", 2: "⚠️ Fraca", 3: "➖ Regular",
                  4: "✔️ Boa", 5: "⭐ Excelente"}
        self.lbl_nota_texto.setText(textos.get(nota, ""))

    def _validar(self):
        if self.estrelas.nota() == 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Nota obrigatória", "Selecione uma nota de 1 a 5 estrelas.")
            return
        self.accept()

    def obter_dados(self):
        return {
            "nota": self.estrelas.nota(),
            "observacoes": self.txt_obs.toPlainText().strip(),
        }
