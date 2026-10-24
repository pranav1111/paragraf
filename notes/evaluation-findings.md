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
- By type: the reranker helps on **paraphrased** questions (Hit@1 0.75 vs dense 0.67); **keyword** search
  helps on **cross-law** questions (both articles in the top 5: 0.92 vs dense 0.75). German questions: dense and
  rerank 1.00.
- Unseen-only (61 questions) numbers are the same within 0.01 → no inflation from `dev_seen` questions.
- **q044** ("Can a bank reject my loan using only an algorithm?", gold GDPR Art. 22) is missed by every mode.
  Retrieval returns AI Act Art. 14 / 6 / 26 (human oversight, high-risk credit scoring), which are *also*
  relevant, so the gold label is arguably too narrow (a cross-law question in disguise). To decide with Pranav;
  the gold set is not changed after seeing results without a documented reason.
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
