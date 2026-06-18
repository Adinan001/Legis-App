# core/ai/aprendizado.py — Memória de preferências para a IA (Etapa 4)
"""
Gera um bloco de contexto a partir das avaliações de peças do advogado.
Esse contexto é injetado no prompt para que a IA:
  - priorize estruturas/abordagens das peças bem avaliadas (nota >= 4)
  - evite os problemas apontados nas peças mal avaliadas (nota <= 2)
Não re-treina o modelo: é aprendizado por contexto acumulado.
"""
from core.database import buscar_avaliacoes


def gerar_contexto_aprendizado(area=None, max_exemplos=5):
    """Monta o bloco de preferências do escritório com base nas avaliações."""
    # Peças bem avaliadas (prioridade para a mesma área, depois geral)
    boas = buscar_avaliacoes(filtro_area=area, nota_minima=4, limite=max_exemplos)
    if len(boas) < max_exemplos:
        extra = buscar_avaliacoes(nota_minima=4, limite=max_exemplos - len(boas))
        ids = {b["id"] for b in boas}
        boas += [e for e in extra if e["id"] not in ids]

    # Peças mal avaliadas (para evitar os mesmos erros)
    ruins = buscar_avaliacoes(nota_maxima=2, limite=3)

    if not boas and not ruins:
        return ""

    partes = ["## PREFERÊNCIAS DO ESCRITÓRIO (aprendizado das avaliações do advogado)"]

    if boas:
        partes.append("\n### Padrões APROVADOS (siga estas preferências):")
        for b in boas:
            linha = f"- Peça '{b['titulo']}' ({b.get('tipo_peca','')}, {b.get('area','')}) — nota {b['nota']}/5."
            if b.get("observacoes"):
                linha += f" Observação do advogado: {b['observacoes']}"
            partes.append(linha)

    if ruins:
        partes.append("\n### Padrões REJEITADOS (evite estes problemas):")
        for r in ruins:
            linha = f"- Peça '{r['titulo']}' recebeu nota baixa ({r['nota']}/5)."
            if r.get("observacoes"):
                linha += f" Problema apontado: {r['observacoes']}"
            partes.append(linha)

    partes.append("\nAplique as preferências aprovadas e evite os problemas rejeitados ao redigir.")
    return "\n".join(partes)


def tem_aprendizado():
    return bool(buscar_avaliacoes(limite=1))
