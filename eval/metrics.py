"""Evaluation metrics (pure functions, unit-tested in tests/test_metrics.py)."""
import re
import statistics

CITATION = re.compile(r"\[\d+\]")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[^\[\s])")   # do not split off a trailing "[1]"


def unique(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


def hit_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    return float(any(r in gold for r in ranked[:k]))


def recall_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    return len(set(ranked[:k]) & gold) / len(gold)


def reciprocal_rank(ranked: list[str], gold: set[str]) -> float:
    for i, r in enumerate(ranked, start=1):
        if r in gold:
            return 1.0 / i
    return 0.0


def citation_coverage(text: str) -> float | None:
    """Share of sentences / list items that carry a citation. Intro lines ending in ':' are not counted."""
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.endswith(":"):
            continue
        units += [s for s in SENTENCE_END.split(line) if len(re.sub(r"\W", "", s)) >= 15]
    if not units:
        return None
    return sum(bool(CITATION.search(u)) for u in units) / len(units)


def mean(values) -> float:
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else float("nan")


def percentile(values, p: float) -> float:
    values = sorted(values)
    if not values:
        return float("nan")
    k = (len(values) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)
