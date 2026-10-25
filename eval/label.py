"""Grade 40 answers yourself: blind, and with a structured check instead of four yes/no questions.

    uv run python eval/label.py

Read eval/calibration_notes.md first (annotation guidelines with worked examples).
The 40 answers: the 20 answers Claude labelled that are NOT worked examples in the guidelines, plus 20 answers
nobody has labelled. You never see a judge verdict or Claude's labels.

Each answer is checked in four steps that force a close reading:
  1. completeness by counting: points in the reference answer vs. points the answer states correctly
  2. is anything wrong (a fact, or a true rule applied to the wrong person or situation)?
  3. is any claim missing from the sources?
  4. which citations point to a source that does not contain the claim (citation numbers that do not exist
     are detected automatically)
Progress is saved after every answer (eval/human_labels.jsonl); run again to continue.
"""
import json
import random
import re
import statistics
import textwrap
import time
from pathlib import Path

GOLD, ANSWERS = Path("eval/gold.jsonl"), Path("eval/results/answers_hybrid+rerank.jsonl")
LABELS = Path("eval/human_labels.jsonl")
CALIBRATION = Path("eval/human_labels_calibration.jsonl")   # round 1: worked examples, not blind any more
REFERENCE = Path("eval/assistant_labels.jsonl")             # Claude's 40 labels (20 are the worked examples)
N_FRESH, SEED = 20, 31
BOLD, DIM, WARN, RESET = "\033[1m", "\033[2m", "\033[33m", "\033[0m"
CITE = re.compile(r"\[(\d+)\]")


def ids_in(path: Path) -> set[str]:
    return {json.loads(line)["id"] for line in path.open(encoding="utf-8")} if path.exists() else set()


def stratified(items: list[dict], gold: dict, k: int, rng: random.Random) -> list[dict]:
    """k items spread over question types in proportion to their share."""
    by_type: dict[str, list[dict]] = {}
    for a in items:
        by_type.setdefault(gold[a["id"]]["type"], []).append(a)
    picked = []
    for _, group in sorted(by_type.items()):
        picked += rng.sample(group, min(len(group), max(1, round(k * len(group) / len(items)))))
    rest = [a for a in items if a not in picked]                # rounding per type can fall short of k
    picked += rng.sample(rest, max(0, min(k - len(picked), len(rest))))
    rng.shuffle(picked)
    return picked[:k]


def sample(gold: dict, answers: list[dict]) -> list[dict]:
    """Claude-labelled answers that are not worked examples, plus N_FRESH never-labelled ones; fixed seed."""
    shown, reference = ids_in(CALIBRATION), ids_in(REFERENCE)
    pool = [a for a in answers if gold[a["id"]]["gold"] and not a["abstained"] and a["id"] not in shown]
    picked = [a for a in pool if a["id"] in reference]
    picked += stratified([a for a in pool if a["id"] not in reference], gold, N_FRESH, random.Random(SEED))
    random.Random(SEED).shuffle(picked)
    return picked


def cited(answer: str) -> list[int]:
    return sorted({int(n) for n in CITE.findall(answer)})


def invalid_citations(answer: str, n_sources: int) -> list[int]:
    return [n for n in cited(answer) if not 1 <= n <= n_sources]


def parse_numbers(text: str) -> list[int] | None:
    """'2, 4' -> [2, 4]; '0' -> [] (all right); anything else -> None (ask again)."""
    text = text.strip()
    if text == "0":
        return []
    if not re.fullmatch(r"\d+(\s*,\s*\d+)*", text):
        return None
    return sorted({int(n) for n in text.split(",")})


def to_labels(points_ref: int, points_ok: int, wrong: bool, unsupported: bool,
              wrong_cites: list[int], invalid: list[int]) -> dict:
    return {"faithful": not unsupported, "correct": not wrong, "complete": points_ok >= points_ref,
            "citations_right": not wrong_cites and not invalid}


def ask_yn(prompt: str) -> bool:
    while True:
        a = input(f"{BOLD}{prompt} [y/n] > {RESET}").strip().lower()
        if a in ("y", "n"):
            return a == "y"


def ask_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        a = input(f"{BOLD}{prompt} [{lo}–{hi}] > {RESET}").strip()
        if a.isdigit() and lo <= int(a) <= hi:
            return int(a)


def ask_text(prompt: str) -> str:
    while not (a := input(f"{BOLD}{prompt} > {RESET}").strip()):
        pass
    return a


def ask_citations(valid: list[int]) -> list[int]:
    shown = ", ".join(f"[{n}]" for n in valid)
    while True:
        nums = parse_numbers(input(f"{BOLD}The answer cites {shown}. Which of them point to a source that does NOT "
                                   f"contain the claim? (e.g. 2,4 · type 0 if all are right) > {RESET}"))
        if nums is not None and set(nums) <= set(valid):
            return nums


def wrap(text: str) -> str:
    return "\n".join(textwrap.fill(p, 100, initial_indent="   ", subsequent_indent="   ") for p in text.splitlines() if p)


def summary(done: dict) -> None:
    rows = list(done.values())
    print(f"\n{BOLD}Your labels so far ({len(rows)} answers){RESET}")
    for k in ("correct", "complete", "faithful", "citations_right"):
        print(f"   {k:16s} yes {sum(r[k] for r in rows):2d} / {len(rows)}")
    times = [r["seconds"] for r in rows if "seconds" in r]
    if times:
        print(f"   median time per answer: {statistics.median(times):.0f} s")
    if len(rows) >= 10:
        for k in ("correct", "complete", "citations_right"):
            if sum(r[k] for r in rows) >= 0.9 * len(rows):
                print(f"{WARN}   ⚠ {k}: {sum(r[k] for r in rows)}/{len(rows)} yes. Rates this high usually mean the check "
                      f"was too lenient (worked examples: complete 10/20, citations right 12/20).{RESET}")


def main() -> None:
    gold = {g["id"]: g for g in map(json.loads, GOLD.open(encoding="utf-8"))}
    answers = [json.loads(line) for line in ANSWERS.open(encoding="utf-8")]
    done = {r["id"]: r for r in map(json.loads, LABELS.open(encoding="utf-8"))} if LABELS.exists() else {}
    picked = sample(gold, answers)
    todo = [a for a in picked if a["id"] not in done]
    print(f"{len(done)} labelled, {len(todo)} to go. Ctrl+C to stop (progress is saved).\n"
          f"{DIM}Method: read the reference and count its points, then read the answer sentence by sentence and find each "
          f"claim in the cited source.{RESET}")
    try:
        for a in todo:
            g, start = gold[a["id"]], time.monotonic()
            print("\n" + "─" * 100)
            print(f"{BOLD}{a['id']}{RESET} · {g['type']} · {g['lang']}   {DIM}[{len(done) + 1}/{len(picked)}]{RESET}")
            print(f"\n{BOLD}Question:{RESET} {g['question']}")
            print(f"\n{BOLD}Reference answer:{RESET}\n{wrap(g['reference'])}")
            print(f"\n{BOLD}Sources Paragraf used:{RESET}")
            for s in a["sources"]:
                print(f"{DIM}[{s['n']}] {s['content']}{RESET}\n")          # full text: the evidence may be at the end
            print(f"{BOLD}Paragraf's answer:{RESET}\n{wrap(a['answer'])}\n")
            invalid = invalid_citations(a["answer"], len(a["sources"]))
            if invalid:
                print(f"{WARN}⚠ Checked automatically: the answer cites {', '.join(f'[{n}]' for n in invalid)}, but only "
                      f"{len(a['sources'])} sources exist. Its citations count as wrong.{RESET}\n")

            print(f"{BOLD}Step 1 · Completeness.{RESET} {DIM}A point is one case, condition, exception, deadline, amount or "
                  f"addressee.{RESET}")
            points_ref = ask_int("How many points does the REFERENCE answer make?", 1, 20)
            points_ok = ask_int(f"How many of those {points_ref} does Paragraf's answer state correctly?", 0, points_ref)
            print(f"{BOLD}Step 2 · Errors.{RESET}")
            wrong = ask_yn("Is anything in the answer WRONG (a fact, number or deadline, or a rule applied to the wrong "
                           "person or situation)?")
            problem = ask_text("What is wrong?") if wrong else ""
            print(f"{BOLD}Step 3 · Sources.{RESET}")
            unsupported = ask_yn("Is there a claim in the answer that you could NOT find in the sources shown?")
            claim = ask_text("Which claim?") if unsupported else ""
            print(f"{BOLD}Step 4 · Citations.{RESET}")
            valid = [n for n in cited(a["answer"]) if n not in invalid]
            wrong_cites = ask_citations(valid) if valid else []
            note = input(f"{BOLD}Optional note > {RESET}").strip()

            done[a["id"]] = {"id": a["id"],
                             **to_labels(points_ref, points_ok, wrong, unsupported, wrong_cites, invalid),
                             "points_reference": points_ref, "points_covered": points_ok, "problem": problem,
                             "unsupported_claim": claim, "wrong_citations": wrong_cites, "invalid_citations": invalid,
                             "note": note, "seconds": round(time.monotonic() - start), "annotator": "pranav",
                             "method": "structured, blind"}
            LABELS.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values()), encoding="utf-8")
    except KeyboardInterrupt:
        print("\nStopped. Progress is saved.")
    summary(done)


if __name__ == "__main__":
    main()
