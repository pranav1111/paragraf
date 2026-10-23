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
