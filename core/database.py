# core/database.py
import sqlite3
import os
import sys

def _get_db_path():
    """Retorna o caminho correto do banco dependendo do ambiente."""
    # Se estiver rodando como executável compilado (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Salva em AppData\Local\Legis — pasta com permissão de escrita
        app_data = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Legis')
        os.makedirs(app_data, exist_ok=True)
        return os.path.join(app_data, 'legis.db')
    else:
        # Modo desenvolvimento — salva na pasta do projeto
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'legis.db')

DB_PATH = _get_db_path()


def conectar():
    # timeout maior + WAL evita travamentos quando o arquivo está em pasta
    # sincronizada (OneDrive/Dropbox) ou acessado por múltiplos processos
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass
    return conn


def inicializar_banco():
    with conectar() as conn:
        c = conn.cursor()

        # Processos
        c.execute("""CREATE TABLE IF NOT EXISTS processos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            cliente TEXT NOT NULL,
            acao TEXT NOT NULL,
            status TEXT NOT NULL,
            data_distribuicao TEXT DEFAULT '',
            observacoes TEXT DEFAULT ''
        )""")

        # Clientes
        c.execute("""CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            documento TEXT NOT NULL,
            contato TEXT NOT NULL,
            email TEXT DEFAULT '',
            endereco TEXT DEFAULT ''
        )""")

        # Financeiro
        c.execute("""CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL
        )""")

        # Agenda / Prazos
        c.execute("""CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT DEFAULT '',
            tipo TEXT NOT NULL,
            processo_vinculado TEXT DEFAULT '',
            concluido INTEGER DEFAULT 0
        )""")

        # Documentos / Modelos
        c.execute("""CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            conteudo TEXT NOT NULL,
            data_criacao TEXT NOT NULL,
            data_modificacao TEXT NOT NULL
        )""")

        # Jurisprudência — Temas
        c.execute("""CREATE TABLE IF NOT EXISTS juris_temas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT NOT NULL,
            tema TEXT NOT NULL,
            data_criacao TEXT DEFAULT ''
        )""")

        # Jurisprudência — Entradas
        c.execute("""CREATE TABLE IF NOT EXISTS juris_entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema_id INTEGER NOT NULL,
            tribunal TEXT NOT NULL,
            numero_acordao TEXT NOT NULL,
            ementa TEXT NOT NULL,
            link TEXT DEFAULT '',
            data_julgamento TEXT DEFAULT '',
            data_cadastro TEXT DEFAULT '',
            FOREIGN KEY(tema_id) REFERENCES juris_temas(id) ON DELETE CASCADE
        )""")

        # Configurações
        c.execute("""CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )""")

        # Dados demo
        c.execute("SELECT COUNT(*) FROM processos")
        if c.fetchone()[0] == 0:
            _popular_dados_demo(c)

        conn.commit()


def _popular_dados_demo(c):
    c.executemany("INSERT INTO processos (numero, cliente, acao, status, data_distribuicao) VALUES (?,?,?,?,?)", [
        ("1002345-67.2026.8.26.0000", "João Silva",       "Trabalhista",           "Em andamento",            "10/01/2026"),
        ("0054321-11.2025.8.19.0001", "Maria Oliveira",   "Cível — Indenização",   "Prazo Fatal",             "05/03/2025"),
        ("5009876-43.2026.4.03.6100", "Empresa X LTDA",   "Tributária",            "Concluso para Sentença",  "22/02/2026"),
    ])
    c.executemany("INSERT INTO clientes (nome, tipo, documento, contato, email) VALUES (?,?,?,?,?)", [
        ("João Silva",     "Pessoa Física",   "123.456.789-00",      "(11) 98888-7777", "joao@email.com"),
        ("Maria Oliveira", "Pessoa Física",   "987.654.321-11",      "(21) 99999-8888", "maria@email.com"),
        ("Empresa X LTDA", "Pessoa Jurídica", "12.345.678/0001-99",  "(11) 3333-4444",  "contato@empresax.com"),
    ])
    c.executemany("INSERT INTO financeiro (data, descricao, tipo, valor) VALUES (?,?,?,?)", [
        ("2026-06-05", "Honorários Contratuais — João Silva",         "Receita",  3500.00),
        ("2026-06-02", "Licença Software de Tribunais",               "Despesa",   250.00),
        ("2026-05-28", "Honorários Sucumbenciais — Empresa X",        "Receita", 12000.00),
        ("2026-05-10", "Aluguel do Escritório",                       "Despesa",  1800.00),
    ])
    c.executemany("INSERT INTO agenda (data, hora, titulo, tipo, processo_vinculado) VALUES (?,?,?,?,?)", [
        ("2026-06-15", "09:00", "Audiência de Instrução — João Silva",    "Audiência",  "1002345-67.2026.8.26.0000"),
        ("2026-06-12", "14:00", "Prazo — Contrarrazões Maria Oliveira",   "Prazo Fatal","0054321-11.2025.8.19.0001"),
        ("2026-06-20", "10:30", "Reunião com Empresa X — Estratégia",     "Reunião",    ""),
    ])
    c.executemany("INSERT INTO documentos (titulo, categoria, conteudo, data_criacao, data_modificacao) VALUES (?,?,?,?,?)", [
        ("Petição Inicial Cível",  "Cível",      "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO...\n\n[Corpo da petição aqui]", "2026-05-01", "2026-05-01"),
        ("Contrato de Honorários", "Contratos",  "CONTRATO DE PRESTAÇÃO DE SERVIÇOS ADVOCATÍCIOS\n\n[Corpo do contrato aqui]", "2026-04-10", "2026-05-20"),
    ])
    c.execute("INSERT INTO juris_temas (area, tema, data_criacao) VALUES (?,?,?)",
              ("Direito Penal", "Homicídio Doloso — Dolo Eventual", "2026-05-01"))
    tema_id = c.lastrowid
    c.execute("""INSERT INTO juris_entradas (tema_id, tribunal, numero_acordao, ementa, link, data_julgamento, data_cadastro)
                 VALUES (?,?,?,?,?,?,?)""", (
        tema_id,
        "STJ",
        "HC 123456/SP",
        "PENAL. HOMICÍDIO. DOLO EVENTUAL. DIREÇÃO PERIGOSA. Configura homicídio doloso na modalidade dolo eventual a conduta do agente que, embriagado, assume o risco de produzir o resultado morte ao conduzir veículo em alta velocidade em via urbana.",
        "https://www.stj.jus.br",
        "2025-08-14",
        "2026-05-01"
    ))
    c.executemany("INSERT INTO configuracoes (chave, valor) VALUES (?,?)", [
        ("nome_escritorio", "Lima & Paixão Advocacia"),
        ("responsavel",     "Adinan da Rocha Lima"),
        ("oab",             "OAB/SP 275.676"),
        ("cidade",          "Sorocaba — SP"),
        ("telefone",        ""),
        ("email",           ""),
    ])


# ──────────────────────────────────────────────
# PROCESSOS
# ──────────────────────────────────────────────
def buscar_processos(filtro=""):
    with conectar() as conn:
        if filtro:
            rows = conn.execute(
                "SELECT * FROM processos WHERE numero LIKE ? OR cliente LIKE ? OR acao LIKE ? OR status LIKE ? ORDER BY id DESC",
                (f"%{filtro}%",)*4
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM processos ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

def salvar_processo(p):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO processos (numero, cliente, acao, status, data_distribuicao, observacoes) VALUES (?,?,?,?,?,?)",
            (p["numero"], p["cliente"], p["acao"], p["status"], p.get("data_distribuicao",""), p.get("observacoes",""))
        )

def atualizar_processo(pid, p):
    with conectar() as conn:
        conn.execute(
            "UPDATE processos SET numero=?, cliente=?, acao=?, status=?, data_distribuicao=?, observacoes=? WHERE id=?",
            (p["numero"], p["cliente"], p["acao"], p["status"], p.get("data_distribuicao",""), p.get("observacoes",""), pid)
        )

def excluir_processo(pid):
    with conectar() as conn:
        conn.execute("DELETE FROM processos WHERE id=?", (pid,))


# ──────────────────────────────────────────────
# CLIENTES
# ──────────────────────────────────────────────
def buscar_clientes(filtro=""):
    with conectar() as conn:
        if filtro:
            rows = conn.execute(
                "SELECT * FROM clientes WHERE nome LIKE ? OR documento LIKE ? OR contato LIKE ? ORDER BY id DESC",
                (f"%{filtro}%",)*3
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM clientes ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

def salvar_cliente(c_):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO clientes (nome, tipo, documento, contato, email, endereco) VALUES (?,?,?,?,?,?)",
            (c_["nome"], c_["tipo"], c_["documento"], c_["contato"], c_.get("email",""), c_.get("endereco",""))
        )

def atualizar_cliente(cid, c_):
    with conectar() as conn:
        conn.execute(
            "UPDATE clientes SET nome=?, tipo=?, documento=?, contato=?, email=?, endereco=? WHERE id=?",
            (c_["nome"], c_["tipo"], c_["documento"], c_["contato"], c_.get("email",""), c_.get("endereco",""), cid)
        )

def excluir_cliente(cid):
    with conectar() as conn:
        conn.execute("DELETE FROM clientes WHERE id=?", (cid,))


# ──────────────────────────────────────────────
# FINANCEIRO
# ──────────────────────────────────────────────
def buscar_lancamentos(filtro=""):
    with conectar() as conn:
        if filtro:
            rows = conn.execute(
                "SELECT * FROM financeiro WHERE descricao LIKE ? OR tipo LIKE ? ORDER BY data DESC, id DESC",
                (f"%{filtro}%", f"%{filtro}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM financeiro ORDER BY data DESC, id DESC").fetchall()
    return [dict(r) for r in rows]

def salvar_lancamento(l):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO financeiro (data, descricao, tipo, valor) VALUES (?,?,?,?)",
            (l["data"], l["descricao"], l["tipo"], float(l["valor"]))
        )

def excluir_lancamento(lid):
    with conectar() as conn:
        conn.execute("DELETE FROM financeiro WHERE id=?", (lid,))


# ──────────────────────────────────────────────
# AGENDA
# ──────────────────────────────────────────────
def buscar_agenda(apenas_pendentes=False):
    with conectar() as conn:
        q = "SELECT * FROM agenda"
        if apenas_pendentes:
            q += " WHERE concluido=0"
        q += " ORDER BY data ASC, hora ASC"
        rows = conn.execute(q).fetchall()
    return [dict(r) for r in rows]

def salvar_compromisso(a):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO agenda (data, hora, titulo, descricao, tipo, processo_vinculado, concluido) VALUES (?,?,?,?,?,?,0)",
            (a["data"], a["hora"], a["titulo"], a.get("descricao",""), a["tipo"], a.get("processo_vinculado",""))
        )

def concluir_compromisso(aid):
    with conectar() as conn:
        conn.execute("UPDATE agenda SET concluido=1 WHERE id=?", (aid,))

def excluir_compromisso(aid):
    with conectar() as conn:
        conn.execute("DELETE FROM agenda WHERE id=?", (aid,))


# ──────────────────────────────────────────────
# DOCUMENTOS
# ──────────────────────────────────────────────
def buscar_documentos(filtro=""):
    with conectar() as conn:
        if filtro:
            rows = conn.execute(
                "SELECT * FROM documentos WHERE titulo LIKE ? OR categoria LIKE ? ORDER BY data_modificacao DESC",
                (f"%{filtro}%", f"%{filtro}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documentos ORDER BY data_modificacao DESC").fetchall()
    return [dict(r) for r in rows]

def salvar_documento(d):
    from datetime import date
    hoje = date.today().isoformat()
    with conectar() as conn:
        conn.execute(
            "INSERT INTO documentos (titulo, categoria, conteudo, data_criacao, data_modificacao) VALUES (?,?,?,?,?)",
            (d["titulo"], d["categoria"], d["conteudo"], hoje, hoje)
        )

def atualizar_documento(did, d):
    from datetime import date
    with conectar() as conn:
        conn.execute(
            "UPDATE documentos SET titulo=?, categoria=?, conteudo=?, data_modificacao=? WHERE id=?",
            (d["titulo"], d["categoria"], d["conteudo"], date.today().isoformat(), did)
        )

def excluir_documento(did):
    with conectar() as conn:
        conn.execute("DELETE FROM documentos WHERE id=?", (did,))


# ──────────────────────────────────────────────
# JURISPRUDÊNCIA
# ──────────────────────────────────────────────
def buscar_temas(area=None):
    with conectar() as conn:
        if area:
            rows = conn.execute("SELECT * FROM juris_temas WHERE area=? ORDER BY tema", (area,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM juris_temas ORDER BY area, tema").fetchall()
    return [dict(r) for r in rows]

def salvar_tema(area, tema):
    from datetime import date
    with conectar() as conn:
        conn.execute("INSERT INTO juris_temas (area, tema, data_criacao) VALUES (?,?,?)",
                     (area, tema, date.today().isoformat()))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

def excluir_tema(tid):
    with conectar() as conn:
        conn.execute("DELETE FROM juris_temas WHERE id=?", (tid,))
        conn.execute("DELETE FROM juris_entradas WHERE tema_id=?", (tid,))

def buscar_entradas(tema_id):
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM juris_entradas WHERE tema_id=? ORDER BY data_julgamento DESC",
            (tema_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def salvar_entrada(e):
    from datetime import date
    with conectar() as conn:
        conn.execute("""
            INSERT INTO juris_entradas (tema_id, tribunal, numero_acordao, ementa, link, data_julgamento, data_cadastro)
            VALUES (?,?,?,?,?,?,?)
        """, (e["tema_id"], e["tribunal"], e["numero_acordao"], e["ementa"],
              e.get("link",""), e.get("data_julgamento",""), date.today().isoformat()))

def excluir_entrada(eid):
    with conectar() as conn:
        conn.execute("DELETE FROM juris_entradas WHERE id=?", (eid,))


# ──────────────────────────────────────────────
# CONFIGURAÇÕES
# ──────────────────────────────────────────────
def buscar_configuracoes():
    with conectar() as conn:
        rows = conn.execute("SELECT chave, valor FROM configuracoes").fetchall()
    return {r["chave"]: r["valor"] for r in rows}

def salvar_configuracao(chave, valor):
    with conectar() as conn:
        conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?,?)", (chave, valor))


# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────
def obter_resumo_dashboard():
    from datetime import date
    hoje = date.today().isoformat()
    with conectar() as conn:
        total_proc   = conn.execute("SELECT COUNT(*) FROM processos").fetchone()[0]
        total_cli    = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        receitas     = conn.execute("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Receita'").fetchone()[0]
        despesas     = conn.execute("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Despesa'").fetchone()[0]
        prazos       = conn.execute(
            "SELECT * FROM agenda WHERE concluido=0 AND data<=? ORDER BY data ASC, hora ASC LIMIT 5",
            (hoje,)
        ).fetchall()
        criticos     = conn.execute(
            "SELECT * FROM processos WHERE status='Prazo Fatal'"
        ).fetchall()
    return {
        "total_processos": total_proc,
        "total_clientes":  total_cli,
        "saldo_caixa":     receitas - despesas,
        "total_receitas":  receitas,
        "total_despesas":  despesas,
        "prazos_hoje":     [dict(r) for r in prazos],
        "alertas_criticos":[dict(r) for r in criticos],
    }


# ──────────────────────────────────────────────
# FINANCEIRO — FILTROS MENSAIS / ANUAIS
# ──────────────────────────────────────────────
def buscar_lancamentos_mes(ano, mes):
    """Retorna lançamentos de um mês específico (mes = 1..12)."""
    with conectar() as conn:
        mes_str = f"{ano}-{mes:02d}"
        rows = conn.execute(
            "SELECT * FROM financeiro WHERE data LIKE ? ORDER BY data ASC, id ASC",
            (f"{mes_str}%",)
        ).fetchall()
    return [dict(r) for r in rows]

def buscar_resumo_mensal(ano):
    """Retorna receita, despesa e saldo para cada mês do ano."""
    resultado = []
    with conectar() as conn:
        for mes in range(1, 13):
            mes_str = f"{ano}-{mes:02d}"
            rec = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Receita' AND data LIKE ?",
                (f"{mes_str}%",)
            ).fetchone()[0]
            des = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Despesa' AND data LIKE ?",
                (f"{mes_str}%",)
            ).fetchone()[0]
            resultado.append({"mes": mes, "receita": rec, "despesa": des, "saldo": rec - des})
    return resultado

def buscar_anos_disponiveis():
    """Retorna anos que possuem lançamentos."""
    with conectar() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(data,1,4) as ano FROM financeiro WHERE data != '' ORDER BY ano DESC"
        ).fetchall()
    from datetime import date
    anos = [r[0] for r in rows if r[0]]
    ano_atual = str(date.today().year)
    if ano_atual not in anos:
        anos.insert(0, ano_atual)
    return anos


# ──────────────────────────────────────────────
# CONSULTAS JURÍDICAS
# ──────────────────────────────────────────────
def inicializar_consultas():
    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            cliente TEXT DEFAULT '',
            descricao TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente',
            resposta TEXT DEFAULT '',
            data_cadastro TEXT DEFAULT ''
        )""")
        conn.commit()

def buscar_consultas(filtro=""):
    with conectar() as conn:
        if filtro:
            rows = conn.execute(
                "SELECT * FROM consultas WHERE titulo LIKE ? OR cliente LIKE ? OR status LIKE ? ORDER BY data DESC, hora DESC",
                (f"%{filtro}%",)*3
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM consultas ORDER BY data DESC, hora DESC").fetchall()
    return [dict(r) for r in rows]

def salvar_consulta(c):
    from datetime import date
    with conectar() as conn:
        conn.execute(
            "INSERT INTO consultas (titulo, data, hora, cliente, descricao, status, data_cadastro) VALUES (?,?,?,?,?,?,?)",
            (c["titulo"], c["data"], c["hora"], c.get("cliente",""), c["descricao"], "Pendente", date.today().isoformat())
        )

def atualizar_status_consulta(cid, status, resposta=""):
    with conectar() as conn:
        conn.execute("UPDATE consultas SET status=?, resposta=? WHERE id=?", (status, resposta, cid))

def excluir_consulta(cid):
    with conectar() as conn:
        conn.execute("DELETE FROM consultas WHERE id=?", (cid,))

def buscar_processos_por_cliente(nome_cliente):
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM processos WHERE cliente LIKE ? ORDER BY id DESC",
            (f"%{nome_cliente}%",)
        ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# ETAPA 1 — VÍNCULOS E NOVOS CAMPOS
# ──────────────────────────────────────────────

def migrar_etapa1():
    """Adiciona colunas e tabelas novas sem apagar dados existentes."""
    with conectar() as conn:
        c = conn.cursor()

        # Adiciona colunas novas em processos (ignora se já existir)
        for col, tipo in [
            ("cliente_id",        "INTEGER DEFAULT 0"),
            ("honorarios_total",  "REAL DEFAULT 0"),
            ("honorarios_pago",   "REAL DEFAULT 0"),
            ("data_intimacao",    "TEXT DEFAULT ''"),
            ("prazo_dias",        "INTEGER DEFAULT 0"),
            ("data_prazo",        "TEXT DEFAULT ''"),
        ]:
            try:
                c.execute(f"ALTER TABLE processos ADD COLUMN {col} {tipo}")
            except Exception:
                pass

        # Adiciona coluna processo_id em documentos e agenda
        for tabela in ["documentos", "agenda", "consultas"]:
            try:
                c.execute(f"ALTER TABLE {tabela} ADD COLUMN processo_id INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                c.execute(f"ALTER TABLE {tabela} ADD COLUMN cliente_id INTEGER DEFAULT 0")
            except Exception:
                pass

        # Tabela de andamentos do processo
        c.execute("""CREATE TABLE IF NOT EXISTS andamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processo_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT DEFAULT 'Geral',
            data_cadastro TEXT DEFAULT '',
            FOREIGN KEY(processo_id) REFERENCES processos(id) ON DELETE CASCADE
        )""")

        conn.commit()


# ── ANDAMENTOS ────────────────────────────────
def buscar_andamentos(processo_id):
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM andamentos WHERE processo_id=? ORDER BY data DESC, id DESC",
            (processo_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def salvar_andamento(a):
    from datetime import date
    with conectar() as conn:
        conn.execute(
            "INSERT INTO andamentos (processo_id, data, descricao, tipo, data_cadastro) VALUES (?,?,?,?,?)",
            (a["processo_id"], a["data"], a["descricao"], a.get("tipo","Geral"), date.today().isoformat())
        )

def excluir_andamento(aid):
    with conectar() as conn:
        conn.execute("DELETE FROM andamentos WHERE id=?", (aid,))


# ── PROCESSOS — campos novos ───────────────────
def atualizar_honorarios(pid, total, pago):
    with conectar() as conn:
        conn.execute(
            "UPDATE processos SET honorarios_total=?, honorarios_pago=? WHERE id=?",
            (total, pago, pid)
        )

def buscar_processo_por_id(pid):
    with conectar() as conn:
        row = conn.execute("SELECT * FROM processos WHERE id=?", (pid,)).fetchone()
    return dict(row) if row else None


# ── VÍNCULOS — busca cruzada ───────────────────
def buscar_agenda_por_processo(processo_id):
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM agenda WHERE processo_vinculado LIKE ? AND concluido=0 ORDER BY data ASC",
            (f"%",)
        ).fetchall()
    # Filtra por ID ou número do processo
    proc = buscar_processo_por_id(processo_id)
    if not proc:
        return []
    numero = proc.get("numero", "")
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM agenda WHERE processo_vinculado LIKE ? ORDER BY data ASC",
            (f"%{numero}%",)
        ).fetchall()
    return [dict(r) for r in rows]

def buscar_documentos_por_processo(processo_id):
    with conectar() as conn:
        row = conn.execute("SELECT numero FROM processos WHERE id=?", (processo_id,)).fetchone()
    if not row:
        return []
    # Documentos vinculados pelo campo processo_id
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos WHERE processo_id=? ORDER BY data_modificacao DESC",
            (processo_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def vincular_documento_processo(doc_id, processo_id):
    with conectar() as conn:
        conn.execute("UPDATE documentos SET processo_id=? WHERE id=?", (processo_id, doc_id))

def buscar_consultas_por_cliente(nome_cliente):
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM consultas WHERE cliente LIKE ? ORDER BY data DESC",
            (f"%{nome_cliente}%",)
        ).fetchall()
    return [dict(r) for r in rows]


# ── PESQUISA GLOBAL ────────────────────────────
def pesquisa_global(termo):
    """Busca o termo em processos, clientes, documentos e consultas."""
    resultado = {"processos": [], "clientes": [], "documentos": [], "consultas": []}
    if not termo or len(termo) < 2:
        return resultado
    t = f"%{termo}%"
    with conectar() as conn:
        resultado["processos"] = [dict(r) for r in conn.execute(
            "SELECT * FROM processos WHERE numero LIKE ? OR cliente LIKE ? OR acao LIKE ? OR status LIKE ? LIMIT 10",
            (t, t, t, t)
        ).fetchall()]
        resultado["clientes"] = [dict(r) for r in conn.execute(
            "SELECT * FROM clientes WHERE nome LIKE ? OR documento LIKE ? OR contato LIKE ? LIMIT 10",
            (t, t, t)
        ).fetchall()]
        resultado["documentos"] = [dict(r) for r in conn.execute(
            "SELECT * FROM documentos WHERE titulo LIKE ? OR categoria LIKE ? OR conteudo LIKE ? LIMIT 10",
            (t, t, t)
        ).fetchall()]
        resultado["consultas"] = [dict(r) for r in conn.execute(
            "SELECT * FROM consultas WHERE titulo LIKE ? OR cliente LIKE ? OR descricao LIKE ? LIMIT 10",
            (t, t, t)
        ).fetchall()]
    return resultado


# ──────────────────────────────────────────────
# DOUTRINA
# ──────────────────────────────────────────────
def inicializar_doutrina():
    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS doutrina_temas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT NOT NULL,
            tema TEXT NOT NULL,
            data_criacao TEXT DEFAULT ''
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS doutrina_entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema_id INTEGER NOT NULL,
            autor TEXT NOT NULL,
            obra TEXT NOT NULL,
            editora TEXT DEFAULT '',
            ano TEXT DEFAULT '',
            paginas TEXT DEFAULT '',
            trecho TEXT NOT NULL,
            data_cadastro TEXT DEFAULT '',
            FOREIGN KEY(tema_id) REFERENCES doutrina_temas(id) ON DELETE CASCADE
        )""")
        conn.commit()

def buscar_doutrina_temas(area=None):
    with conectar() as conn:
        if area:
            rows = conn.execute("SELECT * FROM doutrina_temas WHERE area=? ORDER BY tema", (area,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM doutrina_temas ORDER BY area, tema").fetchall()
    return [dict(r) for r in rows]

def salvar_doutrina_tema(area, tema):
    from datetime import date
    with conectar() as conn:
        conn.execute("INSERT INTO doutrina_temas (area, tema, data_criacao) VALUES (?,?,?)",
                     (area, tema, date.today().isoformat()))

def excluir_doutrina_tema(tid):
    with conectar() as conn:
        conn.execute("DELETE FROM doutrina_temas WHERE id=?", (tid,))
        conn.execute("DELETE FROM doutrina_entradas WHERE tema_id=?", (tid,))

def buscar_doutrina_entradas(tema_id):
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM doutrina_entradas WHERE tema_id=? ORDER BY autor",
            (tema_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def salvar_doutrina_entrada(e):
    from datetime import date
    with conectar() as conn:
        conn.execute("""INSERT INTO doutrina_entradas
            (tema_id, autor, obra, editora, ano, paginas, trecho, data_cadastro)
            VALUES (?,?,?,?,?,?,?,?)""",
            (e["tema_id"], e["autor"], e["obra"], e.get("editora",""),
             e.get("ano",""), e.get("paginas",""), e["trecho"],
             date.today().isoformat()))

def excluir_doutrina_entrada(eid):
    with conectar() as conn:
        conn.execute("DELETE FROM doutrina_entradas WHERE id=?", (eid,))


# ──────────────────────────────────────────────
# ETAPA 2 — PRAZOS E ALERTAS
# ──────────────────────────────────────────────

def migrar_etapa2():
    """Adiciona tabela de alertas e colunas de prazo processual."""
    with conectar() as conn:
        c = conn.cursor()
        # Tabela de alertas/notificações do sistema
        c.execute("""CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT DEFAULT '',
            data_referencia TEXT NOT NULL,
            processo_id INTEGER DEFAULT 0,
            agenda_id INTEGER DEFAULT 0,
            lido INTEGER DEFAULT 0,
            data_criacao TEXT DEFAULT ''
        )""")
        conn.commit()


def calcular_data_prazo(data_inicio_iso, dias):
    """Calcula a data final de um prazo em dias corridos."""
    from datetime import date, timedelta
    try:
        inicio = date.fromisoformat(data_inicio_iso)
        fim = inicio + timedelta(days=dias)
        return fim.isoformat()
    except Exception:
        return ""


def buscar_prazos_urgentes(dias_antecedencia=7):
    """Retorna compromissos e processos com prazo nos próximos N dias."""
    from datetime import date, timedelta
    hoje = date.today()
    limite = (hoje + timedelta(days=dias_antecedencia)).isoformat()
    hoje_iso = hoje.isoformat()

    with conectar() as conn:
        # Agenda com prazo até o limite
        agenda = conn.execute("""
            SELECT *, 
                   CASE 
                     WHEN data < ? THEN 'vencido'
                     WHEN data = ? THEN 'hoje'
                     WHEN data <= ? THEN 'urgente'
                     ELSE 'normal'
                   END as urgencia
            FROM agenda 
            WHERE concluido=0 AND data <= ?
            ORDER BY data ASC, hora ASC
        """, (hoje_iso, hoje_iso, limite, limite)).fetchall()

        # Processos com prazo fatal
        criticos = conn.execute("""
            SELECT * FROM processos WHERE status='Prazo Fatal'
        """).fetchall()

    return {
        "agenda_urgente": [dict(r) for r in agenda],
        "processos_criticos": [dict(r) for r in criticos],
    }


def buscar_resumo_alertas():
    """Retorna contagem de alertas para o dashboard."""
    from datetime import date, timedelta
    hoje = date.today().isoformat()
    amanha = (date.today() + timedelta(days=1)).isoformat()
    semana = (date.today() + timedelta(days=7)).isoformat()

    with conectar() as conn:
        vencidos = conn.execute(
            "SELECT COUNT(*) FROM agenda WHERE concluido=0 AND data < ?", (hoje,)
        ).fetchone()[0]
        hoje_count = conn.execute(
            "SELECT COUNT(*) FROM agenda WHERE concluido=0 AND data = ?", (hoje,)
        ).fetchone()[0]
        semana_count = conn.execute(
            "SELECT COUNT(*) FROM agenda WHERE concluido=0 AND data > ? AND data <= ?",
            (hoje, semana)
        ).fetchone()[0]
        criticos = conn.execute(
            "SELECT COUNT(*) FROM processos WHERE status='Prazo Fatal'"
        ).fetchone()[0]

    return {
        "vencidos":  vencidos,
        "hoje":      hoje_count,
        "semana":    semana_count,
        "criticos":  criticos,
        "total":     vencidos + hoje_count + criticos,
    }


# ──────────────────────────────────────────────
# ETAPA 3 — DOCUMENTOS AVANÇADOS
# ──────────────────────────────────────────────

def migrar_etapa3():
    """Adiciona campo de variáveis e categoria nos documentos."""
    with conectar() as conn:
        c = conn.cursor()
        for col, tipo in [
            ("tags",      "TEXT DEFAULT ''"),
            ("favorito",  "INTEGER DEFAULT 0"),
            ("versao",    "INTEGER DEFAULT 1"),
        ]:
            try:
                c.execute(f"ALTER TABLE documentos ADD COLUMN {col} {tipo}")
            except Exception:
                pass
        conn.commit()

def buscar_documentos_favoritos():
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM documentos WHERE favorito=1 ORDER BY data_modificacao DESC"
        ).fetchall()
    return [dict(r) for r in rows]

def toggle_favorito(doc_id):
    with conectar() as conn:
        atual = conn.execute("SELECT favorito FROM documentos WHERE id=?", (doc_id,)).fetchone()
        novo = 0 if (atual and atual[0]) else 1
        conn.execute("UPDATE documentos SET favorito=? WHERE id=?", (novo, doc_id))

def buscar_variaveis_processo(numero_processo):
    """Retorna dict com variáveis para substituição no documento."""
    with conectar() as conn:
        p = conn.execute(
            "SELECT * FROM processos WHERE numero LIKE ?", (f"%{numero_processo}%",)
        ).fetchone()
        if not p:
            return {}
        p = dict(p)
        c = conn.execute(
            "SELECT * FROM clientes WHERE nome=?", (p.get("cliente",""),)
        ).fetchone()
        cliente = dict(c) if c else {}
    from datetime import date
    return {
        "numero_processo":   p.get("numero",""),
        "cliente":           p.get("cliente",""),
        "acao":              p.get("acao",""),
        "status":            p.get("status",""),
        "data_distribuicao": p.get("data_distribuicao",""),
        "cpf_cnpj":          cliente.get("documento",""),
        "contato_cliente":   cliente.get("contato",""),
        "email_cliente":     cliente.get("email",""),
        "data_hoje":         date.today().strftime("%d/%m/%Y"),
        "ano_atual":         str(date.today().year),
    }


# ──────────────────────────────────────────────
# USUÁRIOS E LOGIN
# ──────────────────────────────────────────────
import hashlib

def _hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_usuarios():
    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL,
            ativo INTEGER DEFAULT 1,
            data_criacao TEXT DEFAULT ''
        )""")
        # Criar admin padrão se não existir
        existe = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if existe == 0:
            from datetime import date
            conn.execute("""INSERT INTO usuarios (nome, login, senha_hash, perfil, data_criacao)
                VALUES (?,?,?,?,?)""",
                ("Administrador", "admin", _hash_senha("admin123"),
                 "Administrador", date.today().isoformat()))
        conn.commit()

def autenticar(login, senha):
    with conectar() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE login=? AND senha_hash=? AND ativo=1",
            (login, _hash_senha(senha))
        ).fetchone()
    return dict(row) if row else None

def buscar_usuarios():
    with conectar() as conn:
        rows = conn.execute("SELECT * FROM usuarios ORDER BY perfil, nome").fetchall()
    return [dict(r) for r in rows]

def salvar_usuario(u):
    from datetime import date
    with conectar() as conn:
        conn.execute("""INSERT INTO usuarios (nome, login, senha_hash, perfil, ativo, data_criacao)
            VALUES (?,?,?,?,1,?)""",
            (u["nome"], u["login"], _hash_senha(u["senha"]),
             u["perfil"], date.today().isoformat()))

def atualizar_usuario(uid, u):
    with conectar() as conn:
        if u.get("senha"):
            conn.execute("""UPDATE usuarios SET nome=?, login=?, senha_hash=?, perfil=?, ativo=?
                WHERE id=?""",
                (u["nome"], u["login"], _hash_senha(u["senha"]),
                 u["perfil"], u.get("ativo", 1), uid))
        else:
            conn.execute("""UPDATE usuarios SET nome=?, login=?, perfil=?, ativo=?
                WHERE id=?""",
                (u["nome"], u["login"], u["perfil"], u.get("ativo", 1), uid))

def excluir_usuario(uid):
    with conectar() as conn:
        conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))

def alterar_senha(uid, senha_nova):
    with conectar() as conn:
        conn.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",
                     (_hash_senha(senha_nova), uid))

def salvar_logo_escritorio(caminho_origem):
    """Copia a logo para a pasta de dados do Legis."""
    import shutil, sys
    if getattr(sys, 'frozen', False):
        destino_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Legis')
    else:
        destino_dir = os.path.dirname(DB_PATH)
    os.makedirs(destino_dir, exist_ok=True)
    ext = os.path.splitext(caminho_origem)[1]
    destino = os.path.join(destino_dir, f"logo_escritorio{ext}")
    shutil.copy2(caminho_origem, destino)
    salvar_configuracao("logo_escritorio", destino)
    return destino

def get_logo_escritorio():
    cfg = buscar_configuracoes()
    caminho = cfg.get("logo_escritorio", "")
    if caminho and os.path.exists(caminho):
        return caminho
    return None




# ──────────────────────────────────────────────
# ETAPA 4 — AVALIAÇÕES E APRENDIZADO
# ──────────────────────────────────────────────
def migrar_etapa4():
    """Cria a tabela de avaliações de peças."""
    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS avaliacoes_pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_id INTEGER,
            titulo TEXT,
            categoria TEXT,
            tipo_peca TEXT,
            area TEXT,
            nota INTEGER,
            observacoes TEXT,
            conteudo TEXT,
            data_avaliacao TEXT
        )""")
        conn.commit()


def salvar_avaliacao(dados):
    from datetime import datetime
    with conectar() as conn:
        existente = None
        if dados.get("documento_id"):
            existente = conn.execute(
                "SELECT id FROM avaliacoes_pecas WHERE documento_id=?",
                (dados.get("documento_id"),)
            ).fetchone()
        if existente:
            conn.execute("""UPDATE avaliacoes_pecas SET
                titulo=?, categoria=?, tipo_peca=?, area=?, nota=?,
                observacoes=?, conteudo=?, data_avaliacao=? WHERE id=?""",
                (dados.get("titulo",""), dados.get("categoria",""),
                 dados.get("tipo_peca",""), dados.get("area",""),
                 dados.get("nota",0), dados.get("observacoes",""),
                 dados.get("conteudo",""), datetime.now().isoformat(),
                 existente["id"]))
        else:
            conn.execute("""INSERT INTO avaliacoes_pecas
                (documento_id, titulo, categoria, tipo_peca, area, nota,
                 observacoes, conteudo, data_avaliacao)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (dados.get("documento_id"), dados.get("titulo",""),
                 dados.get("categoria",""), dados.get("tipo_peca",""),
                 dados.get("area",""), dados.get("nota",0),
                 dados.get("observacoes",""), dados.get("conteudo",""),
                 datetime.now().isoformat()))
        conn.commit()


def buscar_avaliacao_documento(documento_id):
    with conectar() as conn:
        row = conn.execute(
            "SELECT * FROM avaliacoes_pecas WHERE documento_id=?",
            (documento_id,)
        ).fetchone()
    return dict(row) if row else None


def buscar_avaliacoes(nota_minima=None, nota_maxima=None, area=None, limite=50):
    q = "SELECT * FROM avaliacoes_pecas WHERE 1=1"
    params = []
    if nota_minima is not None:
        q += " AND nota >= ?"; params.append(nota_minima)
    if nota_maxima is not None:
        q += " AND nota <= ?"; params.append(nota_maxima)
    if area:
        q += " AND area = ?"; params.append(area)
    q += " ORDER BY nota DESC, data_avaliacao DESC LIMIT ?"
    params.append(limite)
    with conectar() as conn:
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def estatisticas_avaliacoes():
    with conectar() as conn:
        total = conn.execute("SELECT COUNT(*) FROM avaliacoes_pecas").fetchone()[0]
        media = conn.execute("SELECT AVG(nota) FROM avaliacoes_pecas").fetchone()[0]
        boas = conn.execute("SELECT COUNT(*) FROM avaliacoes_pecas WHERE nota >= 4").fetchone()[0]
        ruins = conn.execute("SELECT COUNT(*) FROM avaliacoes_pecas WHERE nota <= 2").fetchone()[0]
    return {"total": total, "media": round(media, 1) if media else 0,
            "boas": boas, "ruins": ruins}


def excluir_avaliacao(aval_id):
    with conectar() as conn:
        conn.execute("DELETE FROM avaliacoes_pecas WHERE id=?", (aval_id,))
        conn.commit()


def construir_contexto_aprendizado(area=None, tipo_peca=None, max_exemplos=2):
    """
    Monta contexto com peças bem avaliadas (modelo) e mal avaliadas (evitar).
    """
    partes = []
    boas = buscar_avaliacoes(nota_minima=4, area=area, limite=max_exemplos)
    if not boas:
        boas = buscar_avaliacoes(nota_minima=4, limite=max_exemplos)
    if boas:
        partes.append("## EXEMPLOS DE PEÇAS BEM AVALIADAS PELO ADVOGADO (siga este padrão de qualidade)")
        for b in boas:
            obs = f" Observação do advogado: {b['observacoes']}" if b.get("observacoes") else ""
            trecho = (b.get("conteudo") or "")[:1500]
            partes.append(f"### {b.get('tipo_peca','Peça')} (nota {b['nota']}/5){obs}\n{trecho}")
    ruins = buscar_avaliacoes(nota_maxima=2, limite=3)
    ruins_com_obs = [r for r in ruins if r.get("observacoes")]
    if ruins_com_obs:
        partes.append("\n## PONTOS A EVITAR (com base em peças que o advogado avaliou mal)")
        for r in ruins_com_obs:
            partes.append(f"- {r['observacoes']}")
    return "\n\n".join(partes) if partes else ""


# ──────────────────────────────────────────────
# ETAPA 5 — INDEXAÇÃO INTELIGENTE (metadados de IA)
# ──────────────────────────────────────────────
def migrar_etapa5():
    """Cria a tabela de metadados inteligentes gerados pela IA."""
    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS metadados_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_fonte TEXT,
            fonte_id INTEGER,
            resumo TEXT,
            area TEXT,
            palavras_chave TEXT,
            data_analise TEXT,
            UNIQUE(tipo_fonte, fonte_id)
        )""")
        conn.commit()


def salvar_metadados_ia(tipo_fonte, fonte_id, resumo, area, palavras_chave):
    from datetime import datetime
    with conectar() as conn:
        conn.execute("""INSERT INTO metadados_ia
            (tipo_fonte, fonte_id, resumo, area, palavras_chave, data_analise)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(tipo_fonte, fonte_id) DO UPDATE SET
                resumo=excluded.resumo, area=excluded.area,
                palavras_chave=excluded.palavras_chave,
                data_analise=excluded.data_analise""",
            (tipo_fonte, fonte_id, resumo, area, palavras_chave,
             datetime.now().isoformat()))
        conn.commit()


def buscar_metadados_ia(tipo_fonte=None, palavra=None, area=None, limite=20):
    q = "SELECT * FROM metadados_ia WHERE 1=1"
    params = []
    if tipo_fonte:
        q += " AND tipo_fonte=?"; params.append(tipo_fonte)
    if area:
        q += " AND area LIKE ?"; params.append(f"%{area}%")
    if palavra:
        q += " AND (palavras_chave LIKE ? OR resumo LIKE ?)"
        params.extend([f"%{palavra}%", f"%{palavra}%"])
    q += " ORDER BY data_analise DESC LIMIT ?"
    params.append(limite)
    with conectar() as conn:
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def estatisticas_metadados_ia():
    with conectar() as conn:
        total = conn.execute("SELECT COUNT(*) FROM metadados_ia").fetchone()[0]
    return {"total": total}


# ──────────────────────────────────────────────
# CENTRAL DE MONITORAMENTO DE PROCESSOS (Datajud)
# ──────────────────────────────────────────────
def migrar_monitoramento():
    """Cria a tabela de processos monitorados."""
    with conectar() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS processos_monitorados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT UNIQUE,
            tribunal TEXT,
            cliente TEXT,
            ultima_movimentacao TEXT,
            data_ultima_mov TEXT,
            resumo_ia TEXT,
            tag_ia TEXT,
            tem_novidade INTEGER DEFAULT 0,
            data_cadastro TEXT,
            data_atualizacao TEXT
        )""")
        conn.commit()


def cadastrar_processo_monitorado(numero, tribunal, cliente, ultima_mov="", data_mov=""):
    from datetime import datetime
    agora = datetime.now().isoformat()
    with conectar() as conn:
        existe = conn.execute(
            "SELECT id FROM processos_monitorados WHERE numero_processo=?",
            (numero,)).fetchone()
        if existe:
            conn.execute("""UPDATE processos_monitorados SET
                tribunal=?, cliente=?, ultima_movimentacao=?, data_ultima_mov=?,
                data_atualizacao=? WHERE numero_processo=?""",
                (tribunal, cliente, ultima_mov, data_mov, agora, numero))
            conn.commit()
            return existe["id"], False  # já existia
        else:
            cur = conn.execute("""INSERT INTO processos_monitorados
                (numero_processo, tribunal, cliente, ultima_movimentacao,
                 data_ultima_mov, data_cadastro, data_atualizacao)
                VALUES (?,?,?,?,?,?,?)""",
                (numero, tribunal, cliente, ultima_mov, data_mov, agora, agora))
            conn.commit()
            return cur.lastrowid, True  # novo


def listar_processos_monitorados():
    with conectar() as conn:
        rows = conn.execute(
            "SELECT * FROM processos_monitorados ORDER BY data_ultima_mov DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def atualizar_movimentacao_processo(numero, ultima_mov, data_mov, tem_novidade=False,
                                     resumo_ia=None, tag_ia=None):
    from datetime import datetime
    with conectar() as conn:
        # Buscar a movimentação anterior para detectar novidade
        atual = conn.execute(
            "SELECT ultima_movimentacao FROM processos_monitorados WHERE numero_processo=?",
            (numero,)).fetchone()
        novidade = 1 if (atual and atual["ultima_movimentacao"] != ultima_mov) else (1 if tem_novidade else 0)

        campos = ["ultima_movimentacao=?", "data_ultima_mov=?", "tem_novidade=?", "data_atualizacao=?"]
        valores = [ultima_mov, data_mov, novidade, datetime.now().isoformat()]
        if resumo_ia is not None:
            campos.append("resumo_ia=?"); valores.append(resumo_ia)
        if tag_ia is not None:
            campos.append("tag_ia=?"); valores.append(tag_ia)
        valores.append(numero)
        conn.execute(f"UPDATE processos_monitorados SET {', '.join(campos)} WHERE numero_processo=?", valores)
        conn.commit()


def marcar_processo_visto(numero):
    with conectar() as conn:
        conn.execute("UPDATE processos_monitorados SET tem_novidade=0 WHERE numero_processo=?", (numero,))
        conn.commit()


def remover_processo_monitorado(numero):
    with conectar() as conn:
        conn.execute("DELETE FROM processos_monitorados WHERE numero_processo=?", (numero,))
        conn.commit()
