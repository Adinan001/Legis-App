# teste_ia_isolado.py — Testa a chamada de IA dentro de uma QThread isolada
import sys, os, asyncio, faulthandler

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

faulthandler.enable(file=open("teste_fault.log", "w", buffering=1))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal


class TesteThread(QThread):
    resultado = pyqtSignal(bool, str)

    def run(self):
        print(">>> Thread iniciada", flush=True)
        try:
            print(">>> Importando google.genai...", flush=True)
            from google import genai
            print(">>> Import OK. Criando client...", flush=True)
            chave = input("COLE A CHAVE GEMINI AQUI E PRESSIONE ENTER: ") if False else os.environ.get("GEMINI_KEY", "")
            client = genai.Client(api_key=chave)
            print(">>> Client criado. Chamando generate_content...", flush=True)
            resp = client.models.generate_content(model="gemini-2.0-flash", contents="Diga OK")
            print(">>> Resposta recebida:", resp.text, flush=True)
            self.resultado.emit(True, resp.text)
        except Exception as e:
            print(">>> ERRO:", e, flush=True)
            self.resultado.emit(False, str(e))


app = QApplication(sys.argv)
win = QWidget()
win.setWindowTitle("Teste IA Isolado")
lay = QVBoxLayout(win)
lbl = QLabel("Clique para testar a chamada de IA em thread")
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
win.resize(400, 150)
win.show()
sys.exit(app.exec())
