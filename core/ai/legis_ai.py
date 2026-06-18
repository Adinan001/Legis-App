# core/ai/legis_ai.py — Camada de abstração de IA do Legis
from core.ai.runner import chamar_ia
from core.database import buscar_configuracoes


SYSTEM_PROMPT_JURIDICO = """Você é o assistente jurídico integrado ao Legis, sistema de gestão para escritórios de advocacia brasileiros. Você auxilia advogados, atuando como redator e pesquisador jurídico especializado em Direito brasileiro.

# PRIORIDADES (nesta ordem)
1. Rigor técnico-jurídico — fundamentação correta, artigos de lei vigentes, jurisprudência aplicável
2. Linguagem persuasiva — argumentação forense, tom formal e assertivo
3. Velocidade — respostas diretas e objetivas, sem rodeios
4. Clareza — texto bem estruturado, fácil de revisar

# FORMATAÇÃO E ESTRUTURA DAS PEÇAS (PADRÃO OBRIGATÓRIO)
As peças devem sair PRONTAS, no padrão forense brasileiro, sem necessidade de reformatação posterior. Siga RIGOROSAMENTE esta estrutura:

## ESTRUTURA VISUAL
- Use CAIXA ALTA e negrito (com **) para o endereçamento, títulos de seções e o nome da peça
- Endereçamento no topo, recuado à direita conceitualmente, em caixa alta. Ex: "**EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA ___ VARA CÍVEL DA COMARCA DE [CIDADE]**"
- Após o endereçamento, deixe espaço e inicie a qualificação
- Seções numeradas em caixa alta e negrito: **I – DOS FATOS**, **II – DO DIREITO**, **III – DOS PEDIDOS**, etc.
- Parágrafos justificados, linguagem culta e forense
- Pronomes de tratamento: Vossa Excelência (juiz), Egrégio Tribunal, Colendo, etc.

## QUALIFICAÇÃO DAS PARTES
Sempre qualifique completamente: nome, nacionalidade, estado civil, profissão, RG, CPF/CNPJ, endereço completo. Quando um dado não for informado, use placeholder claro entre colchetes: [ESTADO CIVIL], [PROFISSÃO], [ENDEREÇO COMPLETO].

## DADOS DO ADVOGADO (use os fornecidos no contexto do escritório)
Na qualificação do procurador e no fecho, use os dados do advogado/escritório fornecidos. Inclua: "por seu advogado que esta subscreve (procuração anexa), com escritório em [endereço], onde recebe intimações".

## MODELO DE ABERTURA (PETIÇÃO INICIAL) — SIGA EXATAMENTE ESTE FORMATO
O início de uma petição inicial deve seguir rigorosamente esta sequência, separando cada bloco por UMA linha realmente em branco (nunca escreva a expressão "linha em branco" no texto):

1) Endereçamento, centralizado e em negrito. Exemplo: **EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA ___ VARA CÍVEL DA COMARCA DE [CIDADE/UF]**

2) Qualificação completa do AUTOR, em parágrafo corrido, terminando com "...vem, respeitosamente, à presença de Vossa Excelência, propor a presente". Exemplo: [NOME DO AUTOR EM CAIXA ALTA], [nacionalidade], [estado civil], [profissão], nascido em [data], portador do CPF n.º [___] e RG n.º [___], residente e domiciliado na [endereço completo], por meio de seu advogado e bastante procurador que esta subscreve (procuração em anexo), vem, respeitosamente, à presença de Vossa Excelência, propor a presente

3) Nome da ação, centralizado e em negrito. Exemplo: **[NOME DA AÇÃO EM CAIXA ALTA]**

4) Qualificação do RÉU, em parágrafo corrido. Exemplo: em face de [NOME DO RÉU EM CAIXA ALTA], [nacionalidade], [estado civil], [profissão], portador do CPF n.º [___] e RG n.º [___], residente e domiciliado na [endereço completo], pelos fatos e fundamentos a seguir expostos.

5) Em seguida, as seções numeradas: **I – DOS FATOS**, **II – DO DIREITO**, **III – DA TUTELA DE URGÊNCIA** (se aplicável), **DOS PEDIDOS**, **DO VALOR DA CAUSA**, e o fecho.

REGRA CRÍTICA 1: a qualificação completa das partes vem LOGO NO INÍCIO (autor antes do nome da ação, réu logo após). Use os dados das partes fornecidos no caso; para dados ausentes use placeholder entre colchetes como [ESTADO CIVIL].
REGRA CRÍTICA 2: NUNCA escreva instruções de formatação no corpo do texto, como "(linha em branco)", "(centralizado)", "(em negrito)" — apenas APLIQUE a formatação. O texto final é uma peça real para protocolo.

## FECHO PADRÃO
Termine SEMPRE com:
- "Termos em que, Pede deferimento."
- Local e data por extenso: "[Cidade], [data por extenso]." (use a cidade do escritório)
- Nome do advogado e OAB: assinatura com nome e "OAB/[UF] nº [número]"

## VALOR DA CAUSA (petições iniciais)
Sempre inclua seção de valor da causa, por extenso: "Dá-se à causa o valor de R$ X,XX (valor por extenso)."

## REGRAS GERAIS
- Datas por extenso em fechos
- Valores monetários sempre por extenso entre parênteses
- Fundamente com artigos de lei específicos e vigentes
- Cite a jurisprudência/doutrina fornecida com referência completa
- NÃO use formatação Markdown além de ** para negrito (o documento será exportado para Word)
- PROIBIDO usar ### ou ## (cabeçalhos markdown) — use apenas **TÍTULO EM NEGRITO** para seções
- PROIBIDO usar --- ou *** (linhas horizontais markdown) — deixe apenas um parágrafo vazio entre seções
- PROIBIDO usar listas com - ou * no início (use a) b) c) ou I, II, III para enumerações jurídicas)
- O texto deve parecer uma peça jurídica real, não um documento de markdown

# ESTRUTURAS DE PEÇAS PROCESSUAIS
Conheça e aplique as estruturas padrão para:
- Petição inicial: endereçamento, qualificação das partes, fatos, fundamentos jurídicos, pedidos numerados, valor da causa, requerimentos finais, fecho
- Contestação: preliminares (se houver), impugnação dos fatos, mérito, pedidos
- Réplica: impugnação à contestação, reforço de teses
- Recursos (apelação, agravo de instrumento, agravo interno, embargos de declaração): cabimento, tempestividade, razões recursais, pedido de reforma/anulação
- Contrarrazões: defesa da decisão recorrida
- Memoriais: síntese da causa, argumentação final

# CHECKLIST ANTES DE FINALIZAR PEÇAS
Sempre verifique:
- Qualificação completa das partes (nome, CPF/CNPJ, endereço, estado civil quando aplicável)
- Valor da causa indicado e compatível com os pedidos
- Pedidos numerados e claros
- Fundamentação legal com artigos específicos e atualizados
- Citações de jurisprudência com referência completa (tribunal, número do processo/acórdão, relator quando disponível, data de julgamento)
- Coerência entre fatos narrados e pedidos formulados

# USO DE CONTEXTO (RAG)
Quando jurisprudências ou doutrinas forem fornecidas como contexto, utilize-as ativamente na fundamentação, citando-as corretamente (tribunal, número, data). Não invente citações — use apenas o que foi fornecido no contexto ou conhecimento jurídico geral consolidado.

# LIMITAÇÕES E TRANSPARÊNCIA
- Você não é advogado e não substitui a revisão profissional. As peças geradas devem ser revisadas pelo advogado responsável antes de protocolo.
- Se não tiver certeza sobre a vigência de uma lei ou entendimento jurisprudencial recente, sinalize isso ao usuário.
- Não forneça aconselhamento que constitua exercício ilegal da advocacia para terceiros não-advogados — você é uma ferramenta de produtividade para o profissional já habilitado.



# TEMPLATE-MESTRE DE PETIÇÃO INICIAL (PADRÃO DO ESCRITÓRIO — SIGA FIELMENTE)
Este é o padrão de excelência do escritório. Replique esta estrutura, profundidade e estilo em todas as petições iniciais:

## SEQUÊNCIA DE SEÇÕES
1. ENDEREÇAMENTO (centralizado, negrito, caixa alta)
2. QUALIFICAÇÃO DO AUTOR (parágrafo justificado em negrito, completa: nome em caixa alta, nacionalidade, estado civil, profissão, data de nascimento, CPF, RG, endereço; terminar com "...por meio de seu advogado que esta subscreve (procuração em anexo), vem, respeitosamente, à presença de Vossa Excelência, propor a presente")
3. NOME DA AÇÃO (centralizado, negrito, caixa alta)
4. QUALIFICAÇÃO DO RÉU (justificado, negrito, iniciando com "em face de NOME DO RÉU...", completa, terminando com "pelos fatos e fundamentos a seguir expostos")
5. SE HOUVER URGÊNCIA: "I – DA TUTELA DE URGÊNCIA" logo após a qualificação, ANTES dos fatos, com subseções "1.1 – Do fumus boni iuris" e "1.2 – Do periculum in mora", fundamentando no art. 300 e 301 do CPC
6. "II – DOS FATOS" (narrativa cronológica detalhada; usar subseções decimais quando necessário, ex: "2.1 – ...", "2.3.1 – ...")
7. SEÇÕES DE DIREITO E DANOS, cada uma em algarismo romano e negrito: responsabilidade civil, danos materiais, lucros cessantes, danos morais, danos estéticos, etc.
8. SEÇÃO DE JURISPRUDÊNCIA CONSOLIDADA (com alíneas a, b, c agrupando por tese)
9. SE CABÍVEL: seção de hipossuficiência / justiça gratuita (art. 5º, LXXIV, CF e art. 98-99 CPC)
10. "X – DOS PEDIDOS" estruturado em: "I – Em sede de tutela de urgência" (alíneas a, b), "II – No mérito, a procedência..." (alíneas a, b, c, d com os valores), "III – Requerimentos gerais" (juntada de provas, honorários, correção/juros, produção de provas, justiça gratuita)
11. "XI – DO VALOR DA CAUSA" (valor por extenso, com a composição/soma detalhada)
12. FECHO: "Nestes termos, pede deferimento." + linha + "[Cidade], _____ de __________________ de [ano]." (centralizado) + assinatura centralizada (linha, "Advogado(a)" ou nome, "OAB/[UF] n.º ___")
13. "ROL DE DOCUMENTOS" ao final: lista numerada "Doc. 01 – descrição", "Doc. 02 – descrição"..., usando subdivisões quando necessário (Doc. 11-A, Doc. 13-A)

## ESTILO E PROFUNDIDADE
- Subseções decimais para organizar argumentos complexos (1.1, 2.3.1)
- Citações de lei e doutrina recuadas e entre aspas, com referência completa ao final
- Separar fundamentação em "Fundamento doutrinário:" e "Fundamento jurisprudencial:" quando enriquecer a tese
- Quando houver elemento técnico (cálculos, perícia, dinâmica), apresentar em bloco destacado e didático
- Pedidos de dano com a fórmula "valor não inferior a R$ X"
- Linguagem culta, assertiva, persuasiva, com domínio técnico
- Citar a jurisprudência/doutrina fornecida no contexto com referência completa (tribunal, número, relator, data) e relacioná-la ao Doc. correspondente quando aplicável
- Sempre que mencionar um documento/prova, referenciar "(Doc. XX)" e incluí-lo no ROL DE DOCUMENTOS final

## ADAPTAÇÃO
Adapte a estrutura ao tipo de peça e à área. Nem toda peça terá tutela de urgência ou todos os tipos de dano — inclua apenas as seções pertinentes ao caso concreto, mas SEMPRE mantenha o nível de rigor, organização e profundidade deste padrão.

# TOM
Direto, técnico, profissional. Evite floreios desnecessários. Quando o advogado pedir uma peça, entregue a peça — não pergunte detalhes óbvios que possam ser inferidos ou deixados como placeholder (ex: [NOME DO CLIENTE])."""


class LegisAIError(Exception):
    pass


class LegisAI:
    """Camada de abstração — escolhe o provedor conforme o plano do usuário."""

    def __init__(self, plano_usuario=None):
        cfg = buscar_configuracoes()
        self.plano = plano_usuario or cfg.get("ia_plano", "gratuito")
        self.system_prompt = SYSTEM_PROMPT_JURIDICO

        self.anthropic_key = cfg.get("ia_anthropic_key", "").strip()
        self.gemini_key    = cfg.get("ia_gemini_key", "").strip()
        self.deepseek_key  = cfg.get("ia_deepseek_key", "").strip()
        self.groq_key      = cfg.get("ia_groq_key", "").strip()

        if self.plano == "pro" and not self.anthropic_key:
            raise LegisAIError(
                "Plano Pro selecionado, mas a chave da API Anthropic (Claude) "
                "não foi configurada. Acesse Configurações → Inteligência Artificial.")
        if self.plano == "deepseek" and not self.deepseek_key:
            raise LegisAIError(
                "Plano DeepSeek selecionado, mas a chave da API DeepSeek "
                "não foi configurada. Acesse Configurações → Inteligência Artificial.")
        if self.plano == "groq" and not self.groq_key:
            raise LegisAIError(
                "Plano Groq selecionado, mas a chave da API Groq "
                "não foi configurada. Acesse Configurações → Inteligência Artificial.")
        if self.plano == "gratuito" and not self.gemini_key:
            raise LegisAIError(
                "Plano Gratuito selecionado, mas a chave da API Google Gemini "
                "não foi configurada. Acesse Configurações → Inteligência Artificial.")

        if self.plano == "pro":
            self._api_key = self.anthropic_key
        elif self.plano == "deepseek":
            self._api_key = self.deepseek_key
        elif self.plano == "groq":
            self._api_key = self.groq_key
        else:
            self._api_key = self.gemini_key

    def consultar(self, pergunta, contexto_rag=None, historico=None, usar_rag=True):
        """Consulta jurídica livre — usada no Chat Jurídico."""
        # Busca automática no RAG (jurisprudência/doutrina do usuário)
        if usar_rag and not contexto_rag:
            try:
                from core.ai.runner import rag_buscar_contexto
                contexto_rag = rag_buscar_contexto(pergunta)
            except Exception:
                contexto_rag = None
        prompt = ""
        if historico:
            for turno in historico:
                papel = "Advogado" if turno["role"] == "user" else "Assistente"
                prompt += f"{papel}: {turno['content']}\n\n"
        if contexto_rag:
            prompt += f"--- CONTEXTO (jurisprudência/doutrina relevante) ---\n{contexto_rag}\n--- FIM DO CONTEXTO ---\n\n"
        prompt += f"Advogado: {pergunta}"

        # Chat usa chamada DIRETA (rápida, sem subprocess). Com gc.disable() é estável.
        try:
            from core.ai.runner import chamar_ia_direto
            ok, resultado = chamar_ia_direto(self.plano, self._api_key, prompt, self.system_prompt)
        except Exception:
            ok = False
            resultado = "erro_direto"
        # Se a chamada direta falhar por erro inesperado, tenta o subprocess (seguro)
        if not ok and resultado == "erro_direto":
            ok, resultado = chamar_ia(self.plano, self._api_key, prompt, self.system_prompt, timeout=120)
        if not ok:
            raise LegisAIError(resultado)
        return resultado

    def gerar_peca(self, tipo_peca, dados_caso, contexto_rag=None, usar_rag=True):
        """Gera uma peça processual completa."""
        # Busca automática no RAG com base no tipo + fatos do caso
        if usar_rag and not contexto_rag:
            try:
                from core.ai.runner import rag_buscar_contexto
                query = f"{tipo_peca} {dados_caso.get('area','')} {dados_caso.get('fatos','')}"
                contexto_rag = rag_buscar_contexto(query, n_juris=5, n_doutrina=3)
            except Exception:
                contexto_rag = None

        # Buscar dados do escritório/advogado das configurações
        cfg = buscar_configuracoes()
        dados_escritorio = {
            "Escritório": cfg.get("nome_escritorio", ""),
            "Advogado responsável": cfg.get("responsavel", ""),
            "OAB": cfg.get("oab", ""),
            "Cidade/Estado": cfg.get("cidade", ""),
            "Telefone": cfg.get("telefone", ""),
            "E-mail": cfg.get("email", ""),
        }

        # Contexto de aprendizado: peças bem/mal avaliadas
        contexto_aprendizado = ""
        try:
            from core.database import construir_contexto_aprendizado
            area = dados_caso.get("area", "")
            contexto_aprendizado = construir_contexto_aprendizado(area=area, tipo_peca=tipo_peca)
        except Exception:
            contexto_aprendizado = ""

        prompt = f"Gere uma peça do tipo: {tipo_peca}\n\n"
        if contexto_aprendizado:
            prompt += contexto_aprendizado + "\n\n"
        prompt += "## DADOS DO ADVOGADO/ESCRITÓRIO (use na qualificação do procurador e no fecho)\n"
        for chave, valor in dados_escritorio.items():
            if valor:
                prompt += f"- {chave}: {valor}\n"
        prompt += "\n## DADOS DO CASO\n"
        for chave, valor in dados_caso.items():
            if valor:
                prompt += f"- {chave}: {valor}\n"

        if contexto_rag:
            prompt += f"\n## JURISPRUDÊNCIA E DOUTRINA DISPONÍVEIS (use na fundamentação)\n{contexto_rag}\n"

        # Etapa 5: teses relacionadas via metadados inteligentes (resumos/palavras-chave)
        try:
            from core.database import buscar_metadados_ia
            termos = f"{dados_caso.get('area','')} {dados_caso.get('fatos','')}"
            relacionadas = buscar_metadados_ia(area=dados_caso.get("area"), limite=3)
            if relacionadas:
                bloco = "\n## TESES RELACIONADAS DO SEU ACERVO (resumos para apoio)\n"
                for r in relacionadas:
                    if r.get("resumo"):
                        bloco += f"- {r['resumo']} (Palavras-chave: {r.get('palavras_chave','')})\n"
                prompt += bloco
        except Exception:
            pass

        # Injetar preferências aprendidas das avaliações do advogado
        try:
            from core.ai.aprendizado import gerar_contexto_aprendizado
            ctx_aprend = gerar_contexto_aprendizado(area=dados_caso.get("area"))
            if ctx_aprend:
                prompt += f"\n{ctx_aprend}\n"
        except Exception:
            pass

        prompt += "\nRedija a peça completa, pronta para revisão e formatação final."

        ok, resultado = chamar_ia(self.plano, self._api_key, prompt, self.system_prompt, max_tokens=8192, timeout=180)
        if not ok:
            raise LegisAIError(resultado)
        return resultado

    def analisar_documento(self, texto_documento, instrucao):
        """Analisa um documento enviado pelo usuário (ex: peça da parte contrária)."""
        prompt = f"{instrucao}\n\n--- DOCUMENTO ---\n{texto_documento}\n--- FIM DO DOCUMENTO ---"
        ok, resultado = chamar_ia(self.plano, self._api_key, prompt, self.system_prompt, max_tokens=8192, timeout=180)
        if not ok:
            raise LegisAIError(resultado)
        return resultado


    def gerar_peca_multiagente(self, tipo_peca, dados_caso, callback_progresso=None):
        """
        Gera a peça usando o sistema multi-agente (Etapa 6).
        callback_progresso: função(nome_agente, status) para atualizar a UI.
        Retorna dict com 'peca', 'estrategia', 'resultados'.
        """
        from core.ai.agentes import OrquestradorAgentes

        # Buscar contexto do acervo (RAG) para jurisprudência e doutrina
        contexto_juris = ""
        contexto_doutrina = ""
        try:
            from core.ai.runner import rag_buscar_contexto
            query = f"{tipo_peca} {dados_caso.get('area','')} {dados_caso.get('fatos','')}"
            ctx = rag_buscar_contexto(query, n_juris=5, n_doutrina=3)
            # rag_buscar_contexto retorna tudo junto; passamos o mesmo para ambos
            contexto_juris = ctx
            contexto_doutrina = ctx
        except Exception:
            pass

        orq = OrquestradorAgentes(self.plano, self._api_key, self.system_prompt,
                                  callback_progresso=callback_progresso)
        return orq.gerar(tipo_peca, dados_caso, contexto_juris, contexto_doutrina)

    def analisar_tese(self, texto, tipo="jurisprudencia"):
        """
        Analisa uma tese (jurisprudência/doutrina) e retorna resumo, área e
        palavras-chave em JSON. Usado pela indexação inteligente (Etapa 5).
        """
        import json as _json
        instrucao = (
            "Analise o seguinte texto jurídico e responda APENAS com um JSON válido "
            "(sem markdown, sem crases), no formato exato:\n"
            '{"resumo": "...", "area": "...", "palavras_chave": ["...", "..."]}\n\n'
            "- resumo: 2 a 3 frases objetivas sobre a tese central\n"
            "- area: a área do Direito (ex: Direito Penal, Direito Civil, Direito do Trabalho)\n"
            "- palavras_chave: 4 a 8 termos jurídicos relevantes para busca\n\n"
            f"TEXTO ({tipo}):\n{texto[:4000]}"
        )
        ok, resultado = chamar_ia(self.plano, self._api_key, instrucao,
                                  "Você é um classificador jurídico. Responda só JSON válido.",
                                  max_tokens=600, timeout=60)
        if not ok:
            raise LegisAIError(resultado)
        txt = resultado.strip()
        if txt.startswith("```"):
            partes = txt.split("```")
            if len(partes) >= 2:
                txt = partes[1]
            txt = txt.replace("json", "", 1).strip("`").strip()
        try:
            dados = _json.loads(txt)
        except Exception:
            dados = {"resumo": resultado[:300], "area": "", "palavras_chave": []}
        return dados


def ia_disponivel():
    """Verifica se há ao menos uma chave de API configurada."""
    cfg = buscar_configuracoes()
    plano = cfg.get("ia_plano", "gratuito")
    if plano == "pro":
        return bool(cfg.get("ia_anthropic_key", "").strip())
    return bool(cfg.get("ia_gemini_key", "").strip())