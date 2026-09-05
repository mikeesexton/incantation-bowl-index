CREATE TABLE saturation_sweeps (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    strategy TEXT NOT NULL,
    baseline_distinct_objects INTEGER NOT NULL CHECK (baseline_distinct_objects >= 0),
    net_new_distinct_objects INTEGER NOT NULL CHECK (net_new_distinct_objects >= 0),
    net_new_rate REAL NOT NULL CHECK (net_new_rate >= 0),
    revealed_new_source_class INTEGER NOT NULL CHECK (revealed_new_source_class IN (0,1)),
    status TEXT NOT NULL CHECK (status IN ('complete','invalidated')),
    completed_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE manual_audits (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    stratum TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    checked_by TEXT NOT NULL,
    citation_verified INTEGER NOT NULL CHECK (citation_verified IN (0,1)),
    identifier_verified INTEGER NOT NULL CHECK (identifier_verified IN (0,1)),
    claims_source_attributed INTEGER NOT NULL CHECK (claims_source_attributed IN (0,1)),
    result TEXT NOT NULL CHECK (result IN ('pass','pass_with_notes','fail')),
    notes TEXT,
    UNIQUE (object_id, stratum)
);
