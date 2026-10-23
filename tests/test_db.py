"""Integration tests: need the database from docker-compose.yml (`docker compose up -d`)."""
import psycopg
import pytest

from paragraf.config import settings

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def conn():
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3, autocommit=True) as c:
            yield c
    except psycopg.OperationalError:
        pytest.skip("database not running (docker compose up -d)")


def test_schema_has_both_search_indexes(conn):
    rows = conn.execute("SELECT indexdef FROM pg_indexes WHERE tablename = 'chunks'").fetchall()
    defs = " ".join(r[0] for r in rows)
    assert "USING gin (tsv)" in defs
    assert "USING hnsw (embedding vector_cosine_ops)" in defs


def test_tsvector_is_generated_with_language_specific_stemming(conn):
    with conn.transaction(force_rollback=True):
        conn.execute(
            "INSERT INTO chunks (id, law, lang, article, title, url, content, ts_config) VALUES "
            "('t-en-art1-c0','GDPR','en','1','t','u','processing of data', 'english'),"
            "('t-de-art1-c0','GDPR','de','1','t','u','Verarbeitung von Daten', 'german')")
        tsv = dict(conn.execute("SELECT lang, tsv::text FROM chunks WHERE id LIKE 't-%'").fetchall())
    assert "'process'" in tsv["en"]
    assert "'verarbeit'" in tsv["de"]


def test_index_is_complete_and_normalised(conn):
    total = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    if total == 0:
        pytest.skip("index is empty (run python -m paragraf.index)")
    per_lang = dict(conn.execute("SELECT lang, count(*) FROM chunks GROUP BY lang").fetchall())
    assert per_lang["en"] == per_lang["de"]
    assert conn.execute("SELECT count(*) FROM chunks WHERE embedding IS NULL").fetchone()[0] == 0
    lo, hi = conn.execute("SELECT min(vector_norm(embedding)), max(vector_norm(embedding)) FROM chunks").fetchone()
    assert abs(lo - 1) < 1e-3 and abs(hi - 1) < 1e-3          # normalised: cosine == dot product
