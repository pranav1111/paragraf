"""Download the six source documents (GDPR, AI Act, NIS2 in EN and DE) as XHTML.

Uses the EU Publications Office's machine-readable API ("Cellar", content negotiation). The EUR-Lex website
answers scripts with a bot check, so we use the API that is meant for automated reuse. Pure Python (httpx),
so it works the same on macOS, Linux and inside the Docker image.

Integrity (finding F1 in Warden's threat model): the server redirects even https requests to plain http, which
would let anyone on the network alter the law texts. So every redirect is upgraded back to https, redirects to
any other host are refused, and every file must match its SHA-256 in data/sources.sha256 before it is written.
When the EU publishes a new version, review it and record the new checksums:

    python -m paragraf.download --update-manifest
"""
import hashlib
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

CELEX = {"GDPR": "32016R0679", "AIACT": "32024R1689", "NIS2": "32022L2555"}
LANGUAGES = {"EN": "eng", "DE": "deu"}
RAW = Path("data/raw")
MANIFEST = Path("data/sources.sha256")       # `cd data/raw && shasum -a 256 -c ../sources.sha256` checks it
HOST = "publications.europa.eu"
MAX_REDIRECTS = 5


def secure_url(url: str, base: str = "") -> str:
    """Absolute https URL on the Publications Office host. Any other host is refused."""
    parts = urlsplit(urljoin(base, url))
    if parts.hostname != HOST:
        raise ValueError(f"refusing to fetch from {parts.hostname!r}, only {HOST} is trusted")
    return urlunsplit(("https", HOST, parts.path, parts.query, ""))


def fetch(client: httpx.Client, url: str, language: str) -> bytes:
    """GET with redirects followed by hand, so that none of them can downgrade to http."""
    url = secure_url(url)
    for _ in range(MAX_REDIRECTS + 1):
        response = client.get(url, headers={"Accept-Language": language})
        if response.is_redirect:
            url = secure_url(response.headers["location"], base=url)
            continue
        response.raise_for_status()
        return response.content
    raise RuntimeError(f"more than {MAX_REDIRECTS} redirects for {url}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_manifest(path: Path = MANIFEST) -> dict[str, str]:
    """'<hex>  <file name>' per line, the format of `shasum -a 256`."""
    if not path.exists():
        return {}
    return {name: digest for digest, name in (line.split(maxsplit=1) for line in path.read_text().splitlines() if line)}


def write_manifest(hashes: dict[str, str], path: Path = MANIFEST) -> None:
    path.write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())))


def check(name: str, digest: str, manifest: dict[str, str]) -> None:
    expected = manifest.get(name)
    if expected is None:
        sys.exit(f"{name}: no checksum in {MANIFEST}. Review the file, then run with --update-manifest.")
    if digest != expected:
        sys.exit(f"{name}: checksum mismatch (expected {expected[:12]}…, got {digest[:12]}…). The source changed "
                 f"or was altered in transit; nothing was written. Review it, then run with --update-manifest.")


def main(argv: list[str] | None = None) -> None:
    update = "--update-manifest" in (sys.argv[1:] if argv is None else argv)
    manifest, seen = read_manifest(), {}
    RAW.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=False, timeout=120,
                      headers={"Accept": "application/xhtml+xml",
                               "User-Agent": "paragraf (student project; github.com/pranav1111)"}) as client:
        for law, celex in CELEX.items():
            for code, iso in LANGUAGES.items():
                name = f"{law}_{code}.html"
                data = fetch(client, f"https://{HOST}/resource/celex/{celex}", iso)
                digest = sha256(data)
                if not update:
                    check(name, digest, manifest)
                (RAW / name).write_bytes(data)
                seen[name] = digest
                print(f"{RAW / name}  {len(data):>9,} bytes  sha256 {digest[:12]}…  {'recorded' if update else 'verified'}")
                time.sleep(1)                           # be polite to a public service
    if update:
        write_manifest(seen)
        print(f"Checksums written to {MANIFEST}. Commit it together with a note on what changed.")


if __name__ == "__main__":
    main()
