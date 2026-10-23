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
