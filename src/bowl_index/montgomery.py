"""Checked ingestion of Montgomery's public-domain 1913 bowl edition."""

import hashlib
import json
import re
from bisect import bisect_right
from pathlib import Path

from pypdf import PdfReader

from .ids import new_id
from .ingest import add_lead, normalize_identifier
from .review import apply_dedupe_review


HEADING_RE = re.compile(r"(?m)^No\.\s+(\d+)\s+\(CBS\s+([^)]+)\)\s*$")
TRANSLATION_RE = re.compile(
    r"(?im)^\s*Translation(?:\s+(?:of|ot)\s+No\.\s*(\d+))?\s*$"
)
COMMENTARY_RE = re.compile(r"(?im)^\s*Commentary\s*$")
HEADER_RE = re.compile(
    r"^\s*(?:(?:[0-9iIl]{1,3})\s+)?(?:UNIVERSITY MUSEUM\.\s*BABY[EL]ONIAN SECTION\.?|"
    r"J\.\s*A\.\s*MONTGOMERY[—-]ARAMAIC INCANTATION TEXTS\.)\s*\d{0,3}\s*$",
    re.IGNORECASE,
)
PAGE_NUMBER_RE = re.compile(r"^\s*\(\s*\d{1,3}\s*\)\s*$")


def _clean_translation(text):
    """Remove scan furniture while retaining the OCR's diplomatic lineation."""
    lines = []
    for line in text.replace("\u00ad", "").splitlines():
        line = " ".join(line.split())
        if HEADER_RE.match(line) or PAGE_NUMBER_RE.match(line):
            while lines and not lines[-1]:
                lines.pop()
            continue
        lines.append(line)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    cleaned = []
    for line in lines:
        if not line and (not cleaned or not cleaned[-1]):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_translation_sections(page_texts):
    """Extract translation blocks from ``[(physical_page, text), ...]``.

    Montgomery prints the translations after the transcriptions and before a
    Commentary heading. Texts 21–23 are a special case: the shared block is
    printed after text 23 and explicitly labelled as the translation of no. 22.
    """
    combined = ""
    page_offsets = []
    for page_number, page_text in page_texts:
        page_offsets.append((len(combined), page_number))
        combined += (page_text or "") + "\n"
    offsets = [item[0] for item in page_offsets]

    def page_at(offset):
        return page_offsets[max(0, bisect_right(offsets, offset) - 1)][1]

    headings = [
        match for match in HEADING_RE.finditer(combined)
        if 1 <= int(match.group(1)) <= 40
    ]
    if {int(match.group(1)) for match in headings} != set(range(1, 41)):
        found = sorted({int(match.group(1)) for match in headings})
        raise ValueError("expected Montgomery headings 1-40; found %s" % found)

    translations = {}
    for index, heading in enumerate(headings):
        section_end = headings[index + 1].start() if index + 1 < len(headings) else len(combined)
        section = combined[heading.end():section_end]
        translation = TRANSLATION_RE.search(section)
        if not translation:
            continue
        after_translation = section[translation.end():]
        commentary = COMMENTARY_RE.search(after_translation)
        if not commentary:
            raise ValueError("translation for text %s has no Commentary boundary" % heading.group(1))
        explicit_number = translation.group(1)
        text_number = int(explicit_number or heading.group(1))
        content_start = heading.end() + translation.end()
        content_end = content_start + commentary.start()
        content = _clean_translation(combined[content_start:content_end])
        if not content:
            raise ValueError("empty translation for Montgomery text %s" % text_number)
        if text_number in translations:
            raise ValueError("duplicate translation for Montgomery text %s" % text_number)
        start_page = page_at(content_start)
        end_page = page_at(max(content_start, content_end - 1))
        translations[text_number] = {
            "text_number": text_number,
            "content": content,
            "pdf_page_start": start_page,
            "pdf_page_end": end_page,
            "printed_page_start": start_page - 6,
            "printed_page_end": end_page - 6,
        }
    return translations


def parse_montgomery_pdf(pdf_path, first_page=123, last_page=264):
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) < last_page:
        raise ValueError("Montgomery PDF has only %s pages" % len(reader.pages))
    pages = [
        (page_number, reader.pages[page_number - 1].extract_text() or "")
        for page_number in range(first_page, last_page + 1)
    ]
    return extract_translation_sections(pages)


def _object_for_publication_key(conn, value, source_id=None):
    sql = (
        "SELECT DISTINCT i.object_id FROM identifiers i WHERE i.scheme='publication object key' "
        "AND i.normalized_value=? AND i.object_id IS NOT NULL"
    )
    params = [normalize_identifier("publication object key", value)]
    if source_id:
        sql += (
            " AND EXISTS (SELECT 1 FROM appearance_object_links l JOIN appearances a "
            "ON a.id=l.appearance_id WHERE l.object_id=i.object_id AND a.source_id=? "
            "AND l.relation_type<>'rejected')"
        )
        params.append(source_id)
    rows = conn.execute(sql, params).fetchall()
    if len(rows) != 1:
        raise ValueError("expected one object for %s; found %s" % (value, len(rows)))
    return rows[0]["object_id"]


def _add_claim(conn, source_id, object_id, appearance_id, claim):
    value_json = (
        json.dumps(claim.get("value_json"), ensure_ascii=False, sort_keys=True)
        if claim.get("value_json") is not None else None
    )
    if conn.execute(
        "SELECT 1 FROM claims WHERE object_id=? AND source_id=? AND field=? "
        "AND value_text IS ? AND value_json IS ? AND locator=?",
        (
            object_id, claim.get("source_id", source_id), claim["field"],
            claim.get("value_text"), value_json, claim["locator"],
        ),
    ).fetchone():
        return False
    conn.execute(
        "INSERT INTO claims (id,object_id,appearance_id,source_id,field,value_text,value_json,"
        "normalized_value,certainty,locator,quotation,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            new_id("claim"), object_id, appearance_id, claim.get("source_id", source_id),
            claim["field"], claim.get("value_text"), value_json,
            claim.get("normalized_value"), claim.get("certainty", "reported"),
            claim["locator"], claim.get("quotation"), claim.get("notes"),
        ),
    )
    return True


def _add_identifier(conn, source_id, object_id, appearance_id, identifier):
    normalized = normalize_identifier(identifier["scheme"], identifier["value"])
    if conn.execute(
        "SELECT 1 FROM identifiers WHERE object_id=? AND source_id=? AND scheme=? "
        "AND normalized_value=?",
        (object_id, source_id, identifier["scheme"], normalized),
    ).fetchone():
        return False
    conn.execute(
        "INSERT INTO identifiers (id,object_id,appearance_id,source_id,scheme,value,"
        "normalized_value,assigning_body,confidence,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            new_id("identifier"), object_id, appearance_id, source_id,
            identifier["scheme"], identifier["value"], normalized,
            identifier.get("assigning_body"), identifier.get("confidence", 1.0),
            identifier.get("notes"),
        ),
    )
    return True


def _ensure_dedupe_candidate(conn, review):
    object_a_id, object_b_id = sorted((review["object_a_id"], review["object_b_id"]))
    row = conn.execute(
        "SELECT id FROM dedupe_candidates WHERE object_a_id=? AND object_b_id=?",
        (object_a_id, object_b_id),
    ).fetchone()
    if row:
        return row["id"]
    dedupe_id = new_id("dedupe")
    conn.execute(
        "INSERT INTO dedupe_candidates (id,object_a_id,object_b_id,score,status,method,rationale) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            dedupe_id, object_a_id, object_b_id, review.get("score", 0.95), "pending",
            review.get("method", "checked_concordance"), review["rationale"],
        ),
    )
    return dedupe_id


def _object_from_review_selector(conn, item, side, montgomery_source_id):
    object_id = item.get(side + "_id")
    if object_id:
        if not conn.execute("SELECT 1 FROM objects WHERE id=?", (object_id,)).fetchone():
            raise ValueError("review object does not exist: %s" % object_id)
        return object_id
    publication_key = item.get(side + "_publication_key")
    if publication_key:
        return _object_for_publication_key(conn, publication_key, montgomery_source_id)
    identifier = item.get(side + "_identifier")
    if identifier:
        rows = conn.execute(
            "SELECT DISTINCT object_id FROM identifiers WHERE scheme=? AND normalized_value=? "
            "AND object_id IS NOT NULL",
            (
                identifier["scheme"],
                normalize_identifier(identifier["scheme"], identifier["value"]),
            ),
        ).fetchall()
        if len(rows) != 1:
            raise ValueError(
                "expected one object for %s selector %s; found %s"
                % (side, identifier, len(rows))
            )
        return rows[0]["object_id"]
    raise ValueError("review is missing a selector for %s" % side)


def apply_montgomery_review(conn, review, translations):
    source_id = review.get("source_id")
    source = conn.execute("SELECT id FROM sources WHERE id=?", (source_id,)).fetchone()
    if not source and review.get("source_url"):
        source = conn.execute(
            "SELECT id FROM sources WHERE url=?", (review["source_url"],)
        ).fetchone()
    if not source:
        raise ValueError("Montgomery source is not present")
    source_id = source["id"]
    stats = {"translations": 0, "claims": 0, "identifiers": 0, "dedupe_reviews": 0}

    expected = set(review["translation_text_numbers"])
    if set(translations) != expected:
        raise ValueError(
            "translation set differs from checked manifest: expected %s, found %s"
            % (sorted(expected), sorted(translations))
        )

    for text_number, translation in sorted(translations.items()):
        object_id = _object_for_publication_key(
            conn, "Montgomery 1913::%s" % text_number, source_id
        )
        appearance = conn.execute(
            "SELECT a.id FROM appearances a JOIN appearance_object_links l "
            "ON l.appearance_id=a.id WHERE l.object_id=? AND a.source_id=? "
            "AND l.relation_type<>'rejected' ORDER BY a.id LIMIT 1",
            (object_id, source_id),
        ).fetchone()
        if not appearance:
            raise ValueError("no Montgomery appearance for text %s" % text_number)
        start = translation["printed_page_start"]
        end = translation["printed_page_end"]
        printed = str(start) if start == end else "%s-%s" % (start, end)
        pdf_start = translation["pdf_page_start"]
        pdf_end = translation["pdf_page_end"]
        pdf_pages = str(pdf_start) if pdf_start == pdf_end else "%s-%s" % (pdf_start, pdf_end)
        locator = "text %s translation, printed pp. %s; PDF pp. %s" % (
            text_number, printed, pdf_pages,
        )
        existing = conn.execute(
            "SELECT id FROM texts WHERE object_id=? AND source_id=? AND text_type='translation' "
            "AND editor='James A. Montgomery'",
            (object_id, source_id),
        ).fetchone()
        values = (
            translation["content"], locator, "public_domain", 0,
            "English translation extracted from the edition's embedded OCR. Public-domain source; "
            "held from public export until line-by-line proofreading against the scan.",
        )
        if existing:
            if conn.execute("SELECT 1 FROM text_proofreading_reviews WHERE text_id=? LIMIT 1",
                            (existing["id"],)).fetchone():
                # Importing OCR is never authority to replace a reviewed reading text.
                continue
            conn.execute(
                "UPDATE texts SET content=?,locator=?,rights_status=?,public_ok=?,notes=? WHERE id=?",
                values + (existing["id"],),
            )
        else:
            conn.execute(
                "INSERT INTO texts (id,object_id,appearance_id,source_id,text_type,language,content,"
                "editor,locator,rights_status,public_ok,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    new_id("text"), object_id, appearance["id"], source_id, "translation",
                    "English", translation["content"], "James A. Montgomery", locator,
                    "public_domain", 0, values[-1],
                ),
            )
            stats["translations"] += 1

    for correction in review.get("corrections", []):
        object_id = _object_for_publication_key(
            conn, correction["publication_key"], source_id
        )
        appearance = conn.execute(
            "SELECT a.id FROM appearances a JOIN appearance_object_links l ON l.appearance_id=a.id "
            "WHERE l.object_id=? AND a.source_id=? ORDER BY a.id LIMIT 1",
            (object_id, source_id),
        ).fetchone()
        appearance_id = appearance["id"] if appearance else None
        for identifier in correction.get("remove_identifiers", []):
            conn.execute(
                "DELETE FROM identifiers WHERE object_id=? AND source_id=? AND scheme=? "
                "AND normalized_value=?",
                (
                    object_id, source_id, identifier["scheme"],
                    normalize_identifier(identifier["scheme"], identifier["value"]),
                ),
            )
        for identifier in correction.get("add_identifiers", []):
            stats["identifiers"] += int(_add_identifier(
                conn, source_id, object_id, appearance_id, identifier
            ))
        for claim in correction.get("claims", []):
            stats["claims"] += int(_add_claim(
                conn, source_id, object_id, appearance_id, claim
            ))
        if correction.get("label"):
            conn.execute(
                "UPDATE objects SET label=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (correction["label"], object_id),
            )

    for item in review.get("dedupe_reviews", []):
        resolved = dict(item)
        resolved["object_a_id"] = _object_from_review_selector(
            conn, item, "object_a", source_id
        )
        resolved["object_b_id"] = _object_from_review_selector(
            conn, item, "object_b", source_id
        )
        resolved["evidence"] = []
        for evidence in item.get("evidence", []):
            evidence = dict(evidence)
            if evidence.get("source_url"):
                evidence_source = conn.execute(
                    "SELECT id FROM sources WHERE url=?", (evidence.pop("source_url"),)
                ).fetchone()
                if not evidence_source:
                    raise ValueError("evidence source URL is not present")
                evidence["source_id"] = evidence_source["id"]
            resolved["evidence"].append(evidence)
        resolved["dedupe_id"] = _ensure_dedupe_candidate(conn, resolved)
        apply_dedupe_review(conn, resolved)
        stats["dedupe_reviews"] += 1

    if review.get("lead_update"):
        add_lead(conn, review["lead_update"])
    return stats


def ingest_montgomery_review(conn, pdf_path, review_path):
    pdf_path = Path(pdf_path)
    review = json.loads(Path(review_path).read_text(encoding="utf-8"))
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    if digest != review["pdf_sha256"]:
        raise ValueError("Montgomery PDF hash does not match checked review manifest")
    try:
        translations = parse_montgomery_pdf(pdf_path)
        stats = apply_montgomery_review(conn, review, translations)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    stats["translation_blocks_found"] = len(translations)
    stats["withheld_pending_proofreading"] = len(translations)
    return stats
