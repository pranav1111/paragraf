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
