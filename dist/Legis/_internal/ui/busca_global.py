# ui/busca_global.py — Pesquisa global do sistema
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QKeySequence
from config import COLORS
from core.database import pesquisa_global


class BuscaGlobalDialog(QDialog):
    navegar = pyqtSignal(int)  # emite o índice da aba destino

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pesquisa Global")
        self.setMinimumSize(580, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_main']};
                border-radius: 12px;
            }}
        """)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Campo de busca
        cab = QWidget()
        cab.setStyleSheet(f"background: {COLORS['white']}; border-bottom: 1px solid {COLORS['border']};")
        cab_lay = QHBoxLayout(cab)
        cab_lay.setContentsMargins(20, 14, 20, 14)

        lbl_icone = QLabel("🔍")
        lbl_icone.setFont(QFont("Segoe UI", 16))
        cab_lay.addWidget(lbl_icone)

        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Buscar em processos, clientes, documentos e consultas...")
        self.txt_busca.setStyleSheet(f"""
            QLineEdit {{
                border: none; background: transparent;
                font-size: 14px; color: {COLORS['text_primary']};
                padding: 0 8px;
            }}
        """)
        self.txt_busca.textChanged.connect(self._buscar)
        cab_lay.addWidget(self.txt_busca)

        btn_fechar = QLabel("✕")
        btn_fechar.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; cursor: pointer;")
        btn_fechar.mousePressEvent = lambda _: self.reject()
        cab_lay.addWidget(btn_fechar)
        layout.addWidget(cab)

        # Resultados
        self.lista = QListWidget()
        self.lista.setStyleSheet(f"""
            QListWidget {{
                border: none; background: {COLORS['bg_main']};
                font-size: 12px; outline: none;
            }}
            QListWidget::item {{
                padding: 10px 20px;
                border-bottom: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['accent_light']};
                color: {COLORS['accent']};
            }}
            QListWidget::item:hover {{
                background: {COLORS['bg_main']};
            }}
        """)
        self.lista.itemDoubleClicked.connect(self._navegar)
        layout.addWidget(self.lista)

        # Rodapé de dica
        rod = QWidget()
        rod.setStyleSheet(f"background: {COLORS['white']}; border-top: 1px solid {COLORS['border']};")
        rod_lay = QHBoxLayout(rod)
        rod_lay.setContentsMargins(20, 8, 20, 8)
        lbl_dica = QLabel("↵  Abrir    Esc  Fechar")
        lbl_dica.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        rod_lay.addWidget(lbl_dica)
        layout.addWidget(rod)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._executar_busca)
        self._resultados_idx = []  # lista de (aba_idx, texto)

    def _buscar(self, texto):
        self._timer.stop()
        if len(texto) >= 2:
            self._timer.start(300)
        else:
            self.lista.clear()

    def _executar_busca(self):
        termo = self.txt_busca.text().strip()
        resultados = pesquisa_global(termo)
        self.lista.clear()
        self._resultados_idx = []

        def adicionar_secao(titulo, items, aba_idx, campo_principal, campo_sec=""):
            if not items: return
            # Header da seção
            item_header = QListWidgetItem(f"  {titulo}  ({len(items)} encontrado{'s' if len(items)>1 else ''})")
            item_header.setFlags(Qt.ItemFlag.NoItemFlags)
            item_header.setForeground(QColor(COLORS["accent"]))
            item_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.lista.addItem(item_header)
            self._resultados_idx.append(None)

            for it in items:
                principal = it.get(campo_principal, "")
                sec = f"  —  {it.get(campo_sec,'')}" if campo_sec and it.get(campo_sec) else ""
                item = QListWidgetItem(f"    {principal}{sec}")
                item.setData(Qt.ItemDataRole.UserRole, aba_idx)
                self.lista.addItem(item)
                self._resultados_idx.append(aba_idx)

        adicionar_secao("⚖️  PROCESSOS",  resultados["processos"],  1, "numero",  "cliente")
        adicionar_secao("👥  CLIENTES",   resultados["clientes"],   3, "nome",    "documento")
        adicionar_secao("📄  DOCUMENTOS", resultados["documentos"], 6, "titulo",  "categoria")
        adicionar_secao("💬  CONSULTAS",  resultados["consultas"],  8, "titulo",  "cliente")

        if self.lista.count() == 0:
            item_vazio = QListWidgetItem("  Nenhum resultado encontrado.")
            item_vazio.setFlags(Qt.ItemFlag.NoItemFlags)
            item_vazio.setForeground(QColor(COLORS["text_muted"]))
            self.lista.addItem(item_vazio)

    def _navegar(self, item):
        aba = item.data(Qt.ItemDataRole.UserRole)
        if aba is not None:
            self.navegar.emit(aba)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            items = self.lista.selectedItems()
            if items:
                self._navegar(items[0])
        else:
            super().keyPressEvent(event)
