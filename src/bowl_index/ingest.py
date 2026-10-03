import json
from datetime import datetime

from .ids import new_id
from .catalogue_metadata import corrected_appearance, corrected_identifier_import, corrected_claim_import


SOURCE_FIELDS = (
    "source_type", "title", "authors", "issued_year", "container_title", "publisher", "url",
    "doi", "isbn", "citation", "access_status", "rights_status", "notes",
)


def _append_reading(conn, object_id, appearance_id, source_id, item, locator):
    """Allow exact rehearsal of private reading manifests without replacing rows."""
    values = dict(object_id=object_id, appearance_id=appearance_id, source_id=source_id,
                  text_type=item['text_type'], language=item.get('language'), script=item.get('script'),
                  content=item['content'], editor=item.get('editor'), locator=locator,
                  rights_status=item.get('rights_status', 'unknown'),
                  public_ok=int(bool(item.get('public_ok', False))), notes=item.get('notes'))
    if item.get('created_at'):
        stamp = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError('Reading creation timestamp must be UTC')
        values['created_at'] = stamp.strftime('%Y-%m-%d %H:%M:%S')
    if item.get('id'):
        prior = conn.execute('SELECT * FROM texts WHERE id=?', (item['id'],)).fetchone()
        if prior:
            snapshots = [dict(prior)]
            for table in ('text_proofreading_reviews', 'text_metadata_corrections'):
                snapshots.extend(json.loads(r['before_json']) for r in conn.execute(
                    f'SELECT before_json FROM {table} WHERE text_id=?', (item['id'],)))
            if not any(all(s.get(k) == v for k, v in values.items()) for s in snapshots):
                raise ValueError('Reading ID reused with different evidence')
            return
        from .text_metadata import previously_corrected_import
        if previously_corrected_import(conn, object_id, appearance_id, source_id, item, locator):
            raise ValueError('Retained reading already exists under another ID')
    prior = conn.execute('SELECT id FROM texts WHERE object_id=? AND appearance_id=? AND source_id=? '
                         'AND text_type=? AND content=? AND locator=?',
                         (object_id, appearance_id, source_id, item['text_type'], item['content'], locator)).fetchone()
    if prior:
        if item.get('id') and item['id'] != prior['id']:
            raise ValueError('Reading already exists under another ID')
        return
    values = dict(id=item.get('id') or new_id('text'), **values)
    conn.execute('INSERT INTO texts (%s) VALUES (%s)' % (','.join(values), ','.join('?' for _ in values)),
                 list(values.values()))


def _append_media(conn, object_id, appearance_id, source_id, item):
    capture_id = item.get('capture_id')
    if capture_id:
        capture = conn.execute('SELECT source_id FROM captures WHERE id=?', (capture_id,)).fetchone()
        if not capture or capture['source_id'] != source_id:
            raise ValueError('Media capture must belong to its source')
    values = dict(object_id=object_id, appearance_id=appearance_id, source_id=source_id,
                  capture_id=capture_id, media_type=item.get('media_type', 'image'), url=item.get('url'),
                  rights_status=item.get('rights_status', 'unknown'),
                  perceptual_hash=item.get('perceptual_hash'), notes=item.get('notes'))
    if item.get('id'):
        prior = conn.execute('SELECT * FROM media WHERE id=?', (item['id'],)).fetchone()
        if prior:
            if not all(prior[k] == v for k, v in values.items()):
                raise ValueError('Media ID reused with different evidence')
            return
    prior = conn.execute('SELECT id FROM media WHERE object_id=? AND appearance_id=? AND source_id=? '
                         'AND media_type=? AND url IS ?',
                         (object_id, appearance_id, source_id, values['media_type'], values['url'])).fetchone()
    if prior:
        if item.get('id') and item['id'] != prior['id']:
            raise ValueError('Media already exists under another ID')
        return
    values = dict(id=item.get('id') or new_id('media'), **values)
    conn.execute('INSERT INTO media (%s) VALUES (%s)' % (','.join(values), ','.join('?' for _ in values)),
                 list(values.values()))


def normalize_identifier(scheme, value):
    normalized = " ".join(value.strip().casefold().split())
    if scheme.casefold() == "collection designation":
        # Catalogue typography varies between `MS2053/13`, `MS 2053/13`,
        # and `MS 2053 / 13`; whitespace is not semantically meaningful.
        normalized = "".join(normalized.split())
    return normalized


def add_source(conn, record):
    required = ("source_type", "title", "citation")
    missing = [field for field in required if not record.get(field)]
    if missing:
        raise ValueError("source missing required fields: %s" % ", ".join(missing))

    # Source manifests are deliberately re-runnable.  Prefer stable scholarly
    # identifiers, then URLs, and finally an exact citation for offline records.
    # This also turns the case-insensitive DOI uniqueness constraint into a clean
    # idempotent lookup rather than an IntegrityError on a second ingest.
    existing = None
    if record.get("id"):
        existing = conn.execute("SELECT id FROM sources WHERE id=?", (record["id"],)).fetchone()
    if not existing and record.get("doi"):
        existing = conn.execute(
            "SELECT id FROM sources WHERE lower(doi)=lower(?)", (record["doi"],)
        ).fetchone()
    if not existing and record.get("url"):
        existing = conn.execute("SELECT id FROM sources WHERE url=?", (record["url"],)).fetchone()
    if not existing and not record.get("doi") and not record.get("url"):
        existing = conn.execute(
            "SELECT id FROM sources WHERE citation=?", (record["citation"],)
        ).fetchone()
    if existing:
        current = conn.execute("SELECT * FROM sources WHERE id=?", (existing["id"],)).fetchone()
        record = dict(record)
        # An old deposit or discovery manifest must not restore metadata that an
        # evidence-bound correction has superseded. Protect only changed fields;
        # genuinely new metadata still follows the ordinary import path.
        for correction in conn.execute(
            "SELECT before_json,after_json FROM source_corrections WHERE source_id=?",
            (existing["id"],),
        ):
            before = json.loads(correction["before_json"])
            after = json.loads(correction["after_json"])
            for field in SOURCE_FIELDS:
                if (field in record and before[field] != after[field]
                        and record[field] == before[field]):
                    record[field] = current[field]
        fields = [field for field in SOURCE_FIELDS
                  if field in record and record[field] != current[field]]
        if fields:
            conn.execute(
                "UPDATE sources SET %s,updated_at=CURRENT_TIMESTAMP WHERE id=?"
                % ",".join("%s=?" % field for field in fields),
                [record[field] for field in fields] + [existing["id"]],
            )
        return existing["id"]

    source_id = record.get("id") or new_id("source")
    fields = [field for field in SOURCE_FIELDS if field in record]
    values = [record[field] for field in fields]
    if record.get('created_at'):
        stamp = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError('Source creation timestamp must be UTC')
        fields.extend(['created_at', 'updated_at'])
        values.extend([stamp.strftime('%Y-%m-%d %H:%M:%S')] * 2)
    conn.execute(
        "INSERT INTO sources (id,%s) VALUES (?,%s)" % (
            ",".join(fields), ",".join("?" for _ in fields)
        ),
        [source_id] + values,
    )
    return source_id


def add_lead(conn, record):
    source_id = record.get("source_id")
    if record.get("source"):
        source_id = add_source(conn, record["source"])
    if not record.get("description"):
        raise ValueError("lead missing required field: description")
    existing = None
    if record.get("id"):
        existing = conn.execute("SELECT id FROM leads WHERE id=?", (record["id"],)).fetchone()
    if not existing:
        existing = conn.execute(
            "SELECT id FROM leads WHERE source_id IS ? AND description=?",
            (source_id, record["description"]),
        ).fetchone()
    if existing:
        conn.execute(
            "UPDATE leads SET lead_type=?,description=?,url=?,status=?,priority=?,"
            "resolution_notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (
                record.get("lead_type", "citation"), record["description"], record.get("url"),
                record.get("status", "open"), record.get("priority", 2),
                record.get("resolution_notes"), existing["id"],
            ),
        )
        return existing["id"]
    lead_id = record.get("id") or new_id("lead")
    conn.execute(
        "INSERT INTO leads (id,source_id,lead_type,description,url,status,priority,resolution_notes) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            lead_id, source_id, record.get("lead_type", "citation"), record["description"],
            record.get("url"), record.get("status", "open"), record.get("priority", 2),
            record.get("resolution_notes"),
        ),
    )
    return lead_id


def add_candidate(conn, record):
    # Some discovery manifests preserve the source's authenticity wording while
    # the database uses a deliberately small review vocabulary.
    authenticity_aliases = {
        "accepted_by_seller": "unassessed",
        "suspected_modern_alteration": "disputed",
    }
    if record.get("authenticity") in authenticity_aliases:
        record = dict(record)
        record["authenticity"] = authenticity_aliases[record["authenticity"]]
    # Explicitly declared paraphrases are commentary, never literal translations.
    from .text_metadata import validate_text_classification, previously_corrected_import
    for text in record.get("texts", []):
        validate_text_classification(text)
    source = record.get("source")
    source_id = record.get("source_id")
    if source:
        source_id = add_source(conn, source)
    if not source_id:
        raise ValueError("candidate must include source_id or source")

    appearance = record["appearance"]
    existing = conn.execute(
        "SELECT l.object_id,a.id AS appearance_id FROM appearances a "
        "JOIN appearance_object_links l ON l.appearance_id=a.id "
        "WHERE a.source_id=? AND a.locator=? AND l.relation_type <> 'rejected' LIMIT 1",
        (source_id, appearance["locator"]),
    ).fetchone()
    if not existing:
        existing = corrected_appearance(conn, source_id, appearance["locator"])
    if existing:
        # Compact manifests evolve as concordances are discovered. Re-ingesting
        # the same appearance should safely add newly documented identifiers
        # without creating another object or duplicating claims.
        for identifier in record.get("identifiers", []):
            value = identifier["value"]
            normalized = identifier.get("normalized_value", normalize_identifier(identifier["scheme"], value))
            if corrected_identifier_import(conn, existing["object_id"], source_id, identifier["scheme"], normalized):
                continue
            if conn.execute(
                "SELECT 1 FROM identifiers WHERE object_id=? AND source_id=? AND scheme=? "
                "AND normalized_value=?",
                (existing["object_id"], source_id, identifier["scheme"], normalized),
            ).fetchone():
                continue
            conn.execute(
                "INSERT INTO identifiers (id,object_id,source_id,scheme,value,normalized_value,"
                "assigning_body,confidence,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    new_id("identifier"), existing["object_id"], source_id,
                    identifier["scheme"], value, normalized,
                    identifier.get("assigning_body"), identifier.get("confidence", 1.0),
                    identifier.get("notes"),
                ),
            )
        for claim in record.get("claims", []):
            value_json = (
                json.dumps(claim.get("value_json"), ensure_ascii=False, sort_keys=True)
                if claim.get("value_json") is not None else None
            )
            locator = claim.get("locator", appearance["locator"])
            if corrected_claim_import(conn, existing["object_id"], existing["appearance_id"], source_id,
                                      claim["field"], claim.get("value_text"), value_json, locator):
                continue
            if conn.execute(
                "SELECT 1 FROM claims WHERE object_id=? AND appearance_id=? AND source_id=? "
                "AND field=? AND value_text IS ? AND value_json IS ? AND locator=?",
                (
                    existing["object_id"], existing["appearance_id"], source_id, claim["field"],
                    claim.get("value_text"), value_json, locator,
                ),
            ).fetchone():
                continue
            conn.execute(
                "INSERT INTO claims (id,object_id,appearance_id,source_id,field,value_text,value_json,"
                "normalized_value,certainty,locator,quotation,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    new_id("claim"), existing["object_id"], existing["appearance_id"], source_id,
                    claim["field"], claim.get("value_text"), value_json,
                    claim.get("normalized_value"), claim.get("certainty", "reported"), locator,
                    claim.get("quotation"), claim.get("notes"),
                ),
            )
        for item in record.get("texts", []):
            locator = item.get("locator", appearance["locator"])
            if not item.get('id') and previously_corrected_import(conn, existing["object_id"], existing["appearance_id"],
                                           source_id, item, locator):
                continue
            _append_reading(conn, existing["object_id"], existing["appearance_id"], source_id, item, locator)
        for event in record.get("events", []):
            locator = event.get("locator", appearance["locator"])
            if conn.execute(
                "SELECT 1 FROM events WHERE object_id=? AND source_id=? AND event_type=? "
                "AND start_date IS ? AND end_date IS ? AND place IS ? AND actor IS ? "
                "AND details=? AND locator=?",
                (
                    existing["object_id"], source_id, event["event_type"], event.get("start_date"),
                    event.get("end_date"), event.get("place"), event.get("actor"), event["details"],
                    locator,
                ),
            ).fetchone():
                continue
            conn.execute(
                "INSERT INTO events (id,object_id,source_id,event_type,start_date,end_date,place,actor,"
                "details,certainty,locator) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    new_id("event"), existing["object_id"], source_id, event["event_type"],
                    event.get("start_date"), event.get("end_date"), event.get("place"),
                    event.get("actor"), event["details"], event.get("certainty", "reported"), locator,
                ),
            )
        for media in record.get("media", []):
            _append_media(conn, existing["object_id"], existing["appearance_id"], source_id, media)
        return existing["object_id"]

    object_id = record.get("object_id") or new_id("object")
    object_exists = conn.execute("SELECT 1 FROM objects WHERE id=?", (object_id,)).fetchone()
    if not object_exists:
        conn.execute(
            "INSERT INTO objects (id,label,object_type,record_status,authenticity,summary) "
            "VALUES (?,?,?,?,?,?)",
            (
                object_id, record["label"], record.get("object_type", "whole_bowl"),
                record.get("record_status", "candidate"), record.get("authenticity", "unassessed"),
                record.get("summary"),
            ),
        )
    appearance_id = appearance.get("id") or new_id("appearance")
    appearance_stamp = None
    if appearance.get('created_at'):
        stamp = datetime.fromisoformat(appearance['created_at'].replace('Z', '+00:00'))
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError('Appearance creation timestamp must be UTC')
        appearance_stamp = stamp.strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "INSERT INTO appearances (id,source_id,locator,title,url,observed_at,description,raw_json,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP))",
        (
            appearance_id, source_id, appearance["locator"], appearance.get("title"),
            appearance.get("url"), appearance.get("observed_at"), appearance.get("description"),
            json.dumps(appearance.get("raw"), ensure_ascii=False, sort_keys=True)
            if appearance.get("raw") is not None else None,
            appearance_stamp,
        ),
    )
    conn.execute(
        "INSERT INTO appearance_object_links "
        "(appearance_id,object_id,relation_type,confidence,rationale,created_at) "
        "VALUES (?,?,?,?,?,COALESCE(?,CURRENT_TIMESTAMP))",
        (
            appearance_id, object_id, appearance.get("relation_type", "primary"),
            appearance.get("confidence", 1.0), appearance.get("rationale", "Source describes this candidate"),
            appearance_stamp,
        ),
    )

    for identifier in record.get("identifiers", []):
        value = identifier["value"]
        conn.execute(
            "INSERT INTO identifiers (id,object_id,appearance_id,source_id,scheme,value,normalized_value,"
            "assigning_body,confidence,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                new_id("identifier"), object_id, appearance_id, source_id, identifier["scheme"], value,
                identifier.get("normalized_value", normalize_identifier(identifier["scheme"], value)), identifier.get("assigning_body"),
                identifier.get("confidence", 1.0), identifier.get("notes"),
            ),
        )

    for claim in record.get("claims", []):
        conn.execute(
            "INSERT INTO claims (id,object_id,appearance_id,source_id,field,value_text,value_json,"
            "normalized_value,certainty,locator,quotation,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                new_id("claim"), object_id, appearance_id, source_id, claim["field"], claim.get("value_text"),
                json.dumps(claim.get("value_json"), ensure_ascii=False, sort_keys=True)
                if claim.get("value_json") is not None else None,
                claim.get("normalized_value"), claim.get("certainty", "reported"),
                claim.get("locator", appearance["locator"]), claim.get("quotation"), claim.get("notes"),
            ),
        )

    for text in record.get("texts", []):
        _append_reading(conn, object_id, appearance_id, source_id, text,
                        text.get("locator", appearance["locator"]))

    for event in record.get("events", []):
        conn.execute(
            "INSERT INTO events (id,object_id,source_id,event_type,start_date,end_date,place,actor,"
            "details,certainty,locator) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                new_id("event"), object_id, source_id, event["event_type"], event.get("start_date"),
                event.get("end_date"), event.get("place"), event.get("actor"), event["details"],
                event.get("certainty", "reported"), event.get("locator", appearance["locator"]),
            ),
        )

    for media in record.get("media", []):
        _append_media(conn, object_id, appearance_id, source_id, media)
    return object_id


def load_jsonl(conn, path, record_type):
    count = 0
    with conn:
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                record = json.loads(line)
                try:
                    if record_type == "source":
                        add_source(conn, record)
                    elif record_type == "candidate":
                        add_candidate(conn, record)
                    elif record_type == "lead":
                        add_lead(conn, record)
                    else:
                        raise ValueError("unsupported record type: %s" % record_type)
                except Exception as exc:
                    raise ValueError("%s:%s: %s" % (path, line_number, exc)) from exc
                count += 1
    return count


def load_compact_list(conn, path):
    """Ingest a checked scholarly list while preserving its item-level locators."""
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    source_id = add_source(conn, manifest["source"])
    entries = list(manifest.get("entries", []))
    for range_spec in manifest.get("ranges", []):
        for number in range(range_spec["start"], range_spec["end"] + 1):
            designation = (
                range_spec["format"].format(number=number)
                if range_spec.get("format")
                else "%03d%s" % (number, range_spec.get("suffix", ""))
            )
            canonical_key = None
            if range_spec.get("canonical_key_format"):
                canonical_key = range_spec["canonical_key_format"].format(
                    number=number, designation=designation
                )
            entries.append({
                "designation": designation,
                "canonical_key": canonical_key,
                "page": range_spec["section_pages"],
                "locator": "text %s; section pp. %s" % (designation, range_spec["section_pages"]),
                "record_status": range_spec.get("record_status", "probable"),
                "authenticity": range_spec.get("authenticity", "accepted"),
                "replace_default_claims": True,
                "claims": range_spec.get("claims", []),
                "notes": range_spec.get("notes"),
            })
    count = 0
    for entry in entries:
        identifiers = [{
            "scheme": "collection designation",
            "value": entry["designation"],
            "assigning_body": entry.get("collection"),
        }]
        if entry.get("list_number") is not None:
            identifiers.append({
                "scheme": manifest["list_number_scheme"],
                "value": str(entry["list_number"]),
                "assigning_body": manifest["source"].get("authors"),
            })
        canonical_key = entry.get("canonical_key")
        if canonical_key is None and manifest.get("canonical_key_prefix"):
            local_key = entry.get("list_number", entry["designation"])
            canonical_key = "%s::%s" % (manifest["canonical_key_prefix"], local_key)
        if canonical_key:
            identifiers.append({
                "scheme": "publication object key",
                "value": canonical_key,
                "assigning_body": manifest["source"].get("authors"),
            })
        identifiers.extend(
            {"scheme": "bibliographic concordance", "value": concordance}
            for concordance in entry.get("concordances", [])
        )
        identifiers.extend(entry.get("identifiers", []))
        claims = [] if entry.get("replace_default_claims") else [
            dict(claim) for claim in manifest.get("default_claims", [])
        ]
        claims.extend(dict(claim) for claim in entry.get("claims", []))
        if entry.get("collection"):
            claims.append({
                "field": "current_or_reported_collection",
                "value_text": entry["collection"],
                "certainty": "reported",
            })
        locator = entry.get("locator") or "p. %s%s" % (
                entry["page"],
                ", item %s" % entry["list_number"]
                if entry.get("list_number") is not None
                else ", designation %s" % entry["designation"],
        )
        for claim in claims:
            claim.setdefault("locator", locator)
        appearance_locator = locator
        locator_owner = conn.execute(
            "SELECT title FROM appearances WHERE source_id=? AND locator=?",
            (source_id, appearance_locator),
        ).fetchone()
        if locator_owner and locator_owner["title"] != entry["designation"]:
            appearance_locator = "%s; designation %s" % (locator, entry["designation"])
        record = {
            "label": entry.get("label") or entry["designation"],
            "object_type": entry.get("object_type", "whole_bowl"),
            "record_status": entry.get("record_status", "probable"),
            "authenticity": entry.get("authenticity", "accepted"),
            "summary": entry.get("notes") or manifest.get("summary"),
            "source_id": source_id,
            "appearance": {
                "locator": appearance_locator,
                "title": entry["designation"],
                "url": manifest["source"].get("url"),
                "description": entry.get("notes"),
            },
            "identifiers": identifiers,
            "claims": claims,
        }
        add_candidate(conn, record)
        count += 1
    for lead in manifest.get("leads", []):
        if conn.execute(
            "SELECT 1 FROM leads WHERE source_id=? AND description=?",
            (source_id, lead["description"]),
        ).fetchone():
            continue
        conn.execute(
            "INSERT INTO leads (id,source_id,lead_type,description,url,status,priority) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                new_id("lead"), source_id, lead.get("lead_type", "citation"), lead["description"],
                lead.get("url"), lead.get("status", "open"), lead.get("priority", 2),
            ),
        )
    conn.commit()
    return count
