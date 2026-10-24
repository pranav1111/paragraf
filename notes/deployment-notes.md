# Deployment notes (Phase 10)

## Measured (Colima VM: 4 vCPU, 6 GB; host: Apple M-series, 24 GB)
| | Apple GPU (Option A, native) | CPU in Docker (Option B) |
|---|---|---|
| Embedding 1,058 chunks | 44 s (24 chunks/s) | 482 s (2.2 chunks/s) |
| Search per question (hybrid + rerank) | ~2 s | ~20 s |
| Answer (qwen2.5:14b on the host) | ~14 s | ~14–20 s (host CPU shared with the VM) |
| Fresh clone → first answer (models already cached) | – | ~9.6 min |
| API image size | – | ~3.0 GB (CPU-only PyTorch; hardening in Project 3) |
| API container memory | – | ~3.4 GB after the first questions |

The index built in Docker is identical to the one built natively (same 1,058 chunks, same per-law counts):
the pipeline is reproducible across machines and CPU/GPU.

## Gotchas found while testing (and how to avoid them)
1. **A stale local server can answer instead of the container.** A `uvicorn` started earlier still held port 8000.
   Docker Desktop reports "port is already allocated"; **Colima's port forwarder fails silently**, so requests
   went to the old process and the first "Docker works" result was wrong. Check: the container's own log must
   show the requests (`docker logs paragraf-api-1 | grep "POST /ask"`), or `lsof -i :8000`.
2. **Colima only shares `$HOME` with its VM.** A clone under `/tmp` made Docker mount an *empty directory* in
   place of `sql/schema.sql` ("could not read from input file: Is a directory"), so the database started without
   tables. Keep projects inside the home folder.
3. **Compose project names come from the folder name.** A second clone in another folder also called `paragraf`
   shares the *same* project, and therefore the same database volume; `docker compose down -v` there would delete
   the original database. Use `docker compose -p <unique-name>` for side-by-side copies.
4. **Bind-mounted secrets stay out of images.** `.dockerignore` excludes `.env`, `data/`, `eval/results/`,
   `.git`; settings come from environment variables set in `docker-compose.yml`.

## CI
GitHub Actions (`.github/workflows/ci.yml`): `uv sync --frozen` (CPU-only PyTorch on Linux from the lock), ruff,
unit tests without database, models or LLM. Token permissions: `contents: read`; checkout without persisted
credentials. First run: green.
