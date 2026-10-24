"""Grade 20 answers yourself, BEFORE looking at any judge output (blind labels).

    uv run python eval/label.py

For each answer you see the question, the reference answer, the sources Paragraf used and its answer.
Three yes/no questions: faithful (everything supported by the sources)? correct? complete?
Progress is saved after every answer (eval/human_labels.jsonl); run again to continue.
"""
import json
import random
import textwrap
from pathlib import Path

GOLD, ANSWERS = Path("eval/gold.jsonl"), Path("eval/results/answers_hybrid+rerank.jsonl")
LABELS = Path("eval/human_labels.jsonl")
N, SEED = 20, 13
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"


def sample(gold: dict, answers: list[dict]) -> list[dict]:
    """Stratified by question type so every type is represented; fixed seed = reproducible."""
    pool = [a for a in answers if gold[a["id"]]["gold"] and not a["abstained"]]
    rng = random.Random(SEED)
    by_type: dict[str, list[dict]] = {}
    for a in pool:
        by_type.setdefault(gold[a["id"]]["type"], []).append(a)
    picked = []
    for qtype, items in sorted(by_type.items()):
        k = max(1, round(N * len(items) / len(pool)))
        picked += rng.sample(items, min(k, len(items)))
    rng.shuffle(picked)
    return picked[:N]


def ask(prompt: str) -> bool:
    while True:
        a = input(f"{BOLD}{prompt} [y/n] > {RESET}").strip().lower()
        if a in ("y", "n"):
            return a == "y"


def wrap(text: str) -> str:
    return "\n".join(textwrap.fill(p, 100, initial_indent="   ", subsequent_indent="   ") for p in text.splitlines() if p)


def main() -> None:
    gold = {g["id"]: g for g in map(json.loads, GOLD.open(encoding="utf-8"))}
    answers = [json.loads(line) for line in ANSWERS.open(encoding="utf-8")]
    done = {r["id"]: r for r in map(json.loads, LABELS.open(encoding="utf-8"))} if LABELS.exists() else {}
    todo = [a for a in sample(gold, answers) if a["id"] not in done]
    print(f"{len(done)} labelled, {len(todo)} to go. Answer y/n; Ctrl+C to stop (progress is saved).")
    for a in todo:
        g = gold[a["id"]]
        print("\n" + "─" * 100)
        print(f"{BOLD}{a['id']}{RESET} · {g['type']} · {g['lang']}   {DIM}[{len(done) + 1}/{N}]{RESET}")
        print(f"\n{BOLD}Question:{RESET} {g['question']}")
        print(f"\n{BOLD}Reference answer:{RESET}\n{wrap(g['reference'])}")
        print(f"\n{BOLD}Sources Paragraf used:{RESET}")
        for s in a["sources"]:
            print(f"{DIM}[{s['n']}] {s['content'][:900]}{' …' if len(s['content']) > 900 else ''}{RESET}\n")
        print(f"{BOLD}Paragraf's answer:{RESET}\n{wrap(a['answer'])}\n")
        row = {"id": a["id"],
               "faithful": ask("Faithful: is EVERY claim in the answer supported by the sources?"),
               "correct": ask("Correct: are the key facts right (no wrong facts, no wrong addressee)?"),
               "complete": ask("Complete: does it cover all main points of the reference?"),
               "note": input(f"{BOLD}Optional note > {RESET}").strip()}
        done[a["id"]] = row
        LABELS.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values()), encoding="utf-8")
    print(f"\nSaved {len(done)} labels to {LABELS}.")


if __name__ == "__main__":
    main()
