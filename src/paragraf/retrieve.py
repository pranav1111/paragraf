"""Two-stage retrieval: hybrid candidates (keyword + dense, fused with RRF), then cross-encoder reranking.

Modes exist for the evaluation (Phase 9): every mode gets the same candidate budget and the same
post-processing (language-twin removal, top-k), so the comparison between them is fair.
"""
from collections import defaultdict
from dataclasses import dataclass

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import CrossEncoder, SentenceTransformer

from paragraf.config import settings

MODES = ("keyword", "dense", "hybrid", "hybrid+rerank")
COLUMNS = "id, law, lang, article, title, url, content"

# Keyword search = BM25 over PostgreSQL's own stemmed lexemes (sql/schema.sql: chunk_terms, chunk_len,
# term_df, lang_stats). The question is stemmed with both language configurations; each chunk is scored
# with its own language's statistics. BM25 weights rare words (IDF) and saturates repeated words (k1)
# and normalises for chunk length (b).
BM25_SQL = """
WITH q AS (
  SELECT 'en'::text AS lang, t AS term FROM unnest(tsvector_to_array(to_tsvector('english', %(q)s))) t
  UNION
  SELECT 'de'::text, t FROM unnest(tsvector_to_array(to_tsvector('german', %(q)s))) t
)
SELECT ct.id
FROM q
JOIN chunk_terms ct ON ct.lang = q.lang AND ct.term = q.term
JOIN term_df     df ON df.lang = q.lang AND df.term = q.term
JOIN chunk_len   cl ON cl.id = ct.id
JOIN lang_stats  ls ON ls.lang = q.lang
GROUP BY ct.id
ORDER BY sum(
    ln(1 + (ls.n - df.df + 0.5) / (df.df + 0.5))                                  -- IDF: rare = important
  * ct.tf * (%(k1)s + 1)
  / (ct.tf + %(k1)s * (1 - %(b)s + %(b)s * cl.len / ls.avgdl))                    -- tf saturation, length norm
) DESC, ct.id
LIMIT %(k)s
"""
BM25_K1, BM25_B = 1.2, 0.75

# The first version (kept for comparison): OR semantics ranked with ts_rank_cd, which has no IDF.
TSRANK_SQL = """
WITH q AS (
  SELECT to_tsquery('english', replace(plainto_tsquery('english', %(q)s)::text, ' & ', ' | ')) AS en,
         to_tsquery('german',  replace(plainto_tsquery('german',  %(q)s)::text, ' & ', ' | ')) AS de
)
SELECT c.id
FROM chunks c, q
WHERE (c.lang = 'en' AND c.tsv @@ q.en) OR (c.lang = 'de' AND c.tsv @@ q.de)
ORDER BY ts_rank_cd(c.tsv, CASE WHEN c.lang = 'en' THEN q.en ELSE q.de END) DESC, c.id
LIMIT %(k)s
"""
DENSE_SQL = "SELECT id FROM chunks ORDER BY embedding <=> %s LIMIT %s"


@dataclass
class Hit:
    id: str
    law: str
    lang: str
    article: str
    title: str
    url: str
    content: str
    score: float = 0.0

    @property
    def article_key(self) -> str:                    # "GDPR-art33", the same for both languages
        return f"{self.law}-art{self.article}"


def rrf(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Reciprocal Rank Fusion: score(d) = sum over lists of 1 / (k + rank of d in that list)."""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores, key=lambda d: (-scores[d], d))


def drop_twins(hits: list[Hit]) -> list[Hit]:
    """Keep only the better-ranked language version of each chunk (GDPR-en-art33-c0 / GDPR-de-art33-c0)."""
    seen, result = set(), []
    for h in hits:
        twin_key = h.id.replace(f"-{h.lang}-", "-", 1)
        if twin_key not in seen:
            seen.add(twin_key)
            result.append(h)
    return result


class Retriever:
    def __init__(self) -> None:
        self.conn = psycopg.connect(settings.database_url, autocommit=True)
        register_vector(self.conn)
        self.embedder = SentenceTransformer(settings.embed_model, device=settings.device)
        self.reranker = CrossEncoder(settings.rerank_model, device=settings.device, max_length=512)

    def keyword(self, query: str, k: int) -> list[str]:
        params = {"q": query, "k": k, "k1": BM25_K1, "b": BM25_B}
        return [row[0] for row in self.conn.execute(BM25_SQL, params)]

    def keyword_tsrank(self, query: str, k: int) -> list[str]:
        return [row[0] for row in self.conn.execute(TSRANK_SQL, {"q": query, "k": k})]

    def dense(self, query: str, k: int) -> list[str]:
        qvec = self.embedder.encode(query, normalize_embeddings=True)
        return [row[0] for row in self.conn.execute(DENSE_SQL, (qvec, k))]

    def fetch(self, ids: list[str]) -> list[Hit]:
        rows = self.conn.execute(f"SELECT {COLUMNS} FROM chunks WHERE id = ANY(%s)", (ids,))
        by_id = {r[0]: Hit(*r) for r in rows}
        return [by_id[i] for i in ids if i in by_id]   # keep the ranking order

    def rerank(self, query: str, hits: list[Hit]) -> list[Hit]:
        scores = self.reranker.predict([(query, h.content) for h in hits], batch_size=16)
        for h, s in zip(hits, scores):
            h.score = float(s)
        return sorted(hits, key=lambda h: h.score, reverse=True)

    def search(self, query: str, mode: str = "hybrid+rerank", top_k: int | None = None) -> list[Hit]:
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}; choose from {MODES}")
        n, top_k = settings.candidates, top_k or settings.top_k
        if mode == "keyword":
            hits = self.fetch(self.keyword(query, n))
        elif mode == "dense":
            hits = self.fetch(self.dense(query, n))
        else:
            hits = self.fetch(rrf([self.keyword(query, n), self.dense(query, n)])[:n])
            if mode == "hybrid+rerank":
                hits = self.rerank(query, hits)
        return drop_twins(hits)[:top_k]
