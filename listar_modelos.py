# listar_modelos.py — Lista os modelos Gemini disponíveis para sua chave
import os, sys

chave = os.environ.get("GEMINI_KEY", "")
if not chave:
    print("ERRO: defina a chave com $env:GEMINI_KEY=\"sua_chave\"")
    sys.exit(1)

from google import genai
client = genai.Client(api_key=chave)

print("\n=== MODELOS DISPONÍVEIS PARA SUA CHAVE ===\n")
for m in client.models.list():
    # Mostra só os que suportam generateContent
    acoes = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", [])
    print(f"{m.name}")
    if acoes:
        print(f"    -> {acoes}")
print("\n=== FIM ===")