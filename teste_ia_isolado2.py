# teste_ia_isolado2.py — Testa usando o GeminiProvider real do Legis
import sys, os, asyncio, faulthandler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

faulthandler.enable(file=open("teste_fault2.log", "w", buffering=1))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal


class TesteThread(QThread):
    resultado = pyqtSignal(bool, str)

    def run(self):
        print(">>> Thread iniciada", flush=True)
        try:
            print(">>> Importando providers...", flush=True)
            from core.ai.providers import GeminiProvider, testar_chave
            print(">>> Import OK.", flush=True)
            chave = os.environ.get("GEMINI_KEY", "")
            print(">>> Chamando testar_chave...", flush=True)
            ok, msg = testar_chave("gratuito", chave)
            print(">>> Resultado:", ok, msg, flush=True)
            self.resultado.emit(ok, msg)
        except Exception as e:
            print(">>> ERRO:", e, flush=True)
            self.resultado.emit(False, str(e))


app = QApplication(sys.argv)
win = QWidget()
win.setWindowTitle("Teste IA Isolado 2 — GeminiProvider real")
lay = QVBoxLayout(win)
lbl = QLabel("Clique para testar com GeminiProvider")
lbl.setWordWrap(True)
lay.addWidget(lbl)
btn = QPushButton("Testar")
lay.addWidget(btn)

def iniciar():
    print(">>> Botão clicado, iniciando thread...", flush=True)
    lbl.setText("Testando...")
    t = TesteThread()
    t.resultado.connect(lambda ok, msg: lbl.setText(f"{'OK' if ok else 'ERRO'}: {msg}"))
    win._thread = t
    t.start()

btn.clicked.connect(iniciar)
win.resize(450, 150)
win.show()
sys.exit(app.exec())
