"""Ask Paragraf from the command line:  python -m paragraf.ask "Wann muss eine Datenpanne gemeldet werden?" """
import sys
import time

from paragraf.generate import answer
from paragraf.retrieve import Retriever


def show(retriever: Retriever, question: str) -> None:
    t0 = time.perf_counter()
    hits = retriever.search(question)
    t1 = time.perf_counter()
    result = answer(question, hits)
    t2 = time.perf_counter()
    print(f"\nQ: {question}\n\n{result.text}\n")
    for i, h in enumerate(hits, start=1):
        mark = "*" if i in result.cited else " "
        print(f"  {mark}[{i}] {h.law} Art. {h.article} ({h.lang}) – {h.title[:70]}")
    flags = []
    if result.abstained:
        flags.append("ABSTAINED")
    if result.invalid_citations:
        flags.append(f"INVALID CITATIONS {result.invalid_citations}")
    print(f"\n  retrieve {1000 * (t1 - t0):.0f} ms · generate {1000 * (t2 - t1):.0f} ms"
          + (f" · {' · '.join(flags)}" if flags else ""))


def main() -> None:
    retriever = Retriever()
    show(retriever, " ".join(sys.argv[1:]) or "Wann muss eine Datenpanne gemeldet werden?")


if __name__ == "__main__":
    main()
