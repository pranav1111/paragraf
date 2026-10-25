# Paragraf

**Cited answers about EU digital law (GDPR, EU AI Act, NIS2), in German and English, with an evaluation that
shows how well it actually works.**

![A German question about data breaches answered with a citation to GDPR Art. 33 (real time, Apple M-series)](docs/demo.gif)

Runs fully locally: PostgreSQL + pgvector for search, a local LLM through Ollama for answers. No question ever
leaves the machine, and the request log never contains question text. Not legal advice.

## Results

Evaluated on a gold set of **80 questions** (reviewed by hand against the law text: direct, paraphrased, exact
article references, cross-law, German, and 8 unanswerable "trap" questions). Full analysis:
[`notes/evaluation-findings.md`](notes/evaluation-findings.md), raw data in [`eval/results/`](eval/results).

**Retrieval** (72 answerable questions, right article found):

| Mode | Hit@1 | Recall@5 | MRR | Latency (p50) |
|---|---|---|---|---|
| Keyword (BM25 in PostgreSQL) | 0.56 | 0.81 | 0.66 | 4 ms |
| Dense (bge-m3 + pgvector HNSW) | **0.92** | **0.97** | **0.95** | 21 ms |
| Hybrid (Reciprocal Rank Fusion) | 0.75 | 0.97 | 0.84 | 26 ms |
| Hybrid + cross-encoder rerank (default) | 0.88 | 0.97 | 0.94 | 1.6 s |

**Answers** (judged by Claude Haiku 4.5; the judge was validated against reference labels first):

| | qwen2.5:7b | **qwen2.5:14b (default)** |
|---|---|---|
| Faithful (claims supported by the cited law) | 97% | 95% |
| Correct | 71% | **76%** |
| Complete (all main points) | 30% | 33% |
| Invented citation numbers | 6 | **0** |
| Unanswerable questions refused | 8/8 | 8/8 |
| Latency (p50, Apple M-series) | 7.9 s | 14.3 s |

### Key findings
- **PostgreSQL's `ts_rank_cd` is not BM25.** It has no IDF, so "Article 50" lost to chunks that repeat "article"
  and "AI". Real BM25 in SQL lifted keyword top-1 from 0/11 to 2/11 on an early test set and doubled hybrid quality.
- **Dense retrieval alone matched the full pipeline** at 1/70 of the latency. The reranker helps only on
  paraphrased questions; keyword search helps on cross-law questions.
- **Validate the judge.** A local 7B judge agreed with the reference labels 82% of the time, but its Cohen's
  κ was **0.00** (no better than chance). Claude Haiku reached κ 0.43–0.60 and is used for all numbers.
- **Prompting cannot add capability.** A stricter prompt made the 7B model *worse* (correct 69% → 58%); a 14B
  model removed invented citations (6 → 0) at 1.8× latency. Both experiments are kept, including the negative one.
- **Biggest open weakness: completeness.** Answers are faithful but often stop after the first case or tier.

## How it works

```mermaid
flowchart TB
    subgraph index["Indexing: once, about a minute on an Apple GPU"]
        direction LR
        A["EUR-Lex via the Cellar API<br/>GDPR, AI Act, NIS2 in EN + DE"] --> B["Parse per article"]
        B --> C["Structure-aware chunks<br/>1,058 aligned DE/EN chunks"]
        C --> D[("PostgreSQL 17<br/>pgvector HNSW + BM25 statistics")]
    end
    subgraph ask["Per question: ~2 s search, ~3 to 20 s answer"]
        direction LR
        Q["Question<br/>(DE or EN)"] --> K["BM25<br/>in SQL"]
        Q --> V["Dense search<br/>bge-m3"]
        K --> F["Reciprocal<br/>Rank Fusion"]
        V --> F
        F --> R["Cross-encoder rerank<br/>top 5 sources"]
        R --> G["Local LLM (Ollama)<br/>qwen2.5:14b"]
        G --> O["Answer with numbered<br/>citations, checked"]
    end
    index -. "search reads the index" .-> ask
```

- **Hybrid search in one database:** pgvector (HNSW, cosine) for meaning; BM25 computed in SQL from PostgreSQL's
  stemmed `tsvector`s (materialised term statistics) for exact references such as "Art. 17".
- **Bilingual by design:** EN and DE versions share article and paragraph structure, so chunks are split at the
  same points in both languages and duplicates across languages are removed exactly.
- **Grounded generation:** numbered sources, mandatory citations, an exact "not found" sentence per language
  (chosen in code, not by the model), and a check that flags invented citation numbers.
- **Provider-agnostic LLM layer:** OpenAI-compatible API, so switching to another local or hosted model is a
  configuration change.

## Design decisions and trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| **PostgreSQL + pgvector** instead of a dedicated vector database | One system for text, vectors, metadata and BM25; transactions, joins and backups come for free | Fine for thousands of chunks; millions would need partitioning or a dedicated engine |
| **BM25 written in SQL** instead of `ts_rank_cd` | `ts_rank_cd` has no IDF, so common words outranked exact article numbers | Term statistics live in materialised views that must be refreshed after indexing |
| **Hybrid + rerank as default**, although dense search alone scored as well overall | Refused 8/8 unanswerable questions (dense: 6/8) and ranked paraphrased questions better (Hit@1 0.82 vs 0.73) | +1.6 s per question and weaker on cross-law questions (Recall@5 0.64 vs 0.71); dense mode stays available (`mode: "dense"`) |
| **Structure-aware chunks** (article → paragraph groups, max 380 tokens, contextual header) | Citations stay at article level; EN and DE chunks align one to one, so duplicates across languages are removed exactly | Long articles are split, which causes chunk-level misses (see Limitations) |
| **Local LLM** (qwen2.5:14b through Ollama) | Questions never leave the machine (GDPR-friendly), no cost per request, reproducible results | Quality is limited by model size: 76% correct, 33% complete (hosted models were not tested) |
| **14B instead of 7B model** | Removed invented citation numbers (6 → 0) and fixed broken German | 1.8× latency, ~9 GB of memory |
| **Abstention sentence chosen in code** (language detection) | The 7B model answered German questions with the English refusal | Only DE and EN are supported |
| **Official Cellar API** instead of scraping EUR-Lex | EUR-Lex shows bot checks to scripts; the Publications Office provides the API for automated reuse | Depends on one public service being available |
| **Metadata-only request log** | Users may type personal data into questions; data minimisation (GDPR Art. 5(1)(c)) | Debugging relies on the eval set instead of production questions |

## Quickstart

Requirements: [Docker](https://docs.docker.com/) (or Colima), [Ollama](https://ollama.com),
[uv](https://docs.astral.sh/uv/), ~25 GB free disk, 16 GB+ RAM for the default 14B model.

### Option A: on macOS with the Apple GPU (fastest)

```bash
git clone https://github.com/pranav1111/paragraf.git && cd paragraf
ollama pull qwen2.5:14b                 # or qwen2.5:7b on smaller machines (set PARAGRAF_LLM_MODEL)
docker compose up -d db                 # PostgreSQL 17 + pgvector, schema applied automatically
uv sync
uv run sh scripts/build_index.sh        # download → parse → chunk → embed (first run downloads ~4.5 GB of models)
uv run uvicorn paragraf.api:app --port 8000
```

Open http://localhost:8000 (web UI) or http://localhost:8000/docs (API).

### Option B: everything except the LLM in Docker (CPU)

> With **Colima**, clone the repository somewhere inside your home folder: Colima only shares `$HOME` with its VM,
> and a project elsewhere (e.g. `/tmp`) silently mounts empty folders, so the database starts without its schema.

```bash
ollama pull qwen2.5:14b                 # Ollama runs on the host
docker compose up -d db
docker compose run --rm api sh scripts/build_index.sh
docker compose up -d api                # → http://localhost:8000
```

Measured on Colima (4 vCPU): building the index takes ~8 minutes on CPU (44 s on the Apple GPU), search
~20 s per question (the cross-encoder reranker) against ~2 s in Option A, and a fresh clone reaches its first
answer in ~10 minutes once the models are downloaded. Use Option A for demos. Troubleshooting in
[`notes/deployment-notes.md`](notes/deployment-notes.md).

### Command line

```bash
uv run python -m paragraf.ask "Which AI practices are prohibited?"
uv run python -m paragraf.search "Art. 17 right to be forgotten"     # compare the four retrieval modes
```

## Configuration

Every setting can be overridden with an environment variable or a `.env` file (see `.env.example`):

| Variable | Default | Meaning |
|---|---|---|
| `PARAGRAF_LLM_MODEL` | `qwen2.5:14b` | Generator model (`qwen2.5:7b` is about 2× faster) |
| `PARAGRAF_LLM_BASE_URL` | `http://localhost:11434/v1` | Any OpenAI-compatible endpoint |
| `PARAGRAF_DATABASE_URL` | `postgresql://paragraf:paragraf@localhost:5432/paragraf` | PostgreSQL with pgvector |
| `PARAGRAF_DEVICE` | `mps` | `mps` (Apple GPU), `cuda` or `cpu` for embeddings and reranking |
| `PARAGRAF_CANDIDATES` / `PARAGRAF_TOP_K` | `30` / `5` | Candidates before reranking / sources sent to the LLM |
| `PARAGRAF_PROMPT_VERSION` | `v1` | `v2` is the documented (worse) experiment |

## Evaluation

```bash
uv run python eval/run_retrieval.py                 # 4 retrieval modes, no LLM needed
uv run python eval/run_answers.py hybrid+rerank     # answers for all 80 questions
uv run python eval/judge.py local hybrid+rerank     # free local judge (or: haiku, needs PARAGRAF_ANTHROPIC_API_KEY)
uv run python eval/report.py                        # → eval/results/report.md
```

The gold set (`eval/gold.jsonl`) was drafted from the law text and reviewed question by question; 13 questions
that overlap with development tests are marked `dev_seen` and reported separately. Reference labels for judge
validation are in `eval/assistant_labels.jsonl` (labelled by Claude, not by a human; stated in the report).

## Project structure

```
src/paragraf/   download · ingest · chunk · index · retrieve · generate · api · ask · search · config
sql/            schema: chunks table, HNSW + GIN indexes, BM25 statistics (materialised views)
eval/           gold set, retrieval/answer runners, judge, labelling tools, report
notes/          data, retrieval, generation and evaluation findings
tests/          unit tests (CI) and integration tests (need PostgreSQL / Ollama)
```

## Limitations and next steps
- Answers are often **incomplete** (they stop after the first case, tier or deadline); read the cited article.
  Next: *small-to-big* retrieval (add the rest of an article when one of its chunks is retrieved).
- Only the GDPR, AI Act and NIS2 (EU level), without recitals. Next: recitals and German national law (BDSG).
- Evaluated on 80 questions: differences of a few points are not statistically significant (tests in the notes).
- Answers **vary between runs** (temperature 0.1): with identical sources, "Wann muss eine Datenpanne gemeldet
  werden?" cited GDPR Art. 33 in three runs and NIS2 Art. 23 (a 72-hour rule for cyber incidents) in the next
  three. The evaluation is a single run per question. Next: repeat runs to measure the variance, or temperature 0.
- The judge was validated against labels written by Claude, not by a human. Next: human labels on the same 40 answers.
- Search takes ~20 s on CPU (the reranker). Next: a smaller reranker, or dense mode on machines without a GPU.
- Not legal advice.

## Data and licence
EU legislation from EUR-Lex / the Publications Office of the EU, reused under Commission Decision 2011/833/EU.
