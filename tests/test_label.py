import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "eval"))
from label import cited, invalid_citations, parse_numbers, sample, to_labels


def test_citation_numbers_that_do_not_exist_are_found():
    answer = "Rule one [1]. Rule two [2][6]. Again [1]. Invented [37]."
    assert cited(answer) == [1, 2, 6, 37]
    assert invalid_citations(answer, n_sources=5) == [6, 37]
    assert invalid_citations("No citations at all.", n_sources=5) == []


def test_typed_citation_lists_are_parsed_strictly():
    assert parse_numbers("0") == []
    assert parse_numbers("2, 4") == [2, 4]
    assert parse_numbers("4,2,2") == [2, 4]
    assert parse_numbers("") is None            # pressing Enter is not an answer
    assert parse_numbers("none") is None
    assert parse_numbers("2 4") is None


def test_structured_answers_map_to_labels():
    assert to_labels(3, 3, False, False, [], []) == {
        "faithful": True, "correct": True, "complete": True, "citations_right": True}
    labels = to_labels(3, 2, True, True, [2], [])
    assert labels == {"faithful": False, "correct": False, "complete": False, "citations_right": False}
    assert to_labels(2, 2, False, False, [], [6])["citations_right"] is False   # invented number


def test_sample_is_blind_and_reproducible(monkeypatch):
    root = Path(__file__).parents[1]
    monkeypatch.chdir(root)                                    # label.py uses repo-relative paths
    def rows(path: str) -> list[dict]:
        return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]

    gold = {g["id"]: g for g in rows("eval/gold.jsonl")}
    answers = rows("eval/results/answers_hybrid+rerank.jsonl")
    worked_examples = {r["id"] for r in rows("eval/human_labels_calibration.jsonl")}
    reference = {r["id"] for r in rows("eval/assistant_labels.jsonl")}

    first, second = sample(gold, answers), sample(gold, answers)
    ids = [a["id"] for a in first]
    assert ids == [a["id"] for a in second]
    assert len(ids) == len(set(ids)) == 40
    assert not set(ids) & worked_examples                      # never an answer whose verdict is published
    assert len(set(ids) & reference) == 20                     # comparable with Claude's labels
