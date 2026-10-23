"""Compare the four retrieval modes side by side:  python -m paragraf.search "your question" """
import sys
import time

from paragraf.retrieve import MODES, Retriever


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Wann muss eine Datenpanne gemeldet werden?"
    retriever = Retriever()
    retriever.search(query)                          # warm-up: first calls load models onto the GPU
    print(f"\nQ: {query}")
    for mode in MODES:
        start = time.perf_counter()
        hits = retriever.search(query, mode=mode)
        ms = (time.perf_counter() - start) * 1000
        print(f"\n== {mode}  ({ms:.0f} ms)")
        for i, h in enumerate(hits, start=1):
            score = f"{h.score:6.3f}" if mode == "hybrid+rerank" else "      "
            print(f"  {i}. {score} {h.law:5} Art. {h.article:>3} ({h.lang})  {h.title[:60]}")


if __name__ == "__main__":
    main()
