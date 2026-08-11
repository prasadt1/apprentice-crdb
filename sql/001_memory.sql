-- Apprentice memory schema (CockroachDB).
-- The warehouse being queried is a separate SQLite prop. This database is the agent's brain.
--
-- Day-one rules:
--   * USING HASH on hot time keys (avoid sequential-range hotspots)
--   * supersession is explicit — do not use GC TTL as audit history
--   * one live semantic rule per rule_key is enforced in a SERIALIZABLE txn (app)

CREATE TABLE IF NOT EXISTS episodic_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    question TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    gold_sql TEXT,
    result_ok BOOL,
    cited_memory_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    notes TEXT,
    INDEX episodic_created_idx (created_at) USING HASH
);

CREATE TABLE IF NOT EXISTS semantic_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    rule_key TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    statement TEXT NOT NULL,
    evidence_episode_id UUID REFERENCES episodic_events (id),
    superseded_by UUID,
    embedding VECTOR(384),
    INDEX semantic_key_idx (rule_key),
    INDEX semantic_created_idx (created_at) USING HASH
);

-- Optional C-SPANN / distributed vector index. May fail on some tiers — do not fake it.
-- Run: apprentice migrate --try-vector-index
-- CREATE VECTOR INDEX semantic_embedding_idx ON semantic_rules (embedding);
