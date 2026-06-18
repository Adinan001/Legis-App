# core/ai/rag.py — Sistema RAG (Retrieval-Augmented Generation)
"""
Indexa jurisprudência e doutrina em um banco vetorial (ChromaDB) usando
embeddings locais (multilingual-e5-large), permitindo que a IA recupere
trechos relevantes para fundamentar peças e responder consultas.

Roda 100% offline após o download inicial do modelo de embeddings.
"""
import os
import sys


def _data_dir():
    if getattr(sys, "frozen", False):
        d = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Legis")
    else:
        d = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.makedirs(d, exist_ok=True)
    return d


CHROMA_PATH = os.path.join(_data_dir(), "rag_db")
MODELO_EMBEDDING = "intfloat/multilingual-e5-large"


class RAGError(Exception):
    pass


class LegisRAG:
    """Gerencia indexação e busca vetorial de jurisprudência e doutrina."""

    _embedder = None  # cache do modelo (carregado uma vez)

    def __init__(self):
        try:
            import chromadb
        except ImportError:
            raise RAGError("Biblioteca 'chromadb' não instalada. Execute: pip install chromadb")

        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.col_juris = self.client.get_or_create_collection("jurisprudencia")
        self.col_doutrina = self.client.get_or_create_collection("doutrina")

    @classmethod
    def _get_embedder(cls):
        """Carrega o modelo de embeddings uma única vez (lazy load)."""
        if cls._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise RAGError(
                    "Biblioteca 'sentence-transformers' não instalada.\n"
                    "Execute: pip install sentence-transformers")
            cls._embedder = SentenceTransformer(MODELO_EMBEDDING)
        return cls._embedder

    def _embed(self, textos, prefixo="passage"):
        """Gera embeddings. O modelo e5 espera prefixos 'query:' ou 'passage:'."""
        embedder = self._get_embedder()
        textos_pref = [f"{prefixo}: {t}" for t in textos]
        return embedder.encode(textos_pref, normalize_embeddings=True).tolist()

    def _chunks(self, texto, tam=900, overlap=150):
        """Divide texto em pedaços com sobreposição."""
        if not texto:
            return []
        palavras = texto.split()
        chunks, atual, contagem = [], [], 0
        for p in palavras:
            atual.append(p)
            contagem += len(p) + 1
            if contagem >= tam:
                chunks.append(" ".join(atual))
                # overlap: mantém últimas palavras
                volta = " ".join(atual)[-overlap:]
                atual = volta.split()
                contagem = len(volta)
        if atual:
            chunks.append(" ".join(atual))
        return chunks

    # ── INDEXAÇÃO ──
    def indexar_jurisprudencia(self, entrada_id, tribunal, numero, ementa, tema=""):
        texto = f"{tribunal} {numero}. {ementa}"
        self._indexar(self.col_juris, f"juris_{entrada_id}", texto,
                      {"tipo": "jurisprudencia", "tribunal": tribunal,
                       "numero": numero, "tema": tema, "entrada_id": str(entrada_id)})

    def indexar_doutrina(self, entrada_id, autor, obra, trecho, tema=""):
        texto = f"{autor}. {obra}. {trecho}"
        self._indexar(self.col_doutrina, f"dout_{entrada_id}", texto,
                      {"tipo": "doutrina", "autor": autor, "obra": obra,
                       "tema": tema, "entrada_id": str(entrada_id)})

    def _indexar(self, colecao, base_id, texto, metadados):
        # Remove versões antigas dessa entrada
        try:
            existentes = colecao.get(where={"entrada_id": metadados["entrada_id"]})
            if existentes and existentes.get("ids"):
                colecao.delete(ids=existentes["ids"])
        except Exception:
            pass

        chunks = self._chunks(texto)
        if not chunks:
            return
        embeddings = self._embed(chunks, prefixo="passage")
        ids = [f"{base_id}_c{i}" for i in range(len(chunks))]
        metas = [dict(metadados, chunk=i) for i in range(len(chunks))]
        colecao.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metas)

    def remover_jurisprudencia(self, entrada_id):
        self._remover(self.col_juris, entrada_id)

    def remover_doutrina(self, entrada_id):
        self._remover(self.col_doutrina, entrada_id)

    def _remover(self, colecao, entrada_id):
        try:
            existentes = colecao.get(where={"entrada_id": str(entrada_id)})
            if existentes and existentes.get("ids"):
                colecao.delete(ids=existentes["ids"])
        except Exception:
            pass

    # ── BUSCA ──
    def buscar_contexto(self, query, n_juris=4, n_doutrina=3):
        """Retorna texto formatado com os trechos mais relevantes."""
        partes = []
        q_emb = self._embed([query], prefixo="query")

        # Jurisprudência
        try:
            if self.col_juris.count() > 0:
                res = self.col_juris.query(query_embeddings=q_emb,
                                           n_results=min(n_juris, self.col_juris.count()))
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                if docs:
                    partes.append("### JURISPRUDÊNCIA RELEVANTE")
                    for doc, meta in zip(docs, metas):
                        ref = f"{meta.get('tribunal','')} {meta.get('numero','')}".strip()
                        partes.append(f"[{ref}] {doc}")
        except Exception:
            pass

        # Doutrina
        try:
            if self.col_doutrina.count() > 0:
                res = self.col_doutrina.query(query_embeddings=q_emb,
                                              n_results=min(n_doutrina, self.col_doutrina.count()))
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                if docs:
                    partes.append("\n### DOUTRINA RELEVANTE")
                    for doc, meta in zip(docs, metas):
                        ref = f"{meta.get('autor','')}, {meta.get('obra','')}".strip(", ")
                        partes.append(f"[{ref}] {doc}")
        except Exception:
            pass

        return "\n\n".join(partes) if partes else ""

    def estatisticas(self):
        try:
            return {"jurisprudencia": self.col_juris.count(),
                    "doutrina": self.col_doutrina.count()}
        except Exception:
            return {"jurisprudencia": 0, "doutrina": 0}


def rag_disponivel():
    """Verifica se as bibliotecas do RAG estão instaladas."""
    try:
        import chromadb  # noqa
        import sentence_transformers  # noqa
        return True
    except ImportError:
        return False
