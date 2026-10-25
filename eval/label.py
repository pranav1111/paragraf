"""Grade the 40 reference answers yourself, BEFORE looking at any judge output or other labels (blind).

    uv run python eval/label.py

Read eval/calibration_notes.md first (annotation guidelines with worked examples).
For each answer you see the question, the reference answer, the sources Paragraf used and its answer.
Four yes/no questions: faithful (everything supported by the sources)? correct? complete?
citations right (each [n] points to a source that contains the claim)?
Progress is saved after every answer (eval/human_labels.jsonl); run again to continue.
You label the same 40 answers as eval/assistant_labels.jsonl (Claude), so your labels can replace them as the
reference and the two label sets can be compared. Claude's labels are never shown.
"""
import json
import random
import textwrap
from pathlib import Path

GOLD, ANSWERS = Path("eval/gold.jsonl"), Path("eval/results/answers_hybrid+rerank.jsonl")
LABELS = Path("eval/human_labels.jsonl")
CALIBRATION = Path("eval/human_labels_calibration.jsonl")   # round 1: seen, not blind any more
REFERENCE = Path("eval/assistant_labels.jsonl")             # round 2: the 40 answers labelled by Claude
N, SEED = 40, 29
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"


def sample(gold: dict, answers: list[dict]) -> list[dict]:
    """The answers Claude labelled (same set, new order); otherwise a stratified sample with a fixed seed."""
    if REFERENCE.exists():
        ids = {json.loads(line)["id"] for line in REFERENCE.open(encoding="utf-8")}
        picked = [a for a in answers if a["id"] in ids]
        random.Random(SEED).shuffle(picked)
        return picked
    seen = {json.loads(line)["id"] for line in CALIBRATION.open(encoding="utf-8")} if CALIBRATION.exists() else set()
    pool = [a for a in answers if gold[a["id"]]["gold"] and not a["abstained"] and a["id"] not in seen]
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
            print(f"{DIM}[{s['n']}] {s['content']}{RESET}\n")          # full text: the evidence may be at the end
        print(f"{BOLD}Paragraf's answer:{RESET}\n{wrap(a['answer'])}\n")
        row = {"id": a["id"],
               "faithful": ask("Faithful: is EVERY claim in the answer supported by the sources?"),
               "correct": ask("Correct: are the key facts right (no wrong facts, no wrong addressee)?"),
               "complete": ask("Complete: does it cover all main points of the reference?"),
               "citations_right": ask("Citations: does each [n] point to a source that really contains that claim?"),
               "note": input(f"{BOLD}Optional note > {RESET}").strip()}
        done[a["id"]] = row
        LABELS.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values()), encoding="utf-8")
    print(f"\nSaved {len(done)} labels to {LABELS}.")


if __name__ == "__main__":
    main()
