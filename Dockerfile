# Paragraf API image. Deliberately simple: Project 3 (Chain of Custody) hardens it (non-root user, smaller base,
# pinned digests, scanning, signing) and uses this version as its "before" measurement.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy \
    PARAGRAF_DEVICE=cpu PATH="/app/.venv/bin:$PATH"
COPY --from=ghcr.io/astral-sh/uv:0.13.3 /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies first (cached layer): only rebuilt when pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY static ./static
COPY sql ./sql
COPY scripts ./scripts
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uvicorn", "paragraf.api:app", "--host", "0.0.0.0", "--port", "8000"]
