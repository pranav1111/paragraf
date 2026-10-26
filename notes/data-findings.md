# Data findings (Phase 1)

## 1. EUR-Lex blocks scripted downloads → use the official Cellar API
`curl` to `eur-lex.europa.eu/legal-content/...` returns `202 Accepted` with an empty body and
`x-amzn-waf-action: challenge` (an AWS WAF bot check). This was risk R3 in the program's risk register.
Instead of working around a bot check, `scripts/download.sh` uses the Publications Office's **Cellar** API,
which is meant for machine access: `http://publications.europa.eu/resource/celex/<CELEX>` with
`Accept: application/xhtml+xml` and `Accept-Language: eng|deu` (HTTP 303 → the XHTML manifestation).

## 2. Use the article containers, not a flat walk over all paragraphs
The XHTML wraps each article in `<div class="eli-subdivision" id="art_N">`. A flat walk over every `<p>`
(the approach in the guide) attaches the **signatures and footnotes** after the last article
("Done at Brussels … M. SCHULZ … OJ C 229 …") to GDPR Art. 99. Parsing per container avoids that.
The files also contain the recitals (`rct_*`: 173 in the GDPR), which are not used yet (stretch goal).

## 3. German and English mark list points differently
English: `(a)`, paragraph numbers `1.` · German: `a)`, paragraph numbers `(1)`.
The first marker regex only knew the English style, so German point letters became separate
"paragraphs". Symptom: 121 articles had more paragraphs in German than in English.
After the fix: **0 lone markers and 0 EN/DE paragraph-count mismatches across all 258 article pairs**,
which is a strong signal that both languages are parsed correctly (and it keeps chunk IDs aligned
between languages for Phase 5's "language twins"). Lesson: a quality check that reuses the buggy
pattern cannot find the bug; the cross-language comparison did.

## Result
| Law | CELEX | Articles EN | Articles DE |
|---|---|---|---|
| GDPR | 32016R0679 | 99 | 99 |
| AI Act | 32024R1689 | 113 | 113 |
| NIS2 | 32022L2555 | 46 | 46 |

## Environment note (not about the data)
The project first lived in `~/Desktop/Work`, which is synced to iCloud Drive. iCloud set the macOS *hidden*
flag on files in `.venv` (Python ignores hidden `.pth` files, so `import paragraf` broke), then overwrote a
symlink workaround with its own cloud copy and created a `.venv 2` conflict copy. Fix: the code repos now
live in `~/Developer` (not synced by iCloud). GitHub is the backup for code; iCloud is for documents.

# Chunking findings (Phase 2)

**Measured first** (bge-m3 tokenizer): median article 342 tokens (EN) / 380 (DE), longest 3,688 / 4,265;
about half the articles exceed the 380-token cap; **no single paragraph exceeds it** (longest 249), so no
paragraph ever has to be cut. German needs roughly 10–20% more tokens than English for the same text.

**Aligned twins.** Because EN and DE have identical paragraph structure (Phase 1), the split points are
chosen once per article pair using the larger token count per paragraph, and applied to both languages.
Result: `GDPR-en-art33-c1` and `GDPR-de-art33-c1` always contain the same paragraphs, which Phase 5's
language-twin removal depends on. Chunking each language separately would split them differently.

**Result:** 1,058 chunks (171 / 255 / 103 per law and language), median 293 tokens, p10 93, p90 366,
max 413 (cap + header). 0 twin mismatches. This is below the guide's rough estimate of 1,200–2,000,
because the greedy packing fills chunks up to the cap.

**Small tails:** 27 chunks are under 60 tokens (the last paragraph of a long article). They stay
meaningful because of the contextual header, e.g. "AI Act Art. 16 – Obligations of providers of high-risk
AI systems / (l) ensure … accessibility requirements". Ideas to *measure* in Phase 9 rather than guess now:
(1) merge small tails into the previous chunk, (2) repeat a list's lead-in sentence ("Providers … shall:")
in chunks that start mid-list, (3) a smaller cap (e.g. 200) versus 380.

# Database findings (Phase 3)

PostgreSQL 17.11 + pgvector 0.8.7 (`pgvector/pgvector:pg17`), port bound to 127.0.0.1 only.
One table, two search indexes: GIN on the generated `tsvector` (keywords) and HNSW with
`vector_cosine_ops` (meaning). The schema runs from `docker-entrypoint-initdb.d`, so
`docker compose down -v && docker compose up -d` rebuilds everything (checked).

**Stemming is useful but imperfect** (why we need hybrid search):
- EN: "processed" and "processing" → `process` ✓, but "notified" → `notifi` and "notification" → `notif` (no match).
- DE: "Verarbeitung" → `verarbeit`, but "verarbeitet" stays `verarbeitet`; "meldet" ≠ "Meldung".
  (The guide claims all German forms collapse to `verarbeit`; the Snowball stemmer does not do that.)

**AND semantics:** `websearch_to_tsquery('english', 'When must a data breach be reported?')` →
`'must' & 'data' & 'breach' & 'report'` (every word required). Phase 5 converts it to OR (`|`) and lets
`ts_rank_cd` reward chunks that match more terms.

# Embedding findings (Phase 4)

**Performance:** 1,058 chunks embedded with bge-m3 in **44 s on the Apple GPU (mps), ~24 chunks/s**;
1024-dimensional, normalised vectors (length 1.0000). Query embedding ~120 ms warm (~500 ms for the
first call), vector search 4–11 ms. Re-running the indexer keeps 1,058 rows (idempotent upsert).

**Dense-only preview** (before hybrid search and reranking):
| Question | Top hit |
|---|---|
| "Wann muss eine Datenpanne gemeldet werden?" | GDPR-de-art33-c0 (0.62), then its EN twin |
| "How fast do I have to tell the regulator when hackers steal customer data?" (paraphrase, no shared keywords) | GDPR-en-art33-c0 (0.63) |
| "Which AI practices are banned?" | AIACT-en-art5-c0 (0.71) |
Two things Phase 5 must handle: **language twins** (DE and EN of the same chunk take two of the five
slots) and **several chunks of the same article** crowding the top results.

**Planner gotcha:** right after the bulk upsert, `EXPLAIN` showed a full `Sort` instead of the HNSW index,
because table statistics were stale (estimated 2,110 rows after the re-run). After `ANALYZE chunks`, the
plan uses `Index Scan using chunks_embedding_idx`. The indexer now runs `ANALYZE` after loading.

# Download integrity (2026-10-26, finding F1 in Warden's threat model)

The Publications Office answers `https://…/resource/celex/<id>` with a **303 redirect to plain `http://`**, and the
old downloader followed it: the law texts travelled unencrypted and were never checked, so anyone on the network
could have altered them before they reached the database (an indirect prompt-injection path). Fix: redirects are
followed by hand and upgraded back to https (other hosts are refused), and every file must match its SHA-256 in
`data/sources.sha256` before it is written. The six files fetched over https were byte-identical to the earlier
plain-http downloads, so the existing index was not affected. A new official version has to be reviewed and
recorded with `python -m paragraf.download --update-manifest`.

