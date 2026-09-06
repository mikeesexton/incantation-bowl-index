"""An index of the literature, not of the bowls.

Three things this has to do honestly. Scope is a reading judgment, not a format,
so it is derived only where the publication registry can settle it and recorded
as a decision otherwise. Contributors need author names grouped, which is the
object-identity problem one level up — a wrong merge misattributes a scholar's
work, so grouping is conservative and every multi-spelling group is reported for
checking. And growth over time is shown against the field's own control list, so
the gap between what was published and what this index holds stays visible.
"""

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from .db import PROJECT_ROOT
from .publications import current_registry, publication_keys

SCHOLARSHIP_TYPES = ("book", "article", "chapter", "thesis", "catalogue", "excavation_report")

SCOPES = ("single_object_edition", "corpus_edition", "catalogue", "thematic_study", "synthesis",
          "linguistic_study", "provenance_ethics", "excavation_report", "not_scholarship")

SCOPE_LABELS = {
    "single_object_edition": "Edition of one bowl",
    "corpus_edition": "Edition of many bowls",
    "catalogue": "Collection catalogue",
    "thematic_study": "Thematic study",
    "synthesis": "Survey or synthesis",
    "linguistic_study": "Language study",
    "provenance_ethics": "Provenance and ethics",
    "excavation_report": "Excavation report",
    "not_scholarship": "Not scholarship",
}

WALLER_LIST = PROJECT_ROOT / "research" / "sources" / "waller_2025_jba_publication_list.jsonl"

_CORPORATE = re.compile(
    r"\b(museum|library|collection|university|universit|institute|arts|studies|centre|center|"
    r"society|press|gallery|auction|house|christie|sotheby|bonhams|department|project)\b", re.I)
_SECONDARY = re.compile(
    r",?\s*with\s+(?:a\s+)?(?:contribution|contributions|assistance)\s+(?:by|of)\s+", re.I)
_TRAILING_ROLE = re.compile(r",?\s*\b(?:eds?|editors?|trans|translators?)\.?\s*$", re.I)
# The SCHOL-002 ingest wrote "Surname [and others; see citation]" wherever Waller's
# list used the em-dash repeat convention. Left alone it invents an author called
# "see citation]" and, worse, keys every such name on the surname "others" — which
# merged Geller with Gordon and Schwab with Shaked. The verbatim citation carries
# the real author list; this strips the placeholder.
_PLACEHOLDER = re.compile(r"\s*\[.*$")
_DROP = re.compile(r"see\s+citation|and\s+others", re.I)


def _fold(value):
    return unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold()


def split_authors(value):
    """One free-text author field into individual names.

    Handles the three shapes the corpus actually contains: semicolon lists,
    "Surname, Given, and Given Surname", and "X, with a contribution by Y".
    """
    if not value or not value.strip():
        return []
    text = _TRAILING_ROLE.sub("", value.strip())
    text = _SECONDARY.sub("; ", text)
    parts = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        # "Babelon, Ernest, and Moïse Schwab" — the inverted first name keeps its
        # comma, so only split on a conjunction, never on the inversion comma.
        for piece in re.split(r",\s+and\s+|\s+and\s+|\s*&\s*", chunk):
            piece = _PLACEHOLDER.sub("", piece)
            piece = re.sub(r"^and\s+", "", piece.strip(" ,.]"), flags=re.I).strip(" ,.")
            if not piece or _DROP.search(piece) or _fold(piece) in {"colleagues", "others", "et al"}:
                continue
            parts.append(piece)
    return parts


def contributor_key(name):
    """Group spellings of one person, conservatively.

    Surname plus first initial, which merges "Ford, James Nathan",
    "James Nathan Ford" and "Ford, J. N." A corporate author keys on its whole
    name. Two scholars sharing a surname and initial would merge wrongly, which
    is why `contributor_groups` reports every group with more than one spelling.
    """
    cleaned = _TRAILING_ROLE.sub("", (name or "").strip())
    if not cleaned:
        return ""
    if _CORPORATE.search(cleaned):
        return _fold(cleaned)
    if " " not in cleaned and "," not in cleaned:
        # A bare surname, usually left by stripping an "[and others]" placeholder.
        # It keys with no initial and is folded into a full name later, but only
        # when exactly one scholar of that surname exists.
        return "%s," % _fold(cleaned).strip()
    if "," in cleaned:
        surname, _, given = cleaned.partition(",")
    else:
        tokens = cleaned.split()
        surname, given = tokens[-1], " ".join(tokens[:-1])
    surname = _fold(surname).strip()
    initial = next((ch for ch in _fold(given) if ch.isalpha()), "")
    return "%s,%s" % (surname, initial) if surname else _fold(cleaned)


def _alias_overrides(conn):
    rows = {}
    try:
        for row in conn.execute("SELECT * FROM contributor_aliases ORDER BY rowid"):
            rows[row["alias"]] = dict(row)
    except Exception:
        return {}
    return rows


def derived_scope(conn, source):
    """Scope where the data can settle it; None where it is a reading judgment."""
    if source["source_type"] not in SCHOLARSHIP_TYPES:
        return "not_scholarship"
    if source["source_type"] == "excavation_report":
        return "excavation_report"
    counts = publication_object_counts_by_source(conn)
    published = counts.get(source["id"], 0)
    if published == 1:
        return "single_object_edition"
    if published > 1:
        return "corpus_edition" if source["source_type"] != "catalogue" else "catalogue"
    if source["source_type"] == "catalogue":
        return "catalogue"
    return None


def publication_object_counts_by_source(conn):
    keys, registry = publication_keys(conn), current_registry(conn)
    counts = {}
    for key, entry in registry.items():
        if entry["resolution"] == "resolved" and entry["source_id"]:
            counts[entry["source_id"]] = counts.get(entry["source_id"], 0) + keys.get(key, 0)
    return counts


def current_scopes(conn):
    rows = {}
    try:
        for row in conn.execute("SELECT * FROM source_scope_reviews ORDER BY rowid"):
            rows[row["source_id"]] = dict(row)
    except Exception:
        return {}
    return rows


def works(conn):
    """Every scholarship record, with its scope, holdings and object count."""
    held = {row[0] for row in conn.execute(
        "SELECT DISTINCT source_id FROM captures WHERE source_id IS NOT NULL")}
    counts = publication_object_counts_by_source(conn)
    reviewed = current_scopes(conn)
    rows = []
    for source in conn.execute(
        "SELECT id,source_type,title,authors,issued_year,container_title,doi,citation,"
        "access_status FROM sources ORDER BY coalesce(issued_year,0) DESC, title"
    ):
        source = dict(source)
        if source["source_type"] not in SCHOLARSHIP_TYPES:
            continue
        decision = reviewed.get(source["id"])
        scope = decision["scope"] if decision else derived_scope(conn, source)
        rows.append({
            "source_id": source["id"], "title": source["title"],
            "authors": source["authors"], "issued_year": source["issued_year"],
            "container_title": source["container_title"], "citation": source["citation"],
            "doi": source["doi"], "source_type": source["source_type"],
            "access_status": source["access_status"],
            "scope": scope, "scope_basis": "reviewed" if decision else ("derived" if scope else "unclassified"),
            "objects_published": counts.get(source["id"], 0),
            "document_held": source["id"] in held,
        })
    return rows


def contributor_groups(conn, work_rows=None):
    """Contributors ranked by publications, with every spelling kept visible."""
    rows = work_rows if work_rows is not None else works(conn)
    overrides = _alias_overrides(conn)
    people = {}
    for work in rows:
        for name in split_authors(work["authors"]):
            override = overrides.get(name)
            key = override["contributor_key"] if override else contributor_key(name)
            if not key:
                continue
            person = people.setdefault(key, {
                "contributor_key": key, "display_name": (override or {}).get("display_name") or name,
                "spellings": set(), "works": 0, "objects_published": 0,
                "first_year": None, "last_year": None, "source_ids": [],
            })
            person["spellings"].add(name)
            person["works"] += 1
            person["objects_published"] += work["objects_published"]
            person["source_ids"].append(work["source_id"])
            year = work["issued_year"]
            if year:
                person["first_year"] = min(person["first_year"] or year, year)
                person["last_year"] = max(person["last_year"] or year, year)
            # Prefer the longest spelling as the display form: "James Nathan Ford"
            # over "J. N. Ford", unless a reviewer has named one.
            if not (override or {}).get("display_name"):
                current = person["display_name"]
                # "Christa Müller-Kessler" reads better than "Müller-Kessler, Christa";
                # otherwise prefer the fullest spelling over an initialism.
                better = ("," in current and "," not in name) or (
                    ("," in current) == ("," not in name and "," not in current)
                    and len(name) > len(current) and ("," in name) == ("," in current))
                if better:
                    person["display_name"] = name
    people = _absorb_bare_surnames(people)
    for person in people.values():
        person["spellings"] = sorted(person["spellings"])
        person["needs_check"] = len(person["spellings"]) > 1
    return sorted(people.values(),
                  key=lambda p: (-p["works"], -p["objects_published"], p["display_name"]))


def _absorb_bare_surnames(people):
    """Fold "Levene" into "Dan Levene" — but never when it would be a guess.

    A surname with no initial belongs to a named scholar only if exactly one
    scholar of that surname is present. Two Fords and the bare name stays its own
    entry, visibly under-attributed rather than silently attributed to the wrong
    person.
    """
    by_surname = {}
    for key in people:
        surname, _, initial = key.partition(",")
        if initial:
            by_surname.setdefault(surname, []).append(key)
    for key in [k for k in people if k.endswith(",")]:
        candidates = by_surname.get(key[:-1], [])
        if len(candidates) != 1:
            continue
        target, source = people[candidates[0]], people.pop(key)
        target["spellings"] |= source["spellings"]
        target["works"] += source["works"]
        target["objects_published"] += source["objects_published"]
        target["source_ids"] += source["source_ids"]
        for bound, pick in (("first_year", min), ("last_year", max)):
            years = [y for y in (target[bound], source[bound]) if y]
            target[bound] = pick(years) if years else None
    return people


def waller_series():
    """The field's own publication curve, for comparison with ours."""
    if not WALLER_LIST.exists():
        return {}
    counts = {}
    for line in WALLER_LIST.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        year = json.loads(line).get("issued_year")
        if year:
            counts[year // 10 * 10] = counts.get(year // 10 * 10, 0) + 1
    return counts


def decade_series(conn, work_rows=None):
    """Two lines: what the field published, and what this index holds."""
    rows = work_rows if work_rows is not None else works(conn)
    ours = {}
    for work in rows:
        if work["issued_year"]:
            decade = work["issued_year"] // 10 * 10
            ours[decade] = ours.get(decade, 0) + 1
    field = waller_series()
    decades = sorted(set(ours) | set(field))
    return [{"decade": d, "held": ours.get(d, 0), "field_control_list": field.get(d, 0)}
            for d in decades]


def scholarship_metrics(conn):
    rows = works(conn)
    return {
        "works": len(rows),
        "works_with_a_held_document": sum(1 for r in rows if r["document_held"]),
        "works_with_a_scope": sum(1 for r in rows if r["scope"]),
        "works_awaiting_scope": sum(1 for r in rows if not r["scope"]),
        "contributors": len(contributor_groups(conn, rows)),
        "contributors_needing_a_spelling_check": sum(
            1 for c in contributor_groups(conn, rows) if c["needs_check"]),
    }


def apply_scope_batch(conn, manifest):
    if manifest.get("schema_version") != 1 or not manifest.get("entries"):
        raise ValueError("A version 1 scope batch with entries is required")
    stamp = datetime.fromisoformat(manifest["reviewed_at"].replace("Z", "+00:00"))
    reviewer = (manifest.get("reviewed_by") or "").strip()
    if not reviewer or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("Named reviewer and UTC timestamp required")
    changed = 0
    with conn:
        if not conn.in_transaction:
            conn.execute("BEGIN IMMEDIATE")
        seen = set()
        for entry in manifest["entries"]:
            source_id = entry["source_id"]
            if source_id in seen:
                raise ValueError("Duplicate source in batch: %s" % source_id)
            seen.add(source_id)
            if entry["scope"] not in SCOPES:
                raise ValueError("Invalid scope for %s" % source_id)
            if not (entry.get("basis") or "").strip():
                raise ValueError("Every scope decision needs a basis: %s" % source_id)
            if not conn.execute("SELECT 1 FROM sources WHERE id=?", (source_id,)).fetchone():
                raise ValueError("No such source: %s" % source_id)
            values = (entry["review_id"], source_id, entry["scope"], entry["basis"],
                      reviewer, stamp.isoformat(timespec="seconds"))
            old = conn.execute(
                "SELECT * FROM source_scope_reviews WHERE id=?", (entry["review_id"],)).fetchone()
            if old:
                if tuple(old) != values:
                    raise ValueError("Scope review ID reused with a changed decision")
                continue
            conn.execute("INSERT INTO source_scope_reviews VALUES (?,?,?,?,?,?)", values)
            changed += 1
    return {"entries": len(manifest["entries"]), "changed": changed, **scholarship_metrics(conn)}
