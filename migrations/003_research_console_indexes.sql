-- Read paths used by the local identity explorer and concordance workbench.
CREATE INDEX IF NOT EXISTS idx_appearance_links_object_relation
ON appearance_object_links(object_id, relation_type);

CREATE INDEX IF NOT EXISTS idx_identifiers_object
ON identifiers(object_id);

CREATE INDEX IF NOT EXISTS idx_texts_object_type
ON texts(object_id, text_type);

CREATE INDEX IF NOT EXISTS idx_events_object_type
ON events(object_id, event_type);

CREATE INDEX IF NOT EXISTS idx_media_object_type
ON media(object_id, media_type);

CREATE INDEX IF NOT EXISTS idx_dedupe_status_score
ON dedupe_candidates(status, score DESC);

PRAGMA optimize;
