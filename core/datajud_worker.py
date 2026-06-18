# core/datajud_worker.py — Worker de consulta Datajud em processo separado
# Isola a lib de rede (requests) do Qt, evitando crash nativo no Windows.
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    try:
        entrada = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"ok": False, "erro": f"Entrada inválida: {e}"}))
        return

    numero = entrada.get("numero", "")
    tribunal = entrada.get("tribunal", "")
    timeout = entrada.get("timeout", 15)

    try:
        from core.datajud import consultar_processo
        ok, resultado = consultar_processo(numero, tribunal, timeout=timeout)
        if ok:
            print(json.dumps({"ok": True, "movimentos": resultado}))
        else:
            print(json.dumps({"ok": False, "erro": resultado}))
    except Exception as e:
        print(json.dumps({"ok": False, "erro": str(e)}))


if __name__ == "__main__":
    main()
