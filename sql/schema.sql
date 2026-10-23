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

-- BM25 statistics. ts_rank_cd has no IDF (rare words are not weighted higher), so keyword search
-- ranks with real BM25 computed from these views. Refresh after loading: see paragraf/index.py.
CREATE MATERIALIZED VIEW IF NOT EXISTS chunk_terms AS
    SELECT c.id, c.lang, t.lexeme AS term, coalesce(array_length(t.positions, 1), 1) AS tf
    FROM chunks c, unnest(c.tsv) AS t;
CREATE INDEX IF NOT EXISTS chunk_terms_lang_term_idx ON chunk_terms (lang, term);

CREATE MATERIALIZED VIEW IF NOT EXISTS chunk_len AS
    SELECT id, lang, sum(tf) AS len FROM chunk_terms GROUP BY id, lang;
CREATE UNIQUE INDEX IF NOT EXISTS chunk_len_id_idx ON chunk_len (id);

CREATE MATERIALIZED VIEW IF NOT EXISTS term_df AS
    SELECT lang, term, count(*) AS df FROM chunk_terms GROUP BY lang, term;
CREATE UNIQUE INDEX IF NOT EXISTS term_df_lang_term_idx ON term_df (lang, term);

CREATE MATERIALIZED VIEW IF NOT EXISTS lang_stats AS
    SELECT lang, count(*) AS n, avg(len) AS avgdl FROM chunk_len GROUP BY lang;
