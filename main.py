# main.py — Legis Beta com Login
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Se chamado como worker de IA (subprocess), executa só o worker e sai.
# Isso permite que o .exe compilado seja reusado como worker isolado.
if "--run-ai-worker" in sys.argv:
    from core.ai.worker_subprocess import main as _worker_main
    _worker_main()
    sys.exit(0)

if "--run-rag-worker" in sys.argv:
    from core.ai.rag_worker import main as _rag_main
    _rag_main()
    sys.exit(0)

if "--run-export-worker" in sys.argv:
    from core.ai.export_worker import main as _export_main
    _export_main()
    sys.exit(0)

if "--run-datajud-worker" in sys.argv:
    from core.datajud_worker import main as _datajud_main
    _datajud_main()
    sys.exit(0)

import asyncio
# Correção para crash silencioso com bibliotecas de rede (httpx/asyncio)
# rodando em threads separadas no Windows com PyQt6
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

import traceback
import faulthandler

# Captura crashes nativos (segfault/access violation) que não geram exceção Python
_log_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    _log_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Legis')
os.makedirs(_log_dir, exist_ok=True)
_fault_file = open(os.path.join(_log_dir, 'legis_fault.log'), 'w', buffering=1)
faulthandler.enable(file=_fault_file)

def _log_excecao(tipo, valor, tb):
    """Registra qualquer exceção não tratada em legis_error.log."""
    if getattr(sys, 'frozen', False):
        log_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Legis')
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'legis_error.log')
    with open(log_path, 'a', encoding='utf-8') as f:
        from datetime import datetime
        f.write(f"\n--- {datetime.now()} ---\n")
        traceback.print_exception(tipo, valor, tb, file=f)
    traceback.print_exception(tipo, valor, tb)

sys.excepthook = _log_excecao

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
from core.database import (inicializar_banco, inicializar_consultas,
                           migrar_etapa1, inicializar_doutrina,
                           migrar_etapa2, migrar_etapa3, migrar_etapa4, migrar_etapa5, migrar_monitoramento, inicializar_usuarios)
from core.backup import fazer_backup_automatico
from ui.splash import SplashScreen
from ui.login import LoginWindow
from ui.main_window import MainWindow


def main():
    # Estabilização do garbage collector para PyQt:
    # aumenta drasticamente os limiares para o GC não coletar objetos Qt
    # em momentos delicados (causa de crashes "wrapped C/C++ object deleted")
    import gc
    gc.disable()  # desliga a coleta automática; objetos ainda são liberados ao sair

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QToolTip { background-color: #1C2B1E; color: white; border: none;
                   padding: 5px 8px; border-radius: 4px; font-size: 11px; }
        QScrollArea { border: none; }
        QSplitter::handle { background-color: #D6DDD7; width: 1px; }
    """)

    # Splash
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    try:
        inicializar_banco()
        inicializar_consultas()
        migrar_etapa1()
        inicializar_doutrina()
        migrar_etapa2()
        migrar_etapa3()
        migrar_etapa4()
        migrar_etapa5()
        migrar_monitoramento()
        inicializar_usuarios()
        fazer_backup_automatico()
    except Exception as e:
        splash.close()
        QMessageBox.critical(None, "Erro crítico", f"Erro ao inicializar:\n{e}")
        sys.exit(1)

    def abrir_login():
        splash.close()

        # Tela de login
        login_dlg = LoginWindow()
        if login_dlg.exec() != LoginWindow.DialogCode.Accepted:
            sys.exit(0)

        usuario = login_dlg.get_usuario()
        if not usuario:
            sys.exit(0)

        # Abre a janela principal com o usuário autenticado
        window = MainWindow(usuario=usuario)
        window.show()

    QTimer.singleShot(2500, abrir_login)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
