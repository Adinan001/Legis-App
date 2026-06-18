# core/ai/worker_subprocess.py
# Executado como processo SEPARADO para isolar as libs de rede do Qt.
# Recebe JSON via stdin, devolve JSON via stdout.
# Suporta: Gemini (gratuito), Claude (pro), DeepSeek (gratuito/fallback).
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _retry(funcao, tentativas=3, espera_base=2):
    """Tenta executar; em erros temporários (503/429/overloaded) repete."""
    ultimo = None
    for i in range(tentativas):
        try:
            return funcao()
        except Exception as e:
            msg = str(e).lower()
            ultimo = e
            temporario = any(t in msg for t in [
                "503", "unavailable", "overloaded", "high demand",
                "429", "rate", "timeout", "deadline"])
            if temporario and i < tentativas - 1:
                time.sleep(espera_base * (i + 1))
                continue
            raise
    raise ultimo


def _chamar_gemini(api_key, modelo, prompt, system, max_tokens):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    def _c():
        resp = client.models.generate_content(
            model=modelo, contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system, max_output_tokens=max_tokens))
        return resp.text
    return _retry(_c)


def _chamar_claude(api_key, prompt, system, max_tokens):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    def _c():
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text
    return _retry(_c)


def _chamar_deepseek(api_key, prompt, system, max_tokens):
    # DeepSeek é compatível com a API da OpenAI
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    def _c():
        resp = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=min(max_tokens, 8000),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ])
        return resp.choices[0].message.content
    return _retry(_c)


def _chamar_groq(api_key, prompt, system, max_tokens):
    # Groq é compatível com a API da OpenAI — gratuito e muito rápido
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    def _c():
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=min(max_tokens, 8000),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ])
        return resp.choices[0].message.content
    return _retry(_c)


def main():
    try:
        entrada = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"ok": False, "erro": f"Entrada inválida: {e}"})); return

    plano      = entrada.get("plano", "gratuito")
    api_key    = entrada.get("api_key", "")
    prompt     = entrada.get("prompt", "")
    system     = entrada.get("system", "")
    max_tokens = entrada.get("max_tokens", 8192)
    modelo_gemini = entrada.get("modelo_gemini", "gemini-flash-latest")
    deepseek_key  = entrada.get("deepseek_key", "")
    groq_key      = entrada.get("groq_key", "")
    usar_fallback = entrada.get("usar_fallback", True)

    erro_principal = None
    try:
        if plano == "pro":
            texto = _chamar_claude(api_key, prompt, system, max_tokens)
        elif plano == "deepseek":
            texto = _chamar_deepseek(api_key, prompt, system, max_tokens)
        elif plano == "groq":
            texto = _chamar_groq(api_key, prompt, system, max_tokens)
        else:
            texto = _chamar_gemini(api_key, modelo_gemini, prompt, system, max_tokens)
        print(json.dumps({"ok": True, "texto": texto, "provedor": plano}))
        return
    except Exception as e:
        erro_principal = str(e)

    # FALLBACK: se o provedor principal falhou por sobrecarga/limite,
    # tenta automaticamente Groq (gratuito) e depois DeepSeek, se houver chave.
    msg_lower = (erro_principal or "").lower()
    deve_tentar = (usar_fallback and any(t in msg_lower for t in [
        "503", "unavailable", "overloaded", "high demand",
        "429", "resource_exhausted", "rate", "quota", "limit", "insufficient"]))
    if deve_tentar:
        # 1) Groq
        if groq_key and plano != "groq":
            try:
                texto = _chamar_groq(groq_key, prompt, system, max_tokens)
                print(json.dumps({"ok": True, "texto": texto, "provedor": "groq",
                                  "fallback": True}))
                return
            except Exception as e2:
                erro_principal = f"{erro_principal} | Fallback Groq falhou: {e2}"
        # 2) DeepSeek
        if deepseek_key and plano != "deepseek":
            try:
                texto = _chamar_deepseek(deepseek_key, prompt, system, max_tokens)
                print(json.dumps({"ok": True, "texto": texto, "provedor": "deepseek",
                                  "fallback": True}))
                return
            except Exception as e3:
                erro_principal = f"{erro_principal} | Fallback DeepSeek falhou: {e3}"

    # Mensagem amigável
    msg = erro_principal or "Erro desconhecido"
    if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
        msg = ("O servidor de IA está sobrecarregado (erro 503). "
               + ("O fallback também não respondeu. " if deepseek_key else "")
               + "Aguarde alguns segundos e tente novamente.")
    elif "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        msg = ("Limite de uso da API atingido (erro 429). "
               "Aguarde um momento ou configure o Groq como alternativa gratuita.")
    print(json.dumps({"ok": False, "erro": msg}))


if __name__ == "__main__":
    main()
