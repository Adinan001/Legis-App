# core/datajud.py — Cliente reutilizável da API Datajud (CNJ)
"""
Consulta processos na API pública do Datajud.
Usado tanto pela tela de consulta quanto pela atualização automática.
"""
import requests
from config import DATAJUD_API_KEY


def consultar_processo(numero_bruto, alias_tribunal, timeout=15):
    """
    Consulta um processo no Datajud.
    Retorna (ok: bool, resultado: list[dict] | str de erro).
    Cada movimento: {data_iso, data, movimento, detalhe}
    """
    num_puro = numero_bruto.replace(".", "").replace("-", "").strip()
    if len(num_puro) != 20:
        return False, "O número CNJ deve ter exatamente 20 dígitos numéricos."

    url = f"https://api-publica.datajud.cnj.jus.br/{alias_tribunal}/_search"
    headers = {"Authorization": f"APIKey {DATAJUD_API_KEY}", "Content-Type": "application/json"}
    payload = {"query": {"match": {"numeroProcesso": num_puro}}}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code != 200:
            return False, f"CNJ recusou a requisição (HTTP {response.status_code})."
        hits = response.json().get("hits", {}).get("hits", [])
        if not hits:
            return False, "Processo não localizado na base deste Tribunal."

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
                    "data_iso": data_iso,
                    "data": data_exib,
                    "movimento": mov.get("nome", "Movimento não identificado"),
                    "detalhe": fonte.get("orgaoJulgador", {}).get("nome", "—"),
                })
        if not movimentos:
            return False, "Processo localizado, mas sem movimentações públicas."
        movimentos.sort(key=lambda x: x["data_iso"], reverse=True)
        return True, movimentos
    except requests.exceptions.Timeout:
        return False, "O servidor do CNJ demorou muito para responder."
    except Exception as e:
        return False, f"Falha de conexão: {str(e)}"
