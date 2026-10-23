-- Paragraf schema. Runs automatically the first time the database volume is created.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id         text PRIMARY KEY,                      -- e.g. GDPR-de-art33-c0
    law        text NOT NULL,
    lang       text NOT NULL CHECK (lang IN ('en', 'de')),
    article    text NOT NULL,
    title      text NOT NULL,
    url        text NOT NULL,
    content    text NOT NULL,
    ts_config  regconfig NOT NULL,                    -- 'english' or 'german' stemming rules
    tsv        tsvector GENERATED ALWAYS AS (to_tsvector(ts_config, content)) STORED,
    embedding  vector(1024)                           -- bge-m3, filled in Phase 4
);

-- Keyword search: inverted index (word stem -> rows)
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);

-- Meaning search: approximate nearest neighbours; operator class must match the <=> operator
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
