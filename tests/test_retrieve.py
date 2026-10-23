import pytest

from paragraf.retrieve import Hit, drop_twins, rrf


def test_rrf_matches_the_guide_example():
    keyword = ["A", "C", "D", "B"]
    dense = ["C", "B", "A", "E"]
    assert rrf([keyword, dense]) == ["C", "A", "B", "D", "E"]


def test_rrf_rewards_agreement_over_a_single_first_place():
    # X is first in one list only; Y is second in both lists -> Y wins
    assert rrf([["X", "Y"], ["Z", "Y"]])[0] == "Y"


def _hit(chunk_id: str) -> Hit:
    law, lang, art, _ = chunk_id.split("-")
    return Hit(chunk_id, law, lang, art[3:], "t", "u", "c")


def test_drop_twins_keeps_the_better_ranked_language_and_other_chunks():
    hits = [_hit("GDPR-de-art33-c0"), _hit("GDPR-en-art33-c0"), _hit("GDPR-en-art33-c1")]
    assert [h.id for h in drop_twins(hits)] == ["GDPR-de-art33-c0", "GDPR-en-art33-c1"]


def test_article_key_is_language_free():
    assert _hit("NIS2-de-art23-c2").article_key == _hit("NIS2-en-art23-c0").article_key == "NIS2-art23"


# --- integration: needs the database (BM25 views) -------------------------------------------------
@pytest.mark.integration
def test_bm25_weights_rare_terms():
    import psycopg

    from paragraf.config import settings
    from paragraf.retrieve import BM25_B, BM25_K1, BM25_SQL

    try:
        conn = psycopg.connect(settings.database_url, connect_timeout=3)
    except psycopg.OperationalError:
        pytest.skip("database not running")
    with conn:
        ids = [r[0] for r in conn.execute(BM25_SQL, {"q": "What does Article 50 of the AI Act require?",
                                                     "k": 5, "k1": BM25_K1, "b": BM25_B})]
    if not ids:
        pytest.skip("index is empty")
    assert ids[0].startswith("AIACT-en-art50-")      # the rare term "50" decides, not "article"/"AI"
