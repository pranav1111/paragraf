"""Download the six source documents (GDPR, AI Act, NIS2 in EN and DE) as XHTML.

Uses the EU Publications Office's machine-readable API ("Cellar", content negotiation). The EUR-Lex website
answers scripts with a bot check, so we use the API that is meant for automated reuse. Pure Python (httpx),
so it works the same on macOS, Linux and inside the Docker image.
"""
import time
from pathlib import Path

import httpx

CELEX = {"GDPR": "32016R0679", "AIACT": "32024R1689", "NIS2": "32022L2555"}
LANGUAGES = {"EN": "eng", "DE": "deu"}
RAW = Path("data/raw")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=120,
                      headers={"Accept": "application/xhtml+xml",
                               "User-Agent": "paragraf (student project; github.com/pranav1111)"}) as client:
        for law, celex in CELEX.items():
            for code, iso in LANGUAGES.items():
                out = RAW / f"{law}_{code}.html"
                response = client.get(f"http://publications.europa.eu/resource/celex/{celex}",
                                      headers={"Accept-Language": iso})
                response.raise_for_status()
                out.write_bytes(response.content)
                print(f"{out}  {len(response.content):>9,} bytes")
                time.sleep(1)                           # be polite to a public service


if __name__ == "__main__":
    main()
