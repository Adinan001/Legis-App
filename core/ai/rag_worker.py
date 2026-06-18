# core/ai/rag_worker.py
# Worker de RAG executado como processo separado.
# Comandos: indexar, remover, buscar, stats, reindexar_tudo
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    try:
        entrada = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"ok": False, "erro": f"Entrada inválida: {e}"}))
        return

    comando = entrada.get("comando", "")

    try:
        from core.ai.rag import LegisRAG
        rag = LegisRAG()

        if comando == "buscar":
            ctx = rag.buscar_contexto(
                entrada.get("query", ""),
                n_juris=entrada.get("n_juris", 4),
                n_doutrina=entrada.get("n_doutrina", 3))
            print(json.dumps({"ok": True, "contexto": ctx}))

        elif comando == "indexar_juris":
            rag.indexar_jurisprudencia(
                entrada["entrada_id"], entrada.get("tribunal", ""),
                entrada.get("numero", ""), entrada.get("ementa", ""),
                entrada.get("tema", ""))
            print(json.dumps({"ok": True}))

        elif comando == "indexar_doutrina":
            rag.indexar_doutrina(
                entrada["entrada_id"], entrada.get("autor", ""),
                entrada.get("obra", ""), entrada.get("trecho", ""),
                entrada.get("tema", ""))
            print(json.dumps({"ok": True}))

        elif comando == "remover_juris":
            rag.remover_jurisprudencia(entrada["entrada_id"])
            print(json.dumps({"ok": True}))

        elif comando == "remover_doutrina":
            rag.remover_doutrina(entrada["entrada_id"])
            print(json.dumps({"ok": True}))

        elif comando == "stats":
            print(json.dumps({"ok": True, "stats": rag.estatisticas()}))

        elif comando == "reindexar_tudo":
            from core.database import (buscar_temas, buscar_entradas,
                                       buscar_doutrina_temas, buscar_doutrina_entradas)
            from config import AREAS_DIREITO
            n_juris, n_dout = 0, 0
            # Reindexar jurisprudência
            for area in AREAS_DIREITO:
                for tema in buscar_temas(area):
                    for e in buscar_entradas(tema["id"]):
                        rag.indexar_jurisprudencia(
                            e["id"], e.get("tribunal", ""), e.get("numero_acordao", ""),
                            e.get("ementa", ""), tema["tema"])
                        n_juris += 1
            # Reindexar doutrina
            for tema in buscar_doutrina_temas():
                for e in buscar_doutrina_entradas(tema["id"]):
                    rag.indexar_doutrina(
                        e["id"], e.get("autor", ""), e.get("obra", ""),
                        e.get("trecho", ""), tema["tema"])
                    n_dout += 1
            print(json.dumps({"ok": True, "n_juris": n_juris, "n_doutrina": n_dout}))

        else:
            print(json.dumps({"ok": False, "erro": f"Comando desconhecido: {comando}"}))

    except Exception as e:
        import traceback
        print(json.dumps({"ok": False, "erro": f"{e}", "trace": traceback.format_exc()[:500]}))


if __name__ == "__main__":
    main()
