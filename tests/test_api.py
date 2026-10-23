"""API tests with a fake retriever and a fake LLM: fast, no models, no database."""
import json
import logging

import pytest
from fastapi.testclient import TestClient

from paragraf import api
from paragraf.generate import Answer
from paragraf.retrieve import Hit

QUESTION = "Mein Name ist Max Mustermann, wann muss ich eine Datenpanne melden?"


class FakeRetriever:
    def search(self, question, mode="hybrid+rerank"):
        return [Hit("GDPR-de-art33-c0", "GDPR", "de", "33", "Meldung …", "https://eur-lex/x", "…"),
                Hit("NIS2-de-art23-c0", "NIS2", "de", "23", "Berichtspflichten", "https://eur-lex/y", "…")]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "answer", lambda q, hits: Answer("Binnen 72 Stunden [1].", [1], [], False))
    api.app.state.retriever = FakeRetriever()
    with TestClient(api.app) as c:
        yield c
    del api.app.state.retriever


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_answer_sources_and_timings(client):
    data = client.post("/ask", json={"question": QUESTION}).json()
    assert data["answer"] == "Binnen 72 Stunden [1]."
    assert [(s["n"], s["article"], s["cited"]) for s in data["sources"]] == [(1, "33", True), (2, "23", False)]
    assert data["sources"][0]["url"].endswith("#art_33")
    assert set(data["timings_ms"]) == {"retrieve", "generate", "total"}


@pytest.mark.parametrize("payload", [{"question": "?"}, {"question": "x" * 1001},
                                     {"question": "What is NIS2?", "mode": "magic"}])
def test_invalid_requests_are_rejected(client, payload):
    assert client.post("/ask", json=payload).status_code == 422


def test_log_contains_metadata_but_never_the_question(client, caplog):
    with caplog.at_level(logging.INFO, logger="paragraf"):
        client.post("/ask", json={"question": QUESTION})
    records = [json.loads(r.message) for r in caplog.records if r.name == "paragraf"]
    assert records and records[-1]["event"] == "ask" and records[-1]["lang"] == "de"
    assert "Mustermann" not in caplog.text and "Datenpanne" not in caplog.text


def test_index_page_is_served(client):
    res = client.get("/")
    assert res.status_code == 200 and "<title>Paragraf</title>" in res.text
