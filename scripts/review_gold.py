"""Review the gold set question by question, with the real article text next to it.

    uv run python scripts/review_gold.py            # unreviewed questions only
    uv run python scripts/review_gold.py --flagged  # only questions you flagged earlier
    uv run python scripts/review_gold.py --all      # everything again

Keys: a = accept · f = flag (type a note: what is wrong) · s = skip · q = quit (progress is saved)
"""
import json
import sys
import textwrap
from datetime import date
from pathlib import Path

GOLD = Path("eval/gold.jsonl")
ARTICLES = Path("data/processed/articles.jsonl")
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"


def load_articles() -> dict:
    return {(a["law"], a["lang"], a["number"]): a for a in map(json.loads, ARTICLES.open(encoding="utf-8"))}


def save(rows: list[dict]) -> None:
    tmp = GOLD.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(GOLD)                                    # atomic: never a half-written file


def wrap(text: str, indent: str = "   ") -> str:
    return textwrap.fill(text, width=100, initial_indent=indent, subsequent_indent=indent)


def show(row: dict, articles: dict, done: int, total: int) -> None:
    print("\n" + "─" * 100)
    print(f"{BOLD}{row['id']}{RESET} · {row['type']} · {row['lang']}   {DIM}[{done}/{total} reviewed]{RESET}")
    print(f"\n{BOLD}Question:{RESET} {row['question']}")
    for key in row["gold"]:
        law, art = key.split("-art")
        a = articles.get((law, row["lang"], art)) or articles[(law, "en", art)]
        text = " ".join(a["paragraphs"])
        print(f"\n{BOLD}Gold: {key} – {a['title']}{RESET}  {DIM}{a['url']}#art_{art}{RESET}")
        print(wrap(text[:2600] + (" …  (open the link for the rest)" if len(text) > 2600 else "")))
    if not row["gold"]:
        print(f"\n{BOLD}Gold:{RESET} none, Paragraf should say it cannot find this")
    print(f"\n{BOLD}Reference answer:{RESET}\n{wrap(row['reference'])}")
    if row.get("notes"):
        print(f"\n{DIM}Notes: {row['notes']}{RESET}")
    if row.get("review_note"):
        print(f"\n{BOLD}Your earlier flag:{RESET} {row['review_note']}")


def main() -> None:
    rows = [json.loads(line) for line in GOLD.open(encoding="utf-8")]
    articles = load_articles()
    if "--all" in sys.argv:
        todo = rows
    elif "--flagged" in sys.argv:
        todo = [r for r in rows if r.get("flagged")]
    else:
        todo = [r for r in rows if not r.get("reviewed")]
    print(f"{len(todo)} question(s) to review. Keys: a accept · f flag · s skip · q quit")
    for row in todo:
        show(row, articles, sum(r.get("reviewed", False) for r in rows), len(rows))
        choice = input(f"\n{BOLD}[a]ccept [f]lag [s]kip [q]uit > {RESET}").strip().lower()
        if choice == "q":
            break
        if choice == "a":
            row.update(reviewed=True, flagged=False, reviewer="pranav", reviewed_on=str(date.today()))
            row.pop("review_note", None)
        elif choice == "f":
            row.update(reviewed=False, flagged=True, review_note=input("What is wrong? > ").strip())
        save(rows)
    reviewed = sum(r.get("reviewed", False) for r in rows)
    flagged = sum(r.get("flagged", False) for r in rows)
    print(f"\nSaved. {reviewed}/{len(rows)} reviewed, {flagged} flagged (tell Claude to fix the flagged ones).")


if __name__ == "__main__":
    main()
