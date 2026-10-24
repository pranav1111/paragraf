"""LLM-as-a-judge for Paragraf's answers. Two interchangeable judges:

    uv run python eval/judge.py local  hybrid+rerank   # qwen2.5:7b via Ollama: free, no key
    uv run python eval/judge.py haiku  hybrid+rerank   # Claude Haiku 4.5: needs PARAGRAF_ANTHROPIC_API_KEY in .env

Writes eval/results/judge_<judge>_<mode>.jsonl. Unanswerable questions and abstentions are not judged
(they are scored deterministically in report.py).
"""
import json
import sys
from pathlib import Path

from paragraf.config import settings

GOLD, OUT = Path("eval/gold.jsonl"), Path("eval/results")

PROMPT = """You are grading an answer produced by a question-answering system about EU law (GDPR, AI Act, NIS2).

SOURCES (the only material the system was allowed to use):
{sources}

QUESTION: {question}

REFERENCE ANSWER (written and checked by a human from the law text):
{reference}

SYSTEM ANSWER:
{answer}

Instructions:
1. Split the SYSTEM ANSWER into atomic factual claims (ignore citation markers like [1]).
2. For each claim decide whether the SOURCES support it ("supported": true/false).
3. "correct": true if the SYSTEM ANSWER gets the key facts of the REFERENCE ANSWER right and states nothing
   that contradicts the reference or the law (it may be shorter or worded differently).
   Applying a rule to the wrong addressee or situation is NOT correct.
4. "complete": true if the SYSTEM ANSWER covers all main points of the REFERENCE ANSWER.

Return ONLY a JSON object, no other text:
{{"claims": [{{"claim": "...", "supported": true}}], "correct": true, "complete": true, "reason": "one sentence"}}"""


def parse(text: str) -> dict:
    """Extract and validate the judge's JSON (models sometimes wrap it in prose or code fences)."""
    start, end = text.find("{"), text.rfind("}")
    data = json.loads(text[start:end + 1])
    claims = [c for c in data.get("claims", []) if isinstance(c, dict) and "supported" in c]
    return {"claims": claims,
            "faithfulness": (sum(bool(c["supported"]) for c in claims) / len(claims)) if claims else None,
            "correct": bool(data["correct"]), "complete": bool(data["complete"]),
            "reason": str(data.get("reason", ""))}


def make_judge(name: str):
    if name == "local":
        from openai import OpenAI
        client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

        def call(prompt: str) -> str:
            r = client.chat.completions.create(model=settings.llm_model, temperature=0,
                                               messages=[{"role": "user", "content": prompt}])
            return r.choices[0].message.content or ""
        return call, settings.llm_model
    if name == "haiku":
        import anthropic
        if not settings.anthropic_api_key:
            sys.exit("Set PARAGRAF_ANTHROPIC_API_KEY in .env first (see .env.example).")
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        model = "claude-haiku-4-5-20251001"

        def call(prompt: str) -> str:
            r = client.messages.create(model=model, max_tokens=2000, temperature=0,
                                       messages=[{"role": "user", "content": prompt}])
            return "".join(block.text for block in r.content if block.type == "text")
        return call, model
    sys.exit(f"unknown judge {name!r} (use local or haiku)")


def main() -> None:
    judge_name, mode = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "hybrid+rerank")
    call, model = make_judge(judge_name)
    gold = {g["id"]: g for g in map(json.loads, GOLD.open(encoding="utf-8"))}
    answers = [json.loads(line) for line in (OUT / f"answers_{mode}.jsonl").open(encoding="utf-8")]
    todo = [a for a in answers if gold[a["id"]]["gold"] and not a["abstained"]]
    out = OUT / f"judge_{judge_name}_{mode}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for i, a in enumerate(todo, start=1):
            g = gold[a["id"]]
            prompt = PROMPT.format(
                sources="\n\n".join(f"[{s['n']}] {s['content']}" for s in a["sources"]),
                question=g["question"], reference=g["reference"], answer=a["answer"])
            row = {"id": a["id"], "judge": judge_name, "model": model, "mode": mode}
            for attempt in range(3):                       # retry when the JSON is malformed
                raw = call(prompt)
                try:
                    row.update(parse(raw))
                    break
                except (ValueError, KeyError, TypeError):
                    row["parse_error"] = raw[:300]
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{i:2}/{len(todo)}] {a['id']} correct={row.get('correct')} complete={row.get('complete')} "
                  f"faithfulness={row.get('faithfulness')}", flush=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
