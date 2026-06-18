# core/ai/agentes.py — Sistema Multi-Agente (Etapa 6)
"""
Orquestra 5 agentes especializados que trabalham em sequência para gerar
uma peça jurídica de alta qualidade:

  1. Estratégico    — define a tese central e a linha argumentativa
  2. Jurisprudência — seleciona acórdãos do acervo (RAG) e sugere outros
  3. Doutrina       — seleciona fundamentos teóricos do acervo e sugere outros
  4. Redator        — escreve a peça completa no padrão forense
  5. Revisor        — revisa, aplica checklist e refina

Conteúdo vindo do acervo (RAG) é confiável.
Conteúdo "de memória" da IA é marcado com {{IA: ...}} para receber realce amarelo.
"""
import json


# Prompts de cada agente
PROMPT_ESTRATEGICO = """Você é o ADVOGADO ESTRATEGISTA do escritório. Sua função é analisar o caso e definir a estratégia jurídica ANTES da redação.

Com base no tipo de peça, área e fatos fornecidos, defina:
1. A TESE CENTRAL (a principal linha de defesa/ataque)
2. As TESES SECUNDÁRIAS de apoio
3. Os PONTOS DE ATENÇÃO (riscos, fragilidades a contornar)
4. A ESTRUTURA recomendada de seções da peça

Responda de forma objetiva e técnica, em tópicos. Esta análise guiará os demais especialistas."""

PROMPT_JURISPRUDENCIA = """Você é o PESQUISADOR DE JURISPRUDÊNCIA do escritório. Recebeu a estratégia do caso e o acervo de jurisprudência disponível.

Sua função:
1. Selecionar do ACERVO FORNECIDO as decisões mais relevantes para a tese (cite tribunal, número, com referência completa).
2. Se o acervo for insuficiente, SUGERIR jurisprudência pertinente do seu conhecimento — mas marque CADA sugestão própria assim: {{IA: <a sugestão>}}.

Conteúdo do acervo = sem marcação. Conteúdo seu (de memória) = sempre dentro de {{IA: ...}}.
Organize por tese. Seja preciso — nunca invente números de acórdão sem marcar como {{IA: ...}}."""

PROMPT_DOUTRINA = """Você é o PESQUISADOR DE DOUTRINA do escritório. Recebeu a estratégia do caso e o acervo de doutrina disponível.

Sua função:
1. Selecionar do ACERVO FORNECIDO os fundamentos teóricos que sustentam a tese (autor, obra).
2. Se o acervo for insuficiente, SUGERIR doutrina pertinente do seu conhecimento — mas marque CADA sugestão própria assim: {{IA: <a sugestão>}}.

Conteúdo do acervo = sem marcação. Conteúdo seu (de memória) = sempre dentro de {{IA: ...}}."""

PROMPT_REDATOR = """Você é o REDATOR FORENSE do escritório. Recebeu a estratégia, a jurisprudência e a doutrina selecionadas. Sua função é redigir a PEÇA COMPLETA no padrão forense brasileiro.

REGRAS CRÍTICAS:
- Siga o padrão de estrutura, formatação e fecho do escritório (endereçamento, qualificação, seções romanas, pedidos, valor da causa, fecho, rol de documentos).
- Use a jurisprudência e doutrina fornecidas na fundamentação.
- Preserve INTEGRALMENTE as marcações {{IA: ...}} que vierem da jurisprudência/doutrina — NÃO as remova. Se você mesmo adicionar algo de memória que não está no acervo, marque também com {{IA: ...}}.
- Conteúdo confiável (do acervo + dados do caso) = texto normal.
- Conteúdo de memória/sugestão = dentro de {{IA: ...}}.
Entregue a peça pronta para revisão."""

PROMPT_REVISOR = """Você é o REVISOR SÊNIOR do escritório. Recebeu a peça redigida. Sua função é revisar e refinar SEM descaracterizar o trabalho.

Verifique e corrija:
- Checklist: endereçamento, qualificação completa das partes, valor da causa, pedidos numerados, fundamentação, fecho com assinatura/OAB.
- Coerência entre fatos, fundamentos e pedidos.
- Clareza e técnica da redação.

REGRA CRÍTICA: preserve TODAS as marcações {{IA: ...}} exatamente onde estão — elas indicam conteúdo a ser verificado pelo advogado. Não remova nem adicione marcações indevidamente.

Entregue a VERSÃO FINAL da peça, completa e revisada. Responda APENAS com a peça final, sem comentários seus."""


class OrquestradorAgentes:
    """Coordena a execução sequencial dos agentes."""

    def __init__(self, plano, api_key, system_prompt_base, callback_progresso=None):
        self.plano = plano
        self.api_key = api_key
        self.system_base = system_prompt_base
        self.callback = callback_progresso  # função(nome_agente, status)
        self._resultados = {}

    def _notificar(self, agente, status):
        if self.callback:
            try:
                self.callback(agente, status)
            except Exception:
                pass

    def _chamar(self, system, prompt, max_tokens=4096, timeout=120):
        from core.ai.runner import chamar_ia
        ok, resultado = chamar_ia(self.plano, self.api_key, prompt, system,
                                  max_tokens=max_tokens, timeout=timeout, usar_fallback=True)
        if not ok:
            raise RuntimeError(resultado)
        return resultado

    def gerar(self, tipo_peca, dados_caso, contexto_juris="", contexto_doutrina=""):
        """Executa o pipeline completo dos 5 agentes. Retorna a peça final."""
        area = dados_caso.get("area", "")
        fatos = dados_caso.get("fatos", "")
        partes = dados_caso.get("partes", "")
        pedidos = dados_caso.get("pedidos", "")

        resumo_caso = (f"Tipo de peça: {tipo_peca}\nÁrea: {area}\n"
                       f"Partes: {partes}\nFatos: {fatos}\nPedidos: {pedidos}")

        # 1) ESTRATÉGICO
        self._notificar("estrategico", "trabalhando")
        estrategia = self._chamar(
            self.system_base + "\n\n" + PROMPT_ESTRATEGICO,
            f"## CASO\n{resumo_caso}\n\nDefina a estratégia jurídica.",
            max_tokens=1500, timeout=90)
        self._resultados["estrategia"] = estrategia
        self._notificar("estrategico", "concluido")

        # 2) JURISPRUDÊNCIA
        self._notificar("jurisprudencia", "trabalhando")
        acervo_j = contexto_juris if contexto_juris else "(acervo de jurisprudência vazio)"
        juris = self._chamar(
            self.system_base + "\n\n" + PROMPT_JURISPRUDENCIA,
            f"## ESTRATÉGIA\n{estrategia}\n\n## ACERVO DE JURISPRUDÊNCIA\n{acervo_j}\n\n"
            f"## CASO\n{resumo_caso}\n\nSelecione/sugira a jurisprudência.",
            max_tokens=1500, timeout=90)
        self._resultados["jurisprudencia"] = juris
        self._notificar("jurisprudencia", "concluido")

        # 3) DOUTRINA
        self._notificar("doutrina", "trabalhando")
        acervo_d = contexto_doutrina if contexto_doutrina else "(acervo de doutrina vazio)"
        doutrina = self._chamar(
            self.system_base + "\n\n" + PROMPT_DOUTRINA,
            f"## ESTRATÉGIA\n{estrategia}\n\n## ACERVO DE DOUTRINA\n{acervo_d}\n\n"
            f"## CASO\n{resumo_caso}\n\nSelecione/sugira a doutrina.",
            max_tokens=1200, timeout=90)
        self._resultados["doutrina"] = doutrina
        self._notificar("doutrina", "concluido")

        # 4) REDATOR
        self._notificar("redator", "trabalhando")
        peca = self._chamar(
            self.system_base + "\n\n" + PROMPT_REDATOR,
            f"## ESTRATÉGIA\n{estrategia}\n\n## JURISPRUDÊNCIA SELECIONADA\n{juris}\n\n"
            f"## DOUTRINA SELECIONADA\n{doutrina}\n\n## DADOS DO CASO\n{resumo_caso}\n\n"
            f"Redija a peça completa.",
            max_tokens=8192, timeout=180)
        self._resultados["peca_rascunho"] = peca
        self._notificar("redator", "concluido")

        # 5) REVISOR
        self._notificar("revisor", "trabalhando")
        peca_final = self._chamar(
            self.system_base + "\n\n" + PROMPT_REVISOR,
            f"## PEÇA A REVISAR\n{peca}\n\nEntregue a versão final revisada.",
            max_tokens=8192, timeout=180)
        self._resultados["peca_final"] = peca_final
        self._notificar("revisor", "concluido")

        return {
            "peca": peca_final,
            "estrategia": estrategia,
            "resultados": self._resultados,
        }
