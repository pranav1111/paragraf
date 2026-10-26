"""Paragraf web service.   uv run uvicorn paragraf.api:app --reload   →  http://localhost:8000

Privacy: the request log contains metadata only (language, length, timings, outcome), never the question
text. People type personal details into legal assistants; logging them would contradict GDPR Art. 5(1)(c)
(data minimisation) in our own system.
"""
import json
import logging
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from openai import BadRequestError, OpenAIError
from pydantic import BaseModel, Field

from paragraf.generate import Answer, answer, detect_language
from paragraf.retrieve import Retriever

log = logging.getLogger("paragraf")
logging.basicConfig(level=logging.INFO, format="%(message)s")
STATIC = Path(__file__).resolve().parents[2] / "static"
_lock = threading.Lock()                     # the embedding models are not safe to call from many threads
# Shown when a security gateway in front of the LLM (Warden) refuses the request.
BLOCKED = {"en": "This request was blocked by the security policy.",
           "de": "Diese Anfrage wurde durch die Sicherheitsrichtlinie blockiert."}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "retriever"):  # tests inject a fake retriever before startup
        app.state.retriever = Retriever()    # load the models once, not per request
    yield


app = FastAPI(title="Paragraf", version="0.1.0", lifespan=lifespan,
              description="Cited answers about the GDPR, the EU AI Act and NIS2 (German and English).")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000, examples=["Wann muss eine Datenpanne gemeldet werden?"])
    mode: Literal["keyword", "dense", "hybrid", "hybrid+rerank"] = "hybrid+rerank"


class Source(BaseModel):
    n: int
    law: str
    article: str
    title: str
    lang: str
    url: str
    cited: bool


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    abstained: bool
    blocked: bool = False
    invalid_citations: list[int]
    timings_ms: dict[str, float]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request) -> AskResponse:
    t0 = time.perf_counter()
    with _lock:
        hits = request.app.state.retriever.search(req.question, mode=req.mode)
    t1 = time.perf_counter()
    blocked, gateway_id = False, None
    try:
        result = answer(req.question, hits)
    except BadRequestError as exc:
        if getattr(exc, "type", None) != "warden_blocked":
            log.error(json.dumps({"event": "llm_error", "error": type(exc).__name__}))
            raise HTTPException(502, "The language model rejected the request.") from exc
        gateway_id = exc.response.headers.get("x-warden-request-id")
        blocked, hits = True, []                 # nothing was answered from the sources
        result = Answer(BLOCKED[detect_language(req.question)], [], [], False)
    except OpenAIError as exc:
        log.error(json.dumps({"event": "llm_error", "error": type(exc).__name__}))
        raise HTTPException(503, "The language model is not reachable. Is Ollama running?") from exc
    t2 = time.perf_counter()

    timings = {"retrieve": round((t1 - t0) * 1000), "generate": round((t2 - t1) * 1000),
               "total": round((t2 - t0) * 1000)}
    log.info(json.dumps({"event": "ask", "lang": detect_language(req.question), "chars": len(req.question),
                         "mode": req.mode, "sources": len(hits), "cited": len(result.cited),
                         "abstained": result.abstained, "blocked": blocked, "gateway_request_id": gateway_id,
                         "invalid_citations": len(result.invalid_citations),
                         **{f"ms_{k}": v for k, v in timings.items()}}))
    return AskResponse(
        answer=result.text,
        sources=[Source(n=i, law=h.law, article=h.article, title=h.title, lang=h.lang,
                        url=f"{h.url}#art_{h.article}", cited=i in result.cited)
                 for i, h in enumerate(hits, start=1)],
        abstained=result.abstained,
        blocked=blocked,
        invalid_citations=result.invalid_citations,
        timings_ms=timings,
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
