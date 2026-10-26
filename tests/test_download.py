import httpx
import pytest

from paragraf.download import check, fetch, read_manifest, secure_url, sha256, write_manifest

CELLAR = "http://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0006.03/DOC_1"


def test_redirects_on_the_eu_host_are_upgraded_to_https():
    assert secure_url(CELLAR) == CELLAR.replace("http://", "https://")
    assert secure_url("http://publications.europa.eu:80/resource/x?a=1") == "https://publications.europa.eu/resource/x?a=1"
    assert secure_url("/resource/y", base="https://publications.europa.eu/resource/celex/1").endswith("/resource/y")


@pytest.mark.parametrize("url", ["https://evil.example/resource/x", "http://publications.europa.eu.evil.example/x",
                                 "https://user@evil.example/x"])
def test_other_hosts_are_refused(url):
    with pytest.raises(ValueError):
        secure_url(url)


def test_fetch_never_follows_a_downgrade():
    """The real server answers an https request with a redirect to plain http (finding F1)."""
    seen = []

    def server(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        if "/celex/" in request.url.path:
            return httpx.Response(303, headers={"location": CELLAR})
        return httpx.Response(200, content=b"<html>law</html>")

    with httpx.Client(transport=httpx.MockTransport(server), follow_redirects=False) as client:
        assert fetch(client, "https://publications.europa.eu/resource/celex/32016R0679", "eng") == b"<html>law</html>"
    assert all(url.startswith("https://") for url in seen) and len(seen) == 2


def test_redirect_to_another_host_is_refused():
    def server(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://evil.example/fake-gdpr"})

    with (httpx.Client(transport=httpx.MockTransport(server), follow_redirects=False) as client,
          pytest.raises(ValueError)):
        fetch(client, "https://publications.europa.eu/resource/celex/32016R0679", "eng")


def test_manifest_roundtrip_and_mismatch(tmp_path):
    path = tmp_path / "sources.sha256"
    write_manifest({"GDPR_EN.html": sha256(b"law")}, path)
    assert path.read_text() == f"{sha256(b'law')}  GDPR_EN.html\n"           # same format as `shasum -a 256`
    manifest = read_manifest(path)
    check("GDPR_EN.html", sha256(b"law"), manifest)                          # passes silently
    with pytest.raises(SystemExit, match="checksum mismatch"):
        check("GDPR_EN.html", sha256(b"tampered law"), manifest)
    with pytest.raises(SystemExit, match="no checksum"):
        check("NIS2_DE.html", sha256(b"law"), manifest)
