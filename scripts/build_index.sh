#!/usr/bin/env sh
# Build the search index from scratch: download -> parse -> chunk -> embed + load into PostgreSQL.
#   on your Mac:      uv run sh scripts/build_index.sh             (Apple GPU, ~1 min for embeddings)
#   in Docker:        docker compose run --rm api sh scripts/build_index.sh   (CPU, several minutes)
set -e
python -m paragraf.download
python -m paragraf.ingest
python -m paragraf.chunk
python -m paragraf.index
