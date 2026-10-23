"""Quick observation (not the real evaluation, which is Phase 9): where does the expected article land in
each retrieval mode for a handful of different question types?   uv run python scripts/observe_retrieval.py"""
import time

from paragraf.retrieve import MODES, Retriever, drop_twins

QUESTIONS = [  # (type, question, expected article)
    ("DE colloquial", "Wann muss eine Datenpanne gemeldet werden?", "GDPR-art33"),
    ("paraphrase", "How fast must I tell the regulator when hackers steal our customer data?", "GDPR-art33"),
    ("exact ref", "Art. 17 right to be forgotten", "GDPR-art17"),
    ("exact ref", "What does Article 50 of the AI Act require?", "AIACT-art50"),
    ("direct", "Which AI practices are banned?", "AIACT-art5"),
    ("acronym", "What is a DPIA and when is it required?", "GDPR-art35"),
    ("DE direct", "Welche Bußgelder drohen bei Verstößen gegen die DSGVO?", "GDPR-art83"),
    ("direct", "When must an essential entity send an early warning to the CSIRT?", "NIS2-art23"),
    ("paraphrase", "Are company directors personally responsible for cybersecurity under NIS2?", "NIS2-art20"),
    ("DE paraphrase", "Müssen Mitarbeiter, die KI-Systeme nutzen, geschult werden?", "AIACT-art4"),
    ("paraphrase", "Do I have to tell people they are chatting with a bot?", "AIACT-art50"),
]


def rank_of(expected: str, hits) -> int | None:
    seen = []
    for h in hits:
        if h.article_key not in seen:
            seen.append(h.article_key)
    return seen.index(expected) + 1 if expected in seen else None


def search(r: Retriever, question: str, mode: str):
    if mode == "keyword (ts_rank_cd)":                      # the first version, kept for comparison
        return drop_twins(r.fetch(r.keyword_tsrank(question, 30)))[:5]
    return r.search(question, mode=mode)


def main() -> None:
    r = Retriever()
    r.search("warm-up")
    modes = ("keyword (ts_rank_cd)", *MODES)
    ms = {m: [] for m in modes}
    print(f"| Type | Question | Expected | {' | '.join(modes)} |")
    print("|---|---|---|" + "---|" * len(modes))
    hits_at_1 = {m: 0 for m in modes}
    for qtype, question, expected in QUESTIONS:
        cells = []
        for mode in modes:
            start = time.perf_counter()
            hits = search(r, question, mode)
            ms[mode].append((time.perf_counter() - start) * 1000)
            rank = rank_of(expected, hits)
            hits_at_1[mode] += rank == 1
            cells.append("✗" if rank is None else ("**1**" if rank == 1 else str(rank)))
        print(f"| {qtype} | {question} | {expected} | {' | '.join(cells)} |")
    n = len(QUESTIONS)
    print(f"| | **rank 1 (of {n})** | | " + " | ".join(f"**{hits_at_1[m]}**" for m in modes) + " |")
    print("| | median latency | | " + " | ".join(f"{sorted(ms[m])[n // 2]:.0f} ms" for m in modes) + " |")


if __name__ == "__main__":
    main()
