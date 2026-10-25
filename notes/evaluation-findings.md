# Evaluation findings (Phase 9)

Raw numbers: `eval/results/report.md` (answers, judges) and `eval/results/retrieval_summary.md` (retrieval).
Gold set: 80 questions reviewed by Pranav (72 answerable, 8 unanswerable; 13 marked `dev_seen`).

## 1. Retrieval (72 answerable questions, article level)

| Mode | Hit@1 | Recall@5 | MRR | p50 latency |
|---|---|---|---|---|
| keyword (BM25 in Postgres) | 0.56 | 0.80 | 0.66 | 4 ms |
| dense (bge-m3, pgvector HNSW) | **0.92** | **0.97** | **0.94** | 23 ms |
| hybrid (RRF) | 0.75 | 0.96 | 0.83 | 28 ms |
| hybrid + rerank (bge-reranker-v2-m3) | 0.88 | 0.96 | 0.93 | 1,608 ms |

- Dense alone matches the full pipeline at **1/70 of the latency**. The dense vs. rerank difference at Hit@1
  (66 vs 63 of 72) is **not statistically meaningful** at this sample size.
- By type (after the q044 change): the reranker helps on **paraphrased** questions (Hit@1 0.82 vs dense 0.73,
  n = 11). On **cross-law** questions (n = 7), keyword search finds both articles most often (Recall@5 0.86 vs
  dense 0.71) and the reranker is the *weakest* mode (0.64): it scores each chunk against the question on its
  own, so chunks from the law that matches best crowd out the second law. German questions: dense and rerank 1.00.
  (Earlier per-type numbers in this note were computed before q044 moved from paraphrase to cross-law.)
- Unseen-only (61 questions) numbers are the same within 0.01 → no inflation from `dev_seen` questions.
- **q044** ("Can a bank reject my loan using only an algorithm?", gold GDPR Art. 22) is missed by every mode.
  Retrieval returns AI Act Art. 14 / 6 / 26 (human oversight, high-risk credit scoring), which are *also*
  relevant, so the gold label was too narrow (a cross-law question in disguise). **Changed on 2026-10-24 with
  Pranav's approval** to cross-law (GDPR Art. 22 + AI Act Art. 14); the old label, reason and date are kept in
  the question's `change_log`, and its Haiku verdicts were re-judged against the new reference. Effect on
  retrieval: Recall@5 0.96 → 0.97 for every mode (one question).
- **Article-level metrics hide chunk-level misses**: q002 (legal bases) counts as a retrieval hit because GDPR
  Art. 6 chunks were retrieved, but the chunk with the actual list (para 1) was not, so the answer lists none of
  the six bases.

## 2. Validating the judges

No human labels were available in round 2 (Pranav's round-1 labels were all "yes" and became the calibration
set). **40 answers were labelled by Claude (assistant), not a human**, before reading any judge output.

| Judge | Correct agree | Correct κ | Complete agree | Complete κ |
|---|---|---|---|---|
| local qwen2.5:7b | 82% | **0.00** | 60% | 0.16 |
| Claude Haiku 4.5 | 80% | **0.43** | 80% | **0.60** |

- The local judge's agreement is an artefact of the base rate (most answers are correct): **κ = 0 means no
  better than chance**. Percent agreement alone would have hidden this.
- Haiku shows moderate agreement → used for the reported numbers. **Caveat:** Haiku and the labeller are both
  Claude models (possible shared bias). Human labels on the same 40 answers would settle this.
- Judges do not measure **citation accuracy**; from the labels it is **68%** (27/40 answers cite only sources
  that contain the cited claim).

## 3. Answer quality (Haiku judge, baseline prompt v1)

| Metric | hybrid + rerank | dense |
|---|---|---|
| faithfulness (claims supported) | 96% | 96% |
| correct (of all answerable) | 69% | 75% |
| complete | 30% | 30% |
| citation coverage (sentences with a citation) | 88% | 88% |
| invalid citation numbers | 6 | 2 |
| unanswerable correctly refused | **8/8** | 6/8 |
| p50 end-to-end latency | 7.9 s | 5.7 s |

## 4. Failure analysis (what goes wrong, in order of size)

1. **Incomplete answers** (~70%): the model stops after the first case or tier (Art. 37 cases, the EUR 10m / 2 %
   tier, NIS2's one-month final report, accountability in Art. 5, the right to a copy in Art. 15).
2. **Wrong citations** (~1/3 of answers, labels): valid numbers that point to the wrong source (q014, q052,
   q054), and invented numbers ([6], [8], [37]).
3. **Wrong scope / misapplied rule**: Art. 100 (Union institutions) fines given as the general AI Act fine;
   the Art. 21(1) override applied to direct marketing (q010); "risk assessments based on profiling" banned
   without "criminal offences" (q021).
4. **Chunk-level retrieval misses** (q002) and **cross-law questions answered from one law only** (q062).
5. **Language quality**: occasional broken German from the 7B model (q066).

## 5. Fix 1: prompt v2 (before/after)

Prompt v2 (see `src/paragraf/generate.py`) adds three rules derived from the failure classes above:
cite the source per sentence/list item, include every condition/case/exception/deadline/amount, and state who
each rule applies to. Same retrieval (hybrid + rerank), same judge, same 80 questions.

| Metric (Haiku judge, all 80) | v1 | v2 |
|---|---|---|
| correct (of all answerable) | **69%** | 58% |
| complete | 30% | 28% |
| faithfulness | 96% | 95% |
| invalid citation numbers | 6 | 8 |
| false abstention | 4% | 6% |
| avg answer length | 78 words | 97 words |
| p50 latency | 7.9 s | 8.2 s |

**Negative result.** Paired comparison: 14 questions went correct → incorrect, 6 incorrect → correct (exact
McNemar p = 0.115, so not significant, but no sign of improvement). Inspecting the flips: the 7B model
follows the new rules *literally* ("This rule applies to controllers [1][3][4]" appended), stuffs citations to
satisfy rule 1, and, asked to be complete, **mixes neighbouring articles** (q016 applies Art. 33's 72-hour rule
to Art. 34). Answers grow by 25% without becoming more complete.
**Decision:** keep v1 as default (`prompt_version = "v1"`); v2 stays in the code as a documented experiment.
**Lesson:** prompt rules cannot add capability a small model lacks. Next candidates: a larger/newer generator
(a configuration change thanks to the OpenAI-compatible client), and *small-to-big* retrieval (add the rest of
an article when one of its chunks is retrieved) for chunk-level misses like q002.

## 6. Fix 2: a larger generator (qwen2.5:14b), same prompt v1, same retrieval

| Metric (Haiku judge, all 80) | 7b (v1) | 14b (v1) |
|---|---|---|
| correct (of all answerable) | 71% | **76%** |
| complete | 30% | 33% |
| faithfulness | 97% | 95% |
| citation coverage | 88% | **96%** |
| invalid citation numbers | 6 | **0** |
| unanswerable refused | 8/8 | 8/8 |
| p50 / p95 latency | 7.9 s / 11.4 s | **14.3 s / 20.4 s** |

(7b baseline 71% instead of 69% because of the documented q044 change.)
- Correctness: 13 questions improved, 9 got worse (exact McNemar p = 0.52), so **the +5 points are not
  statistically significant** at n = 72.
- **Clear wins:** invented citation numbers 6 → 0 and citation coverage 88% → 96%; fluent German instead of
  garbled sentences (q066); the direct-marketing objection is now stated correctly as absolute (q010); the
  prohibited-practice fine is now the correct EUR 35m / 7% (q031). Its second tier, however, is still taken
  from Art. 100 (Union institutions), a scope error that remains.
- Completeness barely moves (30% → 33%): the model still stops after the first case or tier. Remaining levers:
  small-to-big retrieval (whole article in context) and, if quality matters more than privacy and cost, a hosted
  generator.
- **Cost:** about 1.8× latency (and 9 GB of memory instead of 4.7 GB).

## 7. Summary for the README
- Retrieval: dense bge-m3 search alone reaches Hit@1 0.92 / Recall@5 0.97 at 21 ms; a cross-encoder adds
  1.6 s without a measurable gain overall (it helps on paraphrases and keyword search helps on cross-law questions).
- Answers: faithful (95–97%) but often incomplete (~30%). Prompt rules made a 7B model worse (negative result);
  a 14B model removed invented citations and fixed the clearest scope and language errors at 1.8× latency.
- Judges must be validated: a local 7B judge looked fine on % agreement but had kappa 0.00; Claude Haiku had
  kappa 0.43 (correctness) and 0.60 (completeness) against reference labels (by Claude; human labels pending).
