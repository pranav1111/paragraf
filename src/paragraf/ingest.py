"""Parse the official XHTML of each law into articles.

The Publications Office XHTML wraps every article in its own container:
    <div class="eli-subdivision" id="art_5">
      <p class="oj-ti-art">Article 5</p>
      <div class="eli-title"><p class="oj-sti-art">Principles relating to …</p></div>
      <p class="oj-normal">1. Personal data shall be:</p>
      <table> … <p class="oj-normal">(a)</p> … <p class="oj-normal">processed lawfully …</p>
Using these containers (instead of walking every <p> in the file) keeps signatures, footnotes
and annexes that follow the last article out of the data.
"""
import json
import re
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# The files are XHTML; the lenient HTML parser is intentional, so silence bs4's hint.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ARTICLE_RE = re.compile(r"^(?:Article|Artikel)\s+(\d+[a-z]?)$")
MARKER_RE = re.compile(r"^(?:\(?\w{1,5}\)|\d{1,2}\.)$")     # EN "(a)", "(iv)", "3." / DE "a)", "(1)"
CELEX = {"GDPR": "32016R0679", "AIACT": "32024R1689", "NIS2": "32022L2555"}
RAW, OUT = Path("data/raw"), Path("data/processed/articles.jsonl")


@dataclass
class Article:
    law: str
    lang: str
    number: str
    title: str = ""
    paragraphs: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return (f"https://eur-lex.europa.eu/legal-content/{self.lang.upper()}/TXT/HTML/"
                f"?uri=CELEX:{CELEX[self.law]}")


def clean(text: str) -> str:
    return " ".join(text.split())          # also collapses non-breaking spaces


def parse_article(div, law: str, lang: str) -> Article | None:
    heading = div.find("p", class_="oj-ti-art")
    match = ARTICLE_RE.match(clean(heading.get_text(" "))) if heading else None
    if not match:
        return None
    title = div.find("p", class_="oj-sti-art")
    article = Article(law, lang, match.group(1), clean(title.get_text(" ")) if title else "")
    for note in div.select(".oj-note-tag"):          # footnote markers like "( 1 )"
        note.decompose()
    pending = ""
    for p in div.find_all("p"):
        classes = set(p.get("class") or [])
        if classes & {"oj-ti-art", "oj-sti-art"}:
            continue
        text = clean(p.get_text(" "))
        if not text:
            continue
        if MARKER_RE.match(text):                    # list point letter: glue to the next text
            pending = text
            continue
        article.paragraphs.append(f"{pending} {text}".strip())
        pending = ""
    return article


def parse_file(path: Path, law: str, lang: str) -> list[Article]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    divs = soup.find_all("div", class_="eli-subdivision", id=re.compile(r"^art_\d+[a-z]?$"))
    return [a for a in (parse_article(d, law, lang) for d in divs) if a]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for path in sorted(RAW.glob("*.html")):
            law, lang = path.stem.split("_")
            articles = parse_file(path, law, lang.lower())
            print(f"{path.name:16} {len(articles):4} articles")
            for a in articles:
                f.write(json.dumps({**asdict(a), "url": a.url}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
