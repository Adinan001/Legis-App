# core/backup.py — Backup automático do banco de dados
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import sys

def _get_data_dir():
    if getattr(sys, "frozen", False):
        d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Legis")
    else:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.makedirs(d, exist_ok=True)
    return d

DB_PATH    = os.path.join(_get_data_dir(), "legis.db")
BACKUP_DIR = os.path.join(_get_data_dir(), "backups")


def garantir_pasta_backup():
    Path(BACKUP_DIR).mkdir(exist_ok=True)


def fazer_backup():
    """Copia o legis.db para a pasta backups com timestamp."""
    garantir_pasta_backup()
    if not os.path.exists(DB_PATH):
        return None, "Banco de dados não encontrado."
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_backup = f"legis_backup_{timestamp}.db"
    destino = os.path.join(BACKUP_DIR, nome_backup)
    
    try:
        shutil.copy2(DB_PATH, destino)
        _limpar_backups_antigos()
        return destino, None
    except Exception as e:
        return None, str(e)


def verificar_backup_hoje():
    """Verifica se já foi feito backup hoje."""
    garantir_pasta_backup()
    hoje = date.today().strftime("%Y%m%d")
    for arquivo in os.listdir(BACKUP_DIR):
        if arquivo.startswith(f"legis_backup_{hoje}") and arquivo.endswith(".db"):
            return True
    return False


def fazer_backup_automatico():
    """Faz backup automático uma vez por dia."""
    if not verificar_backup_hoje():
        caminho, erro = fazer_backup()
        return caminho, erro
    return None, "Backup já realizado hoje."


def listar_backups():
    """Lista todos os backups disponíveis."""
    garantir_pasta_backup()
    backups = []
    for arquivo in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if arquivo.endswith(".db"):
            caminho = os.path.join(BACKUP_DIR, arquivo)
            tamanho = os.path.getsize(caminho)
            data_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
            backups.append({
                "nome":    arquivo,
                "caminho": caminho,
                "tamanho": f"{tamanho / 1024:.1f} KB",
                "data":    data_mod.strftime("%d/%m/%Y %H:%M"),
            })
    return backups


def restaurar_backup(caminho_backup):
    """Restaura um backup substituindo o banco atual."""
    if not os.path.exists(caminho_backup):
        return False, "Arquivo de backup não encontrado."
    try:
        # Faz backup do banco atual antes de restaurar
        fazer_backup()
        shutil.copy2(caminho_backup, DB_PATH)
        return True, None
    except Exception as e:
        return False, str(e)


def _limpar_backups_antigos(manter=30):
    """Mantém apenas os N backups mais recentes."""
    garantir_pasta_backup()
    arquivos = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
        reverse=True
    )
    for arquivo in arquivos[manter:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, arquivo))
        except Exception:
            pass


def tamanho_banco():
    """Retorna o tamanho atual do banco em KB."""
    if os.path.exists(DB_PATH):
        return f"{os.path.getsize(DB_PATH) / 1024:.1f} KB"
    return "0 KB"
