# Generation observations (Phase 6)

Model: `qwen2.5:7b` via Ollama (OpenAI-compatible API), temperature 0.1, top 5 sources after
hybrid + rerank. Six checkpoint questions, each answer checked by hand against the law text.

| # | Question | Answer (summary) | Verdict |
|---|---|---|---|
| 1 | Wann muss eine Datenpanne gemeldet werden? | "unverzüglich und möglichst innerhalb von 72 Stunden … es sei denn … kein Risiko" [GDPR Art. 33] | ✅ correct, cited |
| 2 | Which AI practices are prohibited under the AI Act? | 7 practices from Art. 5, all cited | ✅ mostly; ⚠️ 7 sentences (rule: max 6); point (d) loses "criminal offence" |
| 3 | What fines can be imposed for infringements of the GDPR? | €10m / 2% and €20m / 4% of worldwide turnover, whichever is higher [Art. 83] | ✅ exact |
| 4 | Darf ich meine Daten von einem Unternehmen löschen lassen? | Erasure when data is no longer necessary or consent is withdrawn [Art. 17] | ✅ content; ⚠️ clumsy German grammar |
| 5 | What is the speed limit on the German Autobahn? | exact English abstention sentence | ✅ |
| 6 | Wie hoch ist das Kindergeld in Deutschland? | English abstention sentence for a German question | ❌ → fixed (see below) |

**Invalid (invented) citations: 0** in all answers.

## Fix: deterministic language handling
Letting the model choose between two abstention sentences failed for a German question (#6). Now the
code detects the question language (function words + umlauts; unit-tested on 6 questions) and puts
**only** the matching sentence and "Answer in German/English" into the system prompt. #6 now returns
"Dazu habe ich in den bereitgestellten Rechtstexten nichts gefunden." Lesson: move decisions that can
be made deterministically out of the prompt and into code.

## Known limits (→ Phase 9 experiments)
- **German fluency of a 7B model**: content correct, grammar sometimes broken (#4). Try a larger or newer
  model and measure answer quality and latency (risk R4).
- **Instruction following**: length rule ignored once (#2). Measure how often in Phase 9.
- **Latency**: retrieval 1.6–2.2 s (reranker) + generation 5–8 s (15 s on the first call while the model
  loads). Generation dominates. Options: streaming (perceived latency), smaller context, smaller model.
- The reranker's top score could support abstention (Autobahn/Kindergeld retrieve only fine-related
  articles with low scores). Measure in Phase 9 before relying on it.

## Found by Pranav: an incompleteness error (2026-10-23)
"Muss mein Unternehmen einen Datenschutzbeauftragten benennen?" → retrieval perfect (GDPR Art. 37, 38, 39),
but the answer gives only case (b) of Art. 37(1) (and drops "Kerntätigkeit", which changes the meaning).
Cases (a) public authorities and (c) large-scale processing of Art. 9 / Art. 10 data were in source [1] but
left out. The answer is *faithful* (nothing invented, citation valid), yet *incomplete*. The citation check
cannot catch this; the Phase 9 correctness judge must compare against a reference answer.
→ Add to the gold set with reference: "Yes, if (a) public authority/body (except courts acting in their
judicial capacity), (b) core activities = large-scale regular and systematic monitoring, or
(c) core activities = large-scale processing of special categories (Art. 9) or criminal data (Art. 10)."
Corpus note: in Germany § 38 BDSG additionally requires a DPO when ≥ 20 persons regularly process personal
data automatically; Paragraf cannot know this because the BDSG is not in the corpus (stretch goal).

## Scope error (found while testing the API, 2026-10-23)
"What fines can the AI Act impose for prohibited practices?" → answered "up to EUR 1 500 000" (Art. 100,
which applies only to **Union institutions, bodies, offices and agencies**). The general rule, Art. 99(3):
**up to EUR 35 000 000 or 7% of worldwide annual turnover**, was retrieved as source [2] (reranker 0.957,
chunk AIACT-en-art99-c0) but ignored; the answer cited [2] only for the EUR 15 000 000 / 3% tier of Art. 99(4).
Retrieval was fine; generation applied a true fact to the wrong addressee. The citation check passes because
every number appears in a cited source → only a reference-based correctness judge catches this.
Deliberately **not** fixed by tuning the prompt on this one example (overfitting to anecdotes); added as a
gold-set case. Phase 9 candidates, measured on the whole set: (1) prompt rule "state who each rule applies
to when sources cover different addressees", (2) a larger/newer generator model.

## Citation coverage (seen in the web UI, 2026-10-23)
"Which AI practices are prohibited?" → an 8-item numbered list with all citations at the very end
("[1][2][3]") instead of after each item (rule 1). Readers cannot tell which item comes from which source.
Phase 9 metric: citation coverage = share of sentences/list items that end with a citation.
