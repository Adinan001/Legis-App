# core/ai/runner.py — Executa o worker de IA em processo separado
import sys, os, json, subprocess


def _subprocess_kwargs():
    """Retorna kwargs seguros para subprocess no Windows, isolando do Qt."""
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = si
    return kwargs


def _python_executavel():
    """Retorna o Python a usar para o subprocess."""
    # Em produção (exe compilado), reusa o próprio executável com flag especial
    return sys.executable


def _worker_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker_subprocess.py")


def chamar_ia(plano, api_key, prompt, system, max_tokens=8192, timeout=120,
              deepseek_key=None, usar_fallback=True):
    """
    Executa a chamada de IA em um processo Python separado.
    Isola completamente as bibliotecas de rede (httpx/grpc) do Qt,
    evitando crashes nativos no Windows.
    Se deepseek_key for fornecida e o provedor principal falhar por
    sobrecarga/limite, tenta automaticamente a DeepSeek (fallback).
    Retorna (ok: bool, resultado: str)
    """
    # Buscar chaves de fallback das configurações se não passadas
    groq_key = ""
    if deepseek_key is None:
        try:
            from core.database import buscar_configuracoes
            _cfg = buscar_configuracoes()
            deepseek_key = _cfg.get("ia_deepseek_key", "").strip()
            groq_key = _cfg.get("ia_groq_key", "").strip()
        except Exception:
            deepseek_key = ""
    else:
        try:
            from core.database import buscar_configuracoes
            groq_key = buscar_configuracoes().get("ia_groq_key", "").strip()
        except Exception:
            groq_key = ""

    entrada = json.dumps({
        "plano": plano,
        "api_key": api_key,
        "prompt": prompt,
        "system": system,
        "max_tokens": max_tokens,
        "deepseek_key": deepseek_key,
        "groq_key": groq_key,
        "usar_fallback": usar_fallback,
    })

    # Flags para não abrir janela de console no Windows
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000  # CREATE_NO_WINDOW

    try:
        if getattr(sys, "frozen", False):
            # Executável compilado: chama o worker via módulo embutido
            cmd = [sys.executable, "--run-ai-worker"]
        else:
            cmd = [_python_executavel(), _worker_path()]

        proc = subprocess.run(
            cmd,
            input=entrada,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=creationflags,
            encoding="utf-8",
        )

        if proc.returncode != 0:
            return False, f"Worker falhou (código {proc.returncode}): {proc.stderr[:300]}"

        saida = (proc.stdout or "").strip()
        if not saida:
            return False, "O worker não retornou resposta."

        # Pega a última linha que for JSON válido
        for linha in reversed(saida.splitlines()):
            linha = linha.strip()
            if linha.startswith("{"):
                try:
                    dados = json.loads(linha)
                    if dados.get("ok"):
                        return True, dados.get("texto", "")
                    else:
                        return False, dados.get("erro", "Erro desconhecido")
                except json.JSONDecodeError:
                    continue
        return False, f"Resposta inválida do worker: {saida[:300]}"

    except subprocess.TimeoutExpired:
        return False, f"Tempo limite excedido ({timeout}s). Verifique sua conexão."
    except Exception as e:
        return False, f"Erro ao executar worker: {e}"


def testar_chave(plano, api_key):
    """Testa a validade da chave via subprocess."""
    return chamar_ia(
        plano, api_key,
        prompt="Responda apenas: OK",
        system="Responda de forma extremamente breve.",
        max_tokens=10,
        timeout=30,
        usar_fallback=False,  # ao testar, não usar fallback
    )


# ──────────────────────────────────────────────
# RAG via subprocess
# ──────────────────────────────────────────────
def _rag_worker_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_worker.py")


def chamar_rag(comando, timeout=300, **kwargs):
    """
    Executa um comando RAG em processo separado.
    Retorna (ok: bool, dados: dict)
    """
    entrada = json.dumps(dict(comando=comando, **kwargs))

    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000  # CREATE_NO_WINDOW

    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--run-rag-worker"]
        else:
            cmd = [_python_executavel(), _rag_worker_path()]

        proc = subprocess.run(
            cmd, input=entrada, capture_output=True, text=True,
            timeout=timeout, creationflags=creationflags, encoding="utf-8",
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )

        if proc.returncode != 0:
            return False, {"erro": f"RAG worker falhou: {proc.stderr[:300]}"}

        saida = (proc.stdout or "").strip()
        for linha in reversed(saida.splitlines()):
            linha = linha.strip()
            if linha.startswith("{"):
                try:
                    dados = json.loads(linha)
                    return dados.get("ok", False), dados
                except json.JSONDecodeError:
                    continue
        return False, {"erro": f"Resposta inválida: {saida[:300]}"}

    except subprocess.TimeoutExpired:
        return False, {"erro": f"Tempo limite excedido ({timeout}s)."}
    except Exception as e:
        return False, {"erro": f"Erro ao executar RAG worker: {e}"}


def rag_buscar_contexto(query, n_juris=4, n_doutrina=3):
    ok, dados = chamar_rag("buscar", query=query, n_juris=n_juris, n_doutrina=n_doutrina, timeout=120)
    return dados.get("contexto", "") if ok else ""


def rag_indexar_juris_async(entrada_id, tribunal, numero, ementa, tema=""):
    """Indexa jurisprudência em background (thread daemon) sem travar a UI."""
    import threading
    def _trabalho():
        chamar_rag("indexar_juris", entrada_id=entrada_id, tribunal=tribunal,
                   numero=numero, ementa=ementa, tema=tema, timeout=180)
    t = threading.Thread(target=_trabalho, daemon=True)
    t.start()


def rag_indexar_doutrina_async(entrada_id, autor, obra, trecho, tema=""):
    import threading
    def _trabalho():
        chamar_rag("indexar_doutrina", entrada_id=entrada_id, autor=autor,
                   obra=obra, trecho=trecho, tema=tema, timeout=180)
    t = threading.Thread(target=_trabalho, daemon=True)
    t.start()


# ──────────────────────────────────────────────
# Exportação de documentos via subprocess
# ──────────────────────────────────────────────
def _export_worker_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_worker.py")


def exportar_documento(formato, caminho, titulo, categoria, conteudo, timeout=120):
    """Exporta documento (docx/pdf) em processo separado. Retorna (ok, msg)."""
    entrada = json.dumps({
        "formato": formato, "caminho": caminho, "titulo": titulo,
        "categoria": categoria, "conteudo": conteudo,
    })
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000

    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--run-export-worker"]
        else:
            cmd = [_python_executavel(), _export_worker_path()]

        proc = subprocess.run(
            cmd, input=entrada, capture_output=True, text=True,
            timeout=timeout, creationflags=creationflags, encoding="utf-8",
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )
        if proc.returncode != 0:
            return False, f"Falha na exportação: {proc.stderr[:300]}"
        saida = (proc.stdout or "").strip()
        for linha in reversed(saida.splitlines()):
            linha = linha.strip()
            if linha.startswith("{"):
                try:
                    dados = json.loads(linha)
                    return dados.get("ok", False), dados.get("caminho") if dados.get("ok") else dados.get("erro", "Erro")
                except json.JSONDecodeError:
                    continue
        return False, f"Resposta inválida: {saida[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"Tempo limite excedido ({timeout}s)."
    except Exception as e:
        return False, f"Erro ao exportar: {e}"


# ──────────────────────────────────────────────
# ETAPA 5 — Indexação Inteligente (análise de teses)
# ──────────────────────────────────────────────
def analisar_tese_async(tipo_fonte, fonte_id, texto):
    """
    Analisa uma tese em background (thread daemon) e salva os metadados.
    Não trava a UI. Silencioso em caso de erro (não atrapalha o salvamento).
    """
    import threading

    def _trabalho():
        try:
            from core.database import buscar_configuracoes, salvar_metadados_ia
            cfg = buscar_configuracoes()
            plano = cfg.get("ia_plano", "gratuito")
            # Escolher a chave conforme o plano
            chave = {
                "pro": cfg.get("ia_anthropic_key", ""),
                "deepseek": cfg.get("ia_deepseek_key", ""),
                "groq": cfg.get("ia_groq_key", ""),
            }.get(plano, cfg.get("ia_gemini_key", "")).strip()
            if not chave:
                return  # IA não configurada; ignora silenciosamente

            instrucao = (
                "Analise o seguinte texto jurídico e responda APENAS com um JSON válido "
                "(sem markdown, sem crases), no formato exato:\n"
                '{"resumo": "...", "area": "...", "palavras_chave": ["...", "..."]}\n\n'
                "- resumo: 2 a 3 frases objetivas sobre a tese central\n"
                "- area: a área do Direito\n"
                "- palavras_chave: 4 a 8 termos jurídicos relevantes\n\n"
                f"TEXTO ({tipo_fonte}):\n{texto[:4000]}"
            )
            ok, resultado = chamar_ia(
                plano, chave, instrucao,
                "Você é um classificador jurídico. Responda só JSON válido.",
                max_tokens=600, timeout=60, usar_fallback=True)
            if not ok:
                return

            import json
            txt = resultado.strip()
            if txt.startswith("```"):
                partes = txt.split("```")
                if len(partes) >= 2:
                    txt = partes[1]
                txt = txt.replace("json", "", 1).strip("`").strip()
            try:
                dados = json.loads(txt)
            except Exception:
                dados = {"resumo": resultado[:300], "area": "", "palavras_chave": []}

            pk = dados.get("palavras_chave", [])
            if isinstance(pk, list):
                pk = ", ".join(str(p) for p in pk)
            salvar_metadados_ia(
                tipo_fonte, fonte_id,
                dados.get("resumo", ""), dados.get("area", ""), pk or "")
        except Exception:
            pass  # nunca interromper o fluxo principal

    t = threading.Thread(target=_trabalho, daemon=True)
    t.start()


# ──────────────────────────────────────────────
# Consulta Datajud via subprocess (isola rede do Qt)
# ──────────────────────────────────────────────
def consultar_datajud_subprocess(numero, tribunal, timeout=20):
    """Consulta o Datajud em processo separado. Retorna (ok, movimentos|erro)."""
    import subprocess
    entrada = json.dumps({"numero": numero, "tribunal": tribunal, "timeout": min(timeout, 15)})
    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--run-datajud-worker"]
        else:
            worker = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datajud_worker.py")
            cmd = [_python_executavel(), worker]

        proc = subprocess.run(
            cmd, input=entrada, capture_output=True, text=True,
            timeout=timeout + 10, encoding="utf-8",
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            **_subprocess_kwargs(),
        )
        if proc.returncode != 0:
            return False, f"Falha na consulta: {proc.stderr[:200]}"
        saida = (proc.stdout or "").strip()
        for linha in reversed(saida.splitlines()):
            linha = linha.strip()
            if linha.startswith("{"):
                try:
                    dados = json.loads(linha)
                    if dados.get("ok"):
                        return True, dados.get("movimentos", [])
                    return False, dados.get("erro", "Erro desconhecido")
                except json.JSONDecodeError:
                    continue
        return False, "Resposta inválida do worker."
    except subprocess.TimeoutExpired:
        return False, "O servidor do CNJ demorou muito para responder."
    except Exception as e:
        return False, f"Erro ao consultar: {e}"


# ──────────────────────────────────────────────
# Chamada DIRETA (sem subprocess) — para o chat, que precisa ser rápido.
# Roda numa QThread do chat; com gc.disable() o risco de crash é baixo.
# ──────────────────────────────────────────────
def chamar_ia_direto(plano, api_key, prompt, system, max_tokens=4096):
    """Chamada direta à IA, sem subprocess. Retorna (ok, resultado)."""
    try:
        if plano == "groq":
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=min(max_tokens, 8000),
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}])
            return True, resp.choices[0].message.content
        elif plano == "deepseek":
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            resp = client.chat.completions.create(
                model="deepseek-chat", max_tokens=min(max_tokens, 8000),
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}])
            return True, resp.choices[0].message.content
        elif plano == "pro":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=max_tokens,
                system=system, messages=[{"role": "user", "content": prompt}])
            return True, resp.content[0].text
        else:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(
                model="gemini-flash-latest", contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system, max_output_tokens=max_tokens))
            return True, resp.text
    except Exception as e:
        msg = str(e)
        if "503" in msg or "overloaded" in msg.lower() or "UNAVAILABLE" in msg:
            return False, "O servidor de IA está sobrecarregado. Tente novamente em instantes."
        if "429" in msg or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
            return False, "Limite de uso da API atingido. Aguarde ou troque de provedor."
        return False, msg