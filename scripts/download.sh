#!/usr/bin/env bash
# Download the six source documents (GDPR, AI Act, NIS2 in EN and DE) as XHTML from the
# EU Publications Office's official machine-readable API ("Cellar", content negotiation).
# The EUR-Lex website itself answers scripts with a bot check (risk R3), so we use the API
# that is meant for automated reuse. Fallback: save the pages manually from a browser.
set -euo pipefail
mkdir -p data/raw
for pair in GDPR:32016R0679 AIACT:32024R1689 NIS2:32022L2555; do
  law=${pair%%:*}; celex=${pair##*:}
  for lang in EN:eng DE:deu; do
    code=${lang%%:*}; iso=${lang##*:}
    out="data/raw/${law}_${code}.html"
    curl -sSL --fail -H "Accept: application/xhtml+xml" -H "Accept-Language: ${iso}" \
      -o "$out" "http://publications.europa.eu/resource/celex/${celex}"
    printf "%-22s %9s bytes\n" "$out" "$(wc -c < "$out" | tr -d ' ')"
    sleep 1   # be polite to a public service
  done
done
