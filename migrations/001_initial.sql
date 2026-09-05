CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN (
        'book','article','chapter','thesis','catalogue','museum_record','auction_record',
        'dealer_record','database','repository','excavation_report','web_page','archive_snapshot','other'
    )),
    title TEXT NOT NULL,
    authors TEXT,
    issued_year INTEGER,
    container_title TEXT,
    publisher TEXT,
    url TEXT,
    doi TEXT,
    isbn TEXT,
    citation TEXT NOT NULL,
    access_status TEXT NOT NULL DEFAULT 'available' CHECK (access_status IN (
        'available','partial','paywalled','login_required','blocked','offline','not_found','unknown'
    )),
    rights_status TEXT NOT NULL DEFAULT 'unknown' CHECK (rights_status IN (
        'public_domain','open_license','permission','copyrighted','unknown'
    )),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX sources_doi_uq ON sources(lower(doi)) WHERE doi IS NOT NULL;
CREATE INDEX sources_url_idx ON sources(url);

CREATE TABLE captures (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id),
    url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    mime_type TEXT,
    status_code INTEGER,
    sha256 TEXT NOT NULL,
    byte_length INTEGER NOT NULL CHECK (byte_length >= 0),
    storage_path TEXT NOT NULL,
    rights_status TEXT NOT NULL DEFAULT 'unknown',
    headers_json TEXT,
    UNIQUE (url, sha256)
);

CREATE TABLE search_runs (
    id TEXT PRIMARY KEY,
    strategy TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','complete','paused','failed')),
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    notes TEXT
);

CREATE TABLE search_queries (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES search_runs(id),
    source_class TEXT NOT NULL,
    language TEXT,
    query TEXT NOT NULL,
    platform TEXT NOT NULL,
    searched_at TEXT,
    result_count INTEGER CHECK (result_count IS NULL OR result_count >= 0),
    net_new_candidates INTEGER CHECK (net_new_candidates IS NULL OR net_new_candidates >= 0),
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN (
        'planned','searched','exhausted','blocked','follow_up'
    )),
    notes TEXT,
    UNIQUE (source_class, language, query, platform)
);

CREATE TABLE coverage_targets (
    id TEXT PRIMARY KEY,
    source_class TEXT NOT NULL,
    target_name TEXT NOT NULL,
    url TEXT,
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN (
        'planned','in_progress','searched','exhausted','blocked','not_applicable'
    )),
    first_searched_at TEXT,
    last_searched_at TEXT,
    notes TEXT,
    UNIQUE (source_class, target_name)
);

CREATE TABLE objects (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    object_type TEXT NOT NULL DEFAULT 'whole_bowl' CHECK (object_type IN (
        'whole_bowl','fragment','reconstructed','lost_or_unlocated','non_bowl','uncertain'
    )),
    record_status TEXT NOT NULL DEFAULT 'candidate' CHECK (record_status IN (
        'candidate','probable','confirmed','rejected','merged'
    )),
    authenticity TEXT NOT NULL DEFAULT 'unassessed' CHECK (authenticity IN (
        'unassessed','accepted','uncertain','disputed','suspected_fake','modern','pseudo_script'
    )),
    summary TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE appearances (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    locator TEXT NOT NULL,
    title TEXT,
    url TEXT,
    observed_at TEXT,
    description TEXT,
    raw_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_id, locator)
);

CREATE TABLE appearance_object_links (
    appearance_id TEXT NOT NULL REFERENCES appearances(id),
    object_id TEXT NOT NULL REFERENCES objects(id),
    relation_type TEXT NOT NULL DEFAULT 'candidate' CHECK (relation_type IN (
        'primary','candidate','rejected'
    )),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (appearance_id, object_id)
);

CREATE TABLE identifiers (
    id TEXT PRIMARY KEY,
    object_id TEXT REFERENCES objects(id),
    appearance_id TEXT REFERENCES appearances(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    scheme TEXT NOT NULL,
    value TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    assigning_body TEXT,
    confidence REAL NOT NULL DEFAULT 1 CHECK (confidence >= 0 AND confidence <= 1),
    notes TEXT,
    CHECK (object_id IS NOT NULL OR appearance_id IS NOT NULL)
);
CREATE INDEX identifiers_lookup_idx ON identifiers(scheme, normalized_value);

CREATE TABLE claims (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    appearance_id TEXT REFERENCES appearances(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    field TEXT NOT NULL,
    value_text TEXT,
    value_json TEXT,
    normalized_value TEXT,
    certainty TEXT NOT NULL DEFAULT 'reported' CHECK (certainty IN (
        'certain','probable','possible','uncertain','disputed','reported'
    )),
    locator TEXT NOT NULL,
    quotation TEXT,
    notes TEXT,
    supersedes_claim_id TEXT REFERENCES claims(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (value_text IS NOT NULL OR value_json IS NOT NULL)
);
CREATE INDEX claims_object_field_idx ON claims(object_id, field);

CREATE TABLE texts (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    appearance_id TEXT REFERENCES appearances(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    text_type TEXT NOT NULL CHECK (text_type IN (
        'inscription','transcription','transliteration','translation','summary','incipit'
    )),
    language TEXT,
    script TEXT,
    content TEXT NOT NULL,
    editor TEXT,
    locator TEXT NOT NULL,
    rights_status TEXT NOT NULL DEFAULT 'unknown',
    public_ok INTEGER NOT NULL DEFAULT 0 CHECK (public_ok IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE events (
    id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL REFERENCES objects(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'creation','excavation','find','ownership','acquisition','sale','offer','transfer',
        'exhibition','publication','observation','loss','other'
    )),
    start_date TEXT,
    end_date TEXT,
    place TEXT,
    actor TEXT,
    details TEXT NOT NULL,
    certainty TEXT NOT NULL DEFAULT 'reported',
    locator TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE media (
    id TEXT PRIMARY KEY,
    object_id TEXT REFERENCES objects(id),
    appearance_id TEXT REFERENCES appearances(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    capture_id TEXT REFERENCES captures(id),
    media_type TEXT NOT NULL CHECK (media_type IN ('image','drawing','scan','video','other')),
    url TEXT,
    rights_status TEXT NOT NULL DEFAULT 'unknown',
    perceptual_hash TEXT,
    notes TEXT,
    CHECK (object_id IS NOT NULL OR appearance_id IS NOT NULL)
);

CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id),
    lead_type TEXT NOT NULL CHECK (lead_type IN (
        'citation','identifier','collection','person','auction','image','restricted_source','other'
    )),
    description TEXT NOT NULL,
    url TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','in_progress','resolved','blocked','rejected')),
    priority INTEGER NOT NULL DEFAULT 2 CHECK (priority BETWEEN 0 AND 3),
    resolution_notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dedupe_candidates (
    id TEXT PRIMARY KEY,
    object_a_id TEXT NOT NULL REFERENCES objects(id),
    object_b_id TEXT NOT NULL REFERENCES objects(id),
    score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending','same_object','different_objects','insufficient_evidence'
    )),
    method TEXT NOT NULL,
    rationale TEXT NOT NULL,
    decided_at TEXT,
    decided_by TEXT,
    CHECK (object_a_id < object_b_id),
    UNIQUE (object_a_id, object_b_id)
);

CREATE TABLE dedupe_evidence (
    id TEXT PRIMARY KEY,
    dedupe_id TEXT NOT NULL REFERENCES dedupe_candidates(id),
    evidence_type TEXT NOT NULL,
    value_a TEXT,
    value_b TEXT,
    weight REAL NOT NULL,
    supports_match INTEGER NOT NULL CHECK (supports_match IN (-1,0,1)),
    source_id TEXT REFERENCES sources(id),
    notes TEXT
);

CREATE TABLE merge_log (
    id TEXT PRIMARY KEY,
    from_object_id TEXT NOT NULL REFERENCES objects(id),
    into_object_id TEXT NOT NULL REFERENCES objects(id),
    dedupe_id TEXT NOT NULL REFERENCES dedupe_candidates(id),
    merged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    justification TEXT NOT NULL,
    reversible INTEGER NOT NULL DEFAULT 1 CHECK (reversible IN (0,1)),
    reversed_at TEXT,
    CHECK (from_object_id <> into_object_id)
);

CREATE VIEW object_source_evidence AS
SELECT DISTINCT l.object_id, a.source_id
FROM appearance_object_links l
JOIN appearances a ON a.id = l.appearance_id
WHERE l.relation_type <> 'rejected'
UNION
SELECT DISTINCT object_id, source_id FROM claims
UNION
SELECT DISTINCT object_id, source_id FROM texts
UNION
SELECT DISTINCT object_id, source_id FROM events;

