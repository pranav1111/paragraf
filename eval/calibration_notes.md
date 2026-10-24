# Annotation guidelines (read before `eval/label.py`)

Round 1 (20 answers, `human_labels_calibration.jsonl`) was graded yes/yes/yes for every answer. A second
look found real problems in about half of them. This happens to almost everyone in a first round: fluent
answers *read* as correct. Round 1 is therefore used as a **calibration set**. Its labels are kept, but
they are not used to validate the judges. Round 2 grades 20 *different* answers, blind.

## The four questions

| Question | Answer **n** when… |
|---|---|
| **Faithful** | any claim in the answer is not supported by the sources, even a small detail or a number |
| **Correct** | a key fact is wrong, OR a true rule is applied to the wrong person or situation, OR an exception is invented or misplaced, OR the answer is so garbled it does not really answer |
| **Complete** | a main point of the reference answer is missing (e.g. one of three legal cases, one of two fine tiers, the final-report deadline) |
| **Citations right** | a [n] points to a source that does not contain that claim, or a number outside 1–5 is used |

Method that works: (1) read the reference, (2) list its main points in your head, (3) read the answer and
tick them off, (4) for every sentence of the answer, find the sentence in the cited source.

## Worked examples from round 1 (my assessment)

| ID | Faithful | Correct | Complete | Citations | Why |
|---|---|---|---|---|---|
| q052 | y | y | y | **n** | Content right; cites [5] (Art. 42 Certification) but the rule is in [2] (Art. 30(5)). |
| q019 | y | y | y | y | AI-system definition reproduced correctly. |
| q009 | y | y | **n** | **n** | Leaves the conditions vague ("subject to certain conditions": consent/contract and automated means are missing); cites [3] (Art. 13) for the public-interest exception, which is in Art. 20(3) = [1]. |
| q035 | y | y | y | y | |
| q053 | y | y | **n** | y | Only one erasure ground named out of six; the [3] claim comes from Art. 19 (informing recipients), OK. |
| q067 | y | y | **n** | y | Only the EUR 20m / 4 % tier; the EUR 10m / 2 % tier is missing. |
| q072 | y | y | **n** | **n** | Misses "profiling is always high-risk"; cites [2][3] = Art. 25 (value chain), which says nothing about classification. |
| q070 | y | y | **n** | y | 24 h and 72 h correct, but the one-month final report is missing. |
| q042 | y | y | y | y | Lists the Art. 32(2) powers and adds enforcement measures from Art. 32(4)–(5); all supported. |
| q045 | y | y | y | y | |
| q056 | y | y | **n** | y | Leaves out the first items of the list (incident handling, business continuity, supply chain security). |
| q015 | y | y | y | y | |
| q005 | y | y | y | **n** | The categories are right, but it cites **[37]** with only 5 sources (invented citation). |
| q010 | **n** | **n** | **n** | y | Says the controller may continue with "compelling legitimate grounds": that exception is Art. 21(1). For **direct marketing** (Art. 21(2)–(3)) the right is absolute. Wrong rule applied. |
| q014 | y | y | y | **n** | Content right; cites [5] = Art. 85 instead of Art. 30. |
| q069 | y | y | y | y | Simplified ("müssen geschult werden") but in substance Art. 4. Borderline; accepted. |
| q066 | y | **n** | **n** | y | First sentence is not meaningful German; none of the three Art. 37(1) cases is named. Does not answer the question. |
| q012 | y | y | **n** | **n** | Default rule's specifics (amount, extent, storage period, accessibility) missing; cites [2] = Art. 47. |
| q065 | y | y | y | y | |
| q062 | y | **n** | **n** | **n** | Claims "the GDPR and NIS2 require…" but lists only NIS2 measures (GDPR Art. 32 was not retrieved); cites [1] = NIS2 Art. 1 for an Art. 21 measure. |

Summary of round 1 by this assessment: correct 17/20, complete 10/20, citations right 12/20, faithful 19/20.
