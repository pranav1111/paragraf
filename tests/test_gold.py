"""Structural checks for eval/gold.jsonl (content is checked by a human with scripts/review_gold.py)."""
import json
from pathlib import Path

import pytest

GOLD = Path("eval/gold.jsonl")
ARTICLES = Path("data/processed/articles.jsonl")
TYPES = {"direct", "paraphrase", "exact_ref", "cross_law", "unanswerable"}


@pytest.fixture(scope="module")
def gold():
    return [json.loads(line) for line in GOLD.open(encoding="utf-8")]


def test_ids_unique_and_fields_present(gold):
    assert len({g["id"] for g in gold}) == len(gold)
    for g in gold:
        assert g["type"] in TYPES and g["lang"] in {"en", "de"}
        assert len(g["question"]) >= 3 and g["reference"]


def test_unanswerable_iff_no_gold_and_cross_law_has_two(gold):
    for g in gold:
        assert (g["type"] == "unanswerable") == (g["gold"] == [])
        if g["type"] == "cross_law":
            assert len(g["gold"]) == 2


@pytest.mark.skipif(not ARTICLES.exists(), reason="run the ingest first")
def test_every_gold_article_exists_in_the_corpus(gold):
    corpus = {f'{a["law"]}-art{a["number"]}' for a in map(json.loads, ARTICLES.open(encoding="utf-8"))}
    missing = sorted({k for g in gold for k in g["gold"]} - corpus)
    assert missing == []
