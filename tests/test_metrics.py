import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "eval"))
from judge import parse
from metrics import citation_coverage, hit_at_k, recall_at_k, reciprocal_rank, unique
from report import kappa


def test_retrieval_metrics_match_the_guide_example():
    ranked, gold = ["GDPR-art34", "GDPR-art33", "NIS2-art23"], {"GDPR-art33"}
    assert hit_at_k(ranked, gold, 1) == 0 and hit_at_k(ranked, gold, 3) == 1
    assert recall_at_k(ranked, gold, 5) == 1.0
    assert reciprocal_rank(ranked, gold) == 0.5


def test_recall_with_two_gold_articles():
    assert recall_at_k(["GDPR-art33", "AIACT-art5"], {"GDPR-art33", "NIS2-art23"}, 5) == 0.5


def test_unique_keeps_first_occurrence_order():
    assert unique(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]


def test_citation_coverage_counts_sentences_and_list_items():
    assert citation_coverage("Within 72 hours [1]. Reasons are needed if later [1].") == 1.0
    listing = "The following are prohibited:\n1. Manipulative techniques causing harm.\n2. Social scoring of people. [1][2]"
    assert citation_coverage(listing) == 0.5          # intro line ignored, only the last item is cited
    assert citation_coverage("") is None


def test_judge_parse_handles_prose_and_computes_faithfulness():
    raw = 'Here is my grading:\n```json\n{"claims": [{"claim": "72 hours", "supported": true}, ' \
          '{"claim": "EUR 1.5m", "supported": false}], "correct": false, "complete": true, "reason": "wrong fine"}\n```'
    r = parse(raw)
    assert r["faithfulness"] == 0.5 and r["correct"] is False and r["complete"] is True


def test_judge_parse_rejects_missing_fields():
    with pytest.raises(KeyError):
        parse('{"claims": [], "reason": "x"}')


def test_kappa():
    assert kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert abs(kappa([True, True, False, False], [True, False, True, False])) < 1e-9   # chance level
