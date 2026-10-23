# Retrieval observations (Phase 5)

Generated with `uv run python scripts/observe_retrieval.py` on 11 hand-picked questions (types: German,
colloquial, paraphrase, exact article reference, acronym). Cell = rank of the expected article in the
top 5 after language-twin removal; ✗ = not in the top 5. **11 questions are far too few to decide
anything**; this is a sanity check. The real comparison is the Phase 9 evaluation on ~80 questions.

| Type | Question | Expected | keyword (ts_rank_cd) | keyword | dense | hybrid | hybrid+rerank |
|---|---|---|---|---|---|---|---|
| DE colloquial | Wann muss eine Datenpanne gemeldet werden? | GDPR-art33 | ✗ | ✗ | **1** | 3 | **1** |
| paraphrase | How fast must I tell the regulator when hackers steal our customer data? | GDPR-art33 | ✗ | ✗ | **1** | 3 | **1** |
| exact ref | Art. 17 right to be forgotten | GDPR-art17 | 3 | **1** | **1** | **1** | **1** |
| exact ref | What does Article 50 of the AI Act require? | AIACT-art50 | ✗ | **1** | **1** | **1** | **1** |
| direct | Which AI practices are banned? | AIACT-art5 | ✗ | ✗ | **1** | **1** | **1** |
| acronym | What is a DPIA and when is it required? | GDPR-art35 | ✗ | ✗ | 2 | ✗ | **1** |
| DE direct | Welche Bußgelder drohen bei Verstößen gegen die DSGVO? | GDPR-art83 | 3 | 3 | **1** | **1** | **1** |
| direct | When must an essential entity send an early warning to the CSIRT? | NIS2-art23 | ✗ | 2 | **1** | **1** | **1** |
| paraphrase | Are company directors personally responsible for cybersecurity under NIS2? | NIS2-art20 | ✗ | ✗ | **1** | ✗ | 4 |
| DE paraphrase | Müssen Mitarbeiter, die KI-Systeme nutzen, geschult werden? | AIACT-art4 | ✗ | ✗ | **1** | 2 | **1** |
| paraphrase | Do I have to tell people they are chatting with a bot? | AIACT-art50 | ✗ | ✗ | **1** | **1** | **1** |
| | **rank 1 (of 11)** | | **0** | **2** | **10** | **6** | **10** |
| | median latency | | 4 ms | 3 ms | 39 ms | 26 ms | 1621 ms |

## What this shows

1. **`ts_rank_cd` is not BM25.** The first keyword search (OR semantics + `ts_rank_cd`) put the right
   article first for 0 of 11 questions, even for "What does Article 50 of the AI Act require?". Cause: no
   IDF. The rare, decisive term `50` appears in 13 English chunks; `articl` in 352, `act` in 306, `ai` in
   255. All were weighted the same, so chunks that say "Article … AI Act" often won.
   **Fix:** real BM25 inside PostgreSQL (materialized views with term frequencies, chunk lengths and
   document frequencies; `sql/schema.sql`). Keyword search now wins exactly where it should (exact
   references: Art. 17, Article 50), and **hybrid went from 3 to 6 of 11** because the keyword list it fuses
   is now useful.
2. **Keyword search cannot handle paraphrases or everyday words**: "Datenpanne" and "banned" never appear
   in the law (it says "Verletzung des Schutzes personenbezogener Daten" and "prohibited"); the acronym
   "DPIA" does not appear either. Dense search handles all of these.
3. **Hybrid without reranking can be worse than dense alone**: fusing a weak list pulls good dense results
   down (Datenpanne: dense rank 1 → hybrid rank 3). The reranker repairs this (10 of 11 at rank 1).
4. **On this small, paraphrase-heavy set, dense alone (10/11, ~40 ms) matches hybrid+rerank (10/11,
   ~1.6 s)**. That is a real question for Phase 9: does reranking pay for 40× the latency? Expect keyword
   and hybrid to matter more on exact references, acronyms like CSIRT, and rare legal terms.
5. **One reranker miss to analyse in Phase 9:** "Are company directors personally responsible for
   cybersecurity under NIS2?" (expected NIS2 Art. 20 "Governance") is rank 1 in dense but rank 4 after
   reranking.
6. **Crowding:** several chunks of the same article can fill the top 5 (NIS2 Art. 23 took 3 slots for the
   breach question). Possible Phase 9 experiment: at most 2 chunks per article.

## Latency (median, warm models)
keyword (BM25) 3 ms · dense 39 ms · hybrid 26 ms · hybrid+rerank 1,621 ms (cross-encoder scoring 30
candidates of up to ~410 tokens on mps). Ideas to test later: 20 candidates, float16 on mps, shorter
max_length.
