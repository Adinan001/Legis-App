# ui/atualizador_processos.py — Atualização automática dos processos monitorados
from PyQt6.QtCore import QThread, pyqtSignal


class AtualizadorProcessosThread(QThread):
    """
    Consulta o Datajud para todos os processos monitorados e atualiza o banco.
    Emite 'progresso' a cada processo e 'concluido' com a quantidade de novidades.
    """
    progresso = pyqtSignal(str)          # número do processo sendo atualizado
    concluido = pyqtSignal(list)         # lista de dicts dos processos com novidade

    def run(self):
        try:
            from core.database import (listar_processos_monitorados,
                                       atualizar_movimentacao_processo)
            from core.ai.runner import consultar_datajud_subprocess
        except Exception:
            self.concluido.emit([])
            return

        novidades_lista = []
        try:
            procs = listar_processos_monitorados()
        except Exception:
            self.concluido.emit([])
            return

        for p in procs:
            numero = p["numero_processo"]
            tribunal = p.get("tribunal", "")
            self.progresso.emit(numero)
            try:
                ok, resultado = consultar_datajud_subprocess(numero, tribunal, timeout=20)
                if ok and resultado:
                    ultima = resultado[0]
                    mov_nova = ultima["movimento"]
                    data_nova = ultima["data_iso"]
                    # Detecta novidade comparando com o que está salvo
                    houve_novidade = (p.get("ultima_movimentacao") != mov_nova or
                                      p.get("data_ultima_mov") != data_nova)
                    atualizar_movimentacao_processo(
                        numero, mov_nova, data_nova, tem_novidade=houve_novidade)
                    if houve_novidade:
                        novidades_lista.append({
                            "numero_processo": numero,
                            "tribunal": tribunal,
                            "cliente": p.get("cliente", ""),
                            "ultima_movimentacao": mov_nova,
                            "data_ultima_mov": data_nova,
                        })
            except Exception:
                continue  # se um falhar, segue os demais

        self.concluido.emit(novidades_lista)
