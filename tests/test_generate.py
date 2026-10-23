import pytest

from paragraf.generate import ABSTAIN_DE, ABSTAIN_EN, check, detect_language, format_sources, system_prompt
from paragraf.retrieve import Hit


def test_check_separates_valid_and_invented_citations():
    result = check("Within 72 hours [1]. Fines apply [2][7]. See also [1].", n_sources=5)
    assert result.cited == [1, 2]
    assert result.invalid_citations == [7]
    assert not result.abstained


@pytest.mark.parametrize("text", [ABSTAIN_EN, ABSTAIN_DE])
def test_check_detects_abstention_in_both_languages(text):
    assert check(text, n_sources=5).abstained


@pytest.mark.parametrize("question,lang", [
    ("Wann muss eine Datenpanne gemeldet werden?", "de"),
    ("Welche KI-Praktiken sind verboten?", "de"),
    ("Wie hoch ist das Kindergeld in Deutschland?", "de"),
    ("What is the speed limit on the German Autobahn?", "en"),
    ("Art. 17 right to be forgotten", "en"),
    ("Which AI practices are prohibited under the AI Act?", "en"),
])
def test_detect_language(question, lang):
    assert detect_language(question) == lang


def test_system_prompt_uses_the_abstention_sentence_of_the_question_language():
    assert ABSTAIN_DE in system_prompt("Wie hoch ist das Kindergeld?")
    assert ABSTAIN_EN not in system_prompt("Wie hoch ist das Kindergeld?")
    assert ABSTAIN_EN in system_prompt("What is the speed limit?")


def test_sources_are_numbered_from_one():
    hits = [Hit("GDPR-en-art33-c0", "GDPR", "en", "33", "t", "u", "GDPR Art. 33 – Notification"),
            Hit("NIS2-en-art23-c0", "NIS2", "en", "23", "t", "u", "NIS2 Art. 23 – Reporting")]
    assert format_sources(hits).startswith("[1] GDPR Art. 33") and "\n\n[2] NIS2 Art. 23" in format_sources(hits)


@pytest.mark.integration
def test_llm_abstains_when_the_source_is_irrelevant():
    import httpx

    from paragraf.config import settings
    from paragraf.generate import answer

    try:
        httpx.get(settings.llm_base_url.replace("/v1", "/api/version"), timeout=2)
    except httpx.HTTPError:
        pytest.skip("Ollama not running")
    hits = [Hit("GDPR-en-art99-c0", "GDPR", "en", "99", "Entry into force", "u",
                "GDPR Art. 99 – Entry into force and application\n2. It shall apply from 25 May 2018.")]
    result = answer("What is the speed limit on the German Autobahn?", hits)
    assert result.abstained and result.invalid_citations == []
