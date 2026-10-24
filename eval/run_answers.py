"""Generate Paragraf's answers for every gold question (input for the judges and for human labels).

    uv run python eval/run_answers.py hybrid+rerank      → eval/results/answers_hybrid+rerank.jsonl
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from metrics import citation_coverage

from paragraf.generate import answer
from paragraf.retrieve import Retriever

GOLD, OUT = Path("eval/gold.jsonl"), Path("eval/results")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "hybrid+rerank"
    gold = [json.loads(line) for line in GOLD.open(encoding="utf-8")]
    retriever = Retriever()
    out = OUT / f"answers_{mode}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for i, g in enumerate(gold, start=1):
            t0 = time.perf_counter()
            hits = retriever.search(g["question"], mode=mode)
            t1 = time.perf_counter()
            result = answer(g["question"], hits)
            t2 = time.perf_counter()
            row = {"id": g["id"], "mode": mode, "answer": result.text, "abstained": result.abstained,
                   "cited": result.cited, "invalid_citations": result.invalid_citations,
                   "citation_coverage": None if result.abstained else citation_coverage(result.text),
                   "gold_in_sources": bool(set(g["gold"]) & {h.article_key for h in hits}),
                   "sources": [{"n": n, "id": h.id, "article_key": h.article_key, "title": h.title,
                                "content": h.content} for n, h in enumerate(hits, start=1)],
                   "ms_retrieve": round((t1 - t0) * 1000), "ms_generate": round((t2 - t1) * 1000)}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{i:2}/{len(gold)}] {g['id']} {'ABSTAIN' if result.abstained else 'answer '} "
                  f"{row['ms_generate']:5} ms", flush=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
