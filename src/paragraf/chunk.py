"""Turn articles into retrieval chunks.

Design:
- Structure first: a chunk never crosses an article boundary and never cuts a paragraph.
- A token cap per chunk (measured with the embedding model's own tokenizer).
- A contextual header on every chunk ("DSGVO Art. 33 – Meldung von …") so short paragraphs stay findable.
- Aligned twins: the EN and DE versions of an article have identical paragraph structure (verified in
  Phase 1), so the split points are chosen once per article pair, using the larger of the two token
  counts, and applied to both. Then GDPR-en-art33-c1 and GDPR-de-art33-c1 hold the same paragraphs.
"""
import json
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path

MAX_TOKENS = 380            # paragraph budget per chunk (the header comes on top); tune with the eval
LAW_NAMES = {
    ("GDPR", "en"): "GDPR", ("GDPR", "de"): "DSGVO",
    ("AIACT", "en"): "AI Act", ("AIACT", "de"): "KI-Verordnung",
    ("NIS2", "en"): "NIS2", ("NIS2", "de"): "NIS-2-Richtlinie",
}
SRC, OUT = Path("data/processed/articles.jsonl"), Path("data/processed/chunks.jsonl")


@dataclass
class Chunk:
    id: str
    law: str
    lang: str
    article: str
    title: str
    url: str
    content: str


@cache
def _tokenizer():
    from transformers import AutoTokenizer  # imported lazily so unit tests don't need the model
    return AutoTokenizer.from_pretrained("BAAI/bge-m3")


def n_tokens(text: str) -> int:
    return len(_tokenizer().encode(text, add_special_tokens=False))


def group_paragraphs(sizes: list[int], max_tokens: int = MAX_TOKENS) -> list[list[int]]:
    """Greedy grouping of consecutive paragraph indices so each group stays within max_tokens.
    A single paragraph larger than the cap becomes its own group (never cut mid-paragraph)."""
    groups, current, used = [], [], 0
    for i, size in enumerate(sizes):
        if current and used + size > max_tokens:
            groups.append(current)
            current, used = [], 0
        current.append(i)
        used += size + 1                         # +1 for the newline that joins paragraphs
    if current:
        groups.append(current)
    return groups


def header(article: dict) -> str:
    return f'{LAW_NAMES[(article["law"], article["lang"])]} Art. {article["number"]} – {article["title"]}'


def make_chunks(article: dict, groups: list[list[int]]) -> list[Chunk]:
    return [
        Chunk(id=f'{article["law"]}-{article["lang"]}-art{article["number"]}-c{k}',
              law=article["law"], lang=article["lang"], article=article["number"],
              title=article["title"], url=article["url"],
              content=header(article) + "\n" + "\n".join(article["paragraphs"][i] for i in group))
        for k, group in enumerate(groups)
    ]


def chunk_corpus(articles: list[dict]) -> list[Chunk]:
    by_key = defaultdict(dict)                   # (law, number) -> {"en": article, "de": article}
    for a in articles:
        by_key[(a["law"], a["number"])][a["lang"]] = a
    chunks = []
    for versions in by_key.values():
        sizes_per_lang = [[n_tokens(p) for p in a["paragraphs"]] for a in versions.values()]
        if len({len(s) for s in sizes_per_lang}) == 1:          # aligned: same paragraph count
            sizes = [max(col) for col in zip(*sizes_per_lang)]
            groups = group_paragraphs(sizes)
            for a in versions.values():
                chunks += make_chunks(a, groups)
        else:                                                   # fallback: chunk each language alone
            for a, s in zip(versions.values(), sizes_per_lang):
                chunks += make_chunks(a, group_paragraphs(s))
    return chunks


def main() -> None:
    articles = [json.loads(line) for line in SRC.open(encoding="utf-8")]
    chunks = chunk_corpus(articles)
    with OUT.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    sizes = [n_tokens(c.content) for c in chunks]
    print(f"{len(chunks)} chunks · median {statistics.median(sizes):.0f} tokens · max {max(sizes)}")
    for law in ("GDPR", "AIACT", "NIS2"):
        for lang in ("en", "de"):
            print(f"  {law:5} {lang}: {sum(c.law == law and c.lang == lang for c in chunks):4} chunks")


if __name__ == "__main__":
    main()
