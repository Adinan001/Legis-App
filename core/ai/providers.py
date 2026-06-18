# core/ai/providers.py — Adaptadores de provedores de IA
"""
Cada provider implementa o mesmo método generate(prompt, system) -> str
para que a classe LegisAI possa trocar de provedor sem alterar a lógica de negócio.
"""
import sys
import asyncio


def _garantir_event_loop():
    """Garante que a thread atual tem um event loop asyncio válido (necessário no Windows)."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)



class ProviderError(Exception):
    """Erro genérico de comunicação com o provedor de IA."""
    pass


class ClaudeProvider:
    """Adaptador para a API da Anthropic (Claude) — Plano Pro."""

    def __init__(self, api_key, modelo="claude-sonnet-4-6"):
        if not api_key:
            raise ProviderError("Chave da API Anthropic não configurada.")
        try:
            import anthropic
        except ImportError:
            raise ProviderError(
                "Biblioteca 'anthropic' não instalada. Execute:\npip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.modelo = modelo

    def generate(self, prompt, system, max_tokens=8192, timeout=60):
        _garantir_event_loop()
        try:
            response = self.client.messages.create(
                model=self.modelo,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
            )
            return response.content[0].text
        except Exception as e:
            raise ProviderError(f"Erro na API Claude: {e}")


class GeminiProvider:
    """Adaptador para a API do Google Gemini — Plano Gratuito (SDK google-genai)."""

    def __init__(self, api_key, modelo="gemini-2.0-flash"):
        if not api_key:
            raise ProviderError("Chave da API Google Gemini não configurada.")
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ProviderError(
                "Biblioteca 'google-genai' não instalada. Execute:\n"
                "pip install google-genai")
        self.client = genai.Client(api_key=api_key)
        self._types = types
        self.modelo = modelo

    def generate(self, prompt, system, max_tokens=8192, timeout=60):
        _garantir_event_loop()
        try:
            response = self.client.models.generate_content(
                model=self.modelo,
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text
        except Exception as e:
            raise ProviderError(f"Erro na API Gemini: {e}")


def testar_chave(plano, api_key):
    """Testa se a chave de API é válida fazendo uma chamada mínima (timeout 20s)."""
    try:
        if plano == "pro":
            provider = ClaudeProvider(api_key)
            resposta = provider.generate(
                "Responda apenas: OK", system="Responda de forma extremamente breve.",
                max_tokens=10, timeout=20)
        else:
            provider = GeminiProvider(api_key)
            resposta = provider.generate(
                "Responda apenas: OK", system="Responda de forma extremamente breve.",
                max_tokens=10, timeout=20)
        return True, resposta.strip()
    except ProviderError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erro inesperado: {e}"
