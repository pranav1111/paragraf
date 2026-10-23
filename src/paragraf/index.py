"""Embed every chunk with bge-m3 and load it into PostgreSQL (idempotent: safe to re-run)."""
import json
import time
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from paragraf.config import settings

TS_CONFIG = {"en": "english", "de": "german"}
SRC = Path("data/processed/chunks.jsonl")

UPSERT = """
INSERT INTO chunks (id, law, lang, article, title, url, content, ts_config, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s::regconfig, %s)
ON CONFLICT (id) DO UPDATE SET
    law = EXCLUDED.law, lang = EXCLUDED.lang, article = EXCLUDED.article, title = EXCLUDED.title,
    url = EXCLUDED.url, content = EXCLUDED.content, ts_config = EXCLUDED.ts_config,
    embedding = EXCLUDED.embedding
"""


def main() -> None:
    chunks = [json.loads(line) for line in SRC.open(encoding="utf-8")]
    model = SentenceTransformer(settings.embed_model, device=settings.device)

    start = time.perf_counter()
    vectors = model.encode([c["content"] for c in chunks], batch_size=16,
                           normalize_embeddings=True, show_progress_bar=True)
    seconds = time.perf_counter() - start
    print(f"embedded {len(chunks)} chunks in {seconds:.0f} s "
          f"({len(chunks) / seconds:.1f} chunks/s on {settings.device}), dim {vectors.shape[1]}")

    rows = [(c["id"], c["law"], c["lang"], c["article"], c["title"], c["url"], c["content"],
             TS_CONFIG[c["lang"]], v) for c, v in zip(chunks, vectors)]
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.executemany(UPSERT, rows)
        conn.commit()
        conn.execute("ANALYZE chunks")             # fresh statistics so the planner uses the HNSW index
        total = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    print(f"{total} rows in chunks")


if __name__ == "__main__":
    main()
