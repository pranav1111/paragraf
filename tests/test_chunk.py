import json
from pathlib import Path

import pytest

from paragraf import chunk
from paragraf.chunk import group_paragraphs


def test_groups_respect_the_cap_and_keep_order():
    assert group_paragraphs([100, 100, 100, 100], max_tokens=250) == [[0, 1], [2, 3]]


def test_oversized_paragraph_gets_its_own_group_and_is_never_cut():
    assert group_paragraphs([50, 500, 50], max_tokens=200) == [[0], [1], [2]]


def test_every_paragraph_is_used_exactly_once():
    sizes = [37, 120, 5, 260, 90, 90, 90, 14]
    flat = [i for g in group_paragraphs(sizes, max_tokens=200) for i in g]
    assert flat == list(range(len(sizes)))


def _article(lang, paragraphs):
    return {"law": "GDPR", "lang": lang, "number": "33", "url": "u",
            "title": "Notification" if lang == "en" else "Meldung", "paragraphs": paragraphs}


def test_twins_are_split_at_the_same_points(monkeypatch):
    # German is longer here; the split must follow the longer language for BOTH versions.
    monkeypatch.setattr(chunk, "n_tokens", len)                     # 1 "token" per character
    en = _article("en", ["a" * 100, "b" * 100, "c" * 100])
    de = _article("de", ["a" * 100, "b" * 300, "c" * 100])
    chunks = chunk.chunk_corpus([en, de])
    by_lang = {lang: [c.content.count("\n") for c in chunks if c.lang == lang] for lang in ("en", "de")}
    assert by_lang["en"] == by_lang["de"]                           # same paragraphs per chunk
    assert {c.id for c in chunks} == {f"GDPR-{l}-art33-c{k}" for l in ("en", "de") for k in range(3)}


def test_header_is_prepended_in_the_right_language(monkeypatch):
    monkeypatch.setattr(chunk, "n_tokens", len)
    chunks = chunk.chunk_corpus([_article("en", ["text"]), _article("de", ["Text"])])
    heads = {c.lang: c.content.splitlines()[0] for c in chunks}
    assert heads == {"en": "GDPR Art. 33 – Notification", "de": "DSGVO Art. 33 – Meldung"}


CHUNKS = Path("data/processed/chunks.jsonl")


@pytest.mark.skipif(not CHUNKS.exists(), reason="run paragraf.chunk first")
def test_real_chunks_are_unique_and_aligned():
    chunks = [json.loads(line) for line in CHUNKS.open(encoding="utf-8")]
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids))
    by_id = {c["id"]: c for c in chunks}
    for c in chunks:
        if c["lang"] == "en":
            twin = by_id[c["id"].replace("-en-", "-de-")]
            assert twin["content"].count("\n") == c["content"].count("\n")
