# core/ai/realce.py — Processamento das marcações {{IA: ...}}
"""
A IA marca conteúdo gerado "de memória" (não vindo do acervo) com {{IA: ...}}.
Este módulo converte essas marcações em:
- Editor Qt: realce de fundo amarelo (via QTextCharFormat)
- Word: realce amarelo (highlight)
- Texto limpo: remove as marcações, mantendo só o conteúdo
"""
import re

PADRAO = re.compile(r"\{\{IA:\s*(.*?)\}\}", re.DOTALL)


def tem_marcacoes(texto):
    return bool(PADRAO.search(texto or ""))


def extrair_segmentos(texto):
    """
    Divide o texto em segmentos (trecho, eh_ia).
    Retorna lista de tuplas: (conteudo, True se for {{IA}}, False se normal).
    """
    segmentos = []
    pos = 0
    for m in PADRAO.finditer(texto):
        if m.start() > pos:
            segmentos.append((texto[pos:m.start()], False))
        segmentos.append((m.group(1), True))
        pos = m.end()
    if pos < len(texto):
        segmentos.append((texto[pos:], False))
    return segmentos


def texto_limpo(texto):
    """Remove as marcações {{IA: ...}}, mantendo o conteúdo (para salvar/editar)."""
    return PADRAO.sub(r"\1", texto or "")
