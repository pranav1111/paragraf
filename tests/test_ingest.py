import json
from pathlib import Path

import pytest

from paragraf.ingest import parse_file

SNIPPET = """<html><body>
<div class="eli-subdivision" id="rct_1"><p class="oj-normal">(1) A recital, not an article.</p></div>
<div class="eli-subdivision" id="art_5">
  <p class="oj-ti-art">{word} 5</p>
  <div class="eli-title"><p class="oj-sti-art">Principles</p></div>
  <p class="oj-normal">{p1} Personal data shall be:<span class="oj-super oj-note-tag">( 1 )</span></p>
  <table><tr><td><p class="oj-normal">{a}</p></td><td><p class="oj-normal">processed lawfully;</p></td></tr>
         <tr><td><p class="oj-normal">{b}</p></td><td><p class="oj-normal">collected for specified purposes.</p></td></tr></table>
</div>
<div class="eli-subdivision" id="fnp_1"><p class="oj-normal">Done at Brussels, 27 April 2016.</p></div>
</body></html>"""


@pytest.mark.parametrize("lang,word,p1,a,b", [
    ("en", "Article", "1.", "(a)", "(b)"),          # English marker style
    ("de", "Artikel", "(1)", "a)", "b)"),           # German marker style (the bug found in Phase 1)
])
def test_parses_article_and_glues_point_markers(tmp_path, lang, word, p1, a, b):
    path = tmp_path / "doc.html"
    path.write_text(SNIPPET.format(word=word, p1=p1, a=a, b=b), encoding="utf-8")
    [article] = parse_file(path, "GDPR", lang)
    assert article.number == "5"
    assert article.title == "Principles"
    assert article.paragraphs == [
        f"{p1} Personal data shall be:",            # footnote marker removed
        f"{a} processed lawfully;",
        f"{b} collected for specified purposes.",
    ]


def test_ignores_recitals_and_final_part(tmp_path):
    path = tmp_path / "doc.html"
    path.write_text(SNIPPET.format(word="Article", p1="1.", a="(a)", b="(b)"), encoding="utf-8")
    text = " ".join(p for a in parse_file(path, "GDPR", "en") for p in a.paragraphs)
    assert "recital" not in text and "Done at Brussels" not in text


PROCESSED = Path("data/processed/articles.jsonl")


@pytest.mark.skipif(not PROCESSED.exists(), reason="run scripts/download.sh and paragraf.ingest first")
def test_real_corpus_counts_and_language_alignment():
    articles = [json.loads(line) for line in PROCESSED.open(encoding="utf-8")]
    counts = {}
    for a in articles:
        counts[(a["law"], a["lang"])] = counts.get((a["law"], a["lang"]), 0) + 1
    assert counts == {("GDPR", "en"): 99, ("GDPR", "de"): 99, ("AIACT", "en"): 113,
                      ("AIACT", "de"): 113, ("NIS2", "en"): 46, ("NIS2", "de"): 46}
    by = {(a["law"], a["lang"], a["number"]): len(a["paragraphs"]) for a in articles}
    mismatched = [k for k in by if k[1] == "en" and by[k] != by[(k[0], "de", k[2])]]
    assert mismatched == []
