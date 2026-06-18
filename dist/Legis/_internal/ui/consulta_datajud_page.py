# ui/consulta_datajud_page.py
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QAbstractItemView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from config import COLORS, DATAJUD_API_KEY
from ui.widgets import btn_primario, campo_busca, label_titulo, estilo_tabela, separador_h
from ui.configuracoes_page import carregar_tribunais


class WorkerDatajud(QThread):
    sucesso = pyqtSignal(list)
    erro    = pyqtSignal(str)

    def __init__(self, numero_bruto, alias_tribunal):
        super().__init__()
        self.numero_bruto  = numero_bruto
        self.alias_tribunal = alias_tribunal

    def run(self):
        num_puro = self.numero_bruto.replace(".", "").replace("-", "").strip()
        if len(num_puro) != 20:
            self.erro.emit("O número CNJ deve ter exatamente 20 dígitos numéricos.")
            return

        url     = f"https://api-publica.datajud.cnj.jus.br/{self.alias_tribunal}/_search"
        headers = {"Authorization": f"APIKey {DATAJUD_API_KEY}", "Content-Type": "application/json"}
        payload = {"query": {"match": {"numeroProcesso": num_puro}}}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                hits = response.json().get("hits", {}).get("hits", [])
                if not hits:
                    self.erro.emit("Processo não localizado na base deste Tribunal.")
                    return
                movimentos = []
                for hit in hits:
                    fonte = hit.get("_source", {})
                    for mov in fonte.get("movimentos", []):
                        data_iso = mov.get("dataHora", "")
                        data_exib = data_iso
                        if "T" in data_iso:
                            partes = data_iso.split("T")
                            data_exib = "/".join(partes[0].split("-")[::-1]) + " " + partes[1][:5]
                        movimentos.append({
                            "data_iso":  data_iso,
                            "data":      data_exib,
                            "movimento": mov.get("nome", "Movimento não identificado"),
                            "detalhe":   fonte.get("orgaoJulgador", {}).get("nome", "—"),
                        })
                if movimentos:
                    movimentos.sort(key=lambda x: x["data_iso"], reverse=True)
                    self.sucesso.emit(movimentos)
                else:
                    self.erro.emit("Processo localizado, mas sem movimentações públicas.")
            else:
                self.erro.emit(f"CNJ recusou a requisição (HTTP {response.status_code}).")
        except requests.exceptions.Timeout:
            self.erro.emit("O servidor do CNJ demorou muito para responder.")
        except Exception as e:
            self.erro.emit(f"Falha de conexão: {str(e)}")


class ConsultaDatajudPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        layout.addWidget(label_titulo("Processos Automáticos"))
        sub = QLabel("Consulta em tempo real via API pública do CNJ — DataJud.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(sub)
        layout.addWidget(separador_h())

        busca_row = QHBoxLayout()
        busca_row.setSpacing(10)

        self.cb_tribunal = QComboBox()
        self._popular_tribunais()
        self.cb_tribunal.setStyleSheet(f"""
            QComboBox {{
                padding: 9px 12px; border: 1.5px solid {COLORS['border']};
                border-radius: 6px; background: white; font-size: 12px; min-width: 280px;
            }}
            QComboBox:focus {{ border-color: {COLORS['accent']}; }}
        """)

        self.txt_processo = campo_busca("Nº do processo. Ex: 1000742-40.2024.8.26.0269")
        self.txt_processo.returnPressed.connect(self.iniciar_busca)

        self.btn_buscar = btn_primario("⚡  Consultar Tribunal")
        self.btn_buscar.clicked.connect(self.iniciar_busca)

        busca_row.addWidget(self.cb_tribunal)
        busca_row.addWidget(self.txt_processo, 1)
        busca_row.addWidget(self.btn_buscar)
        layout.addLayout(busca_row)

        self.lbl_status = QLabel("Selecione o tribunal e informe o número do processo para consultar.")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        layout.addWidget(QLabel("<b>Histórico de Movimentações:</b>"))
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Data / Hora", "Movimento", "Órgão Judiciário"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(estilo_tabela())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _popular_tribunais(self):
        self.cb_tribunal.clear()
        for nome, alias in carregar_tribunais():
            self.cb_tribunal.addItem(nome, alias)

    def recarregar_tribunais(self):
        """Chamado pela MainWindow ao voltar para esta aba."""
        self._popular_tribunais()

    def iniciar_busca(self):
        entrada = self.txt_processo.text().strip()
        if len(entrada.replace(".", "").replace("-", "")) != 20:
            self._set_status("⚠️  O número do processo deve ter exatamente 20 dígitos.", "warning")
            return

        if self.worker and self.worker.isRunning():
            self.worker.quit(); self.worker.wait()

        self.table.setRowCount(0)
        trib = self.cb_tribunal.currentText().split("—")[0].strip()
        self._set_status(f"🔍  Consultando {trib}...", "info")
        self.btn_buscar.setEnabled(False)

        self.worker = WorkerDatajud(entrada, self.cb_tribunal.currentData())
        self.worker.sucesso.connect(self._exibir_resultados)
        self.worker.erro.connect(self._exibir_erro)
        self.worker.finished.connect(lambda: self.btn_buscar.setEnabled(True))
        self.worker.start()

    def _exibir_resultados(self, resultados):
        self.table.setRowCount(len(resultados))
        for i, item in enumerate(resultados):
            self.table.setItem(i, 0, QTableWidgetItem(item["data"]))
            self.table.setItem(i, 1, QTableWidgetItem(item["movimento"]))
            self.table.setItem(i, 2, QTableWidgetItem(item["detalhe"]))
        self._set_status(f"✅  {len(resultados)} movimentações encontradas.", "success")

    def _exibir_erro(self, msg):
        self.table.setRowCount(0)
        self._set_status(f"❌  {msg}", "danger")

    def _set_status(self, texto, tipo="info"):
        cores = {"info": COLORS["blue"], "success": COLORS["success"],
                 "warning": COLORS["warning"], "danger": COLORS["danger"]}
        self.lbl_status.setText(texto)
        self.lbl_status.setStyleSheet(f"color: {cores.get(tipo, COLORS['text_secondary'])}; font-size: 12px; font-weight: 600;")
