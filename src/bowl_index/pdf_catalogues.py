import re
from pathlib import Path

from pypdf import PdfReader

from .db import PROJECT_ROOT
from .ids import new_id
from .ingest import add_candidate


WALLER_DOI = "10.11647/OBP.0305"

_ROW_NAMES = (
    r"Isbell \d{2}|AMB \d{2}[a-z]?|MSF\s+\d+|CAMIB \d+(?:\+\d+)*|"
    r"M \d+|VA \d+|JBA \d+|HS \d+|Aaron [BEF]|IM \d+|"
    r"MS (?:19\d{2}|2053)/\d+|S-\d+|T \d+|A33965|C10-116|De Menil|"
    r"JNF 124|MFL 10895|Moriah 2|SD 34|XI-t 5178|"
    r"Müller-Kessler 1994: B2|ZRL 48|Abousamra 2020|Ford/Ten-Ami 2012|"
    r"Herman 2021|Müller-Kessler 2013|Schwab 1891: 592|Shaked 2015: 109-110"
)
_ROW_RE = re.compile(r"^(%s)(?=\s|=)" % _ROW_NAMES)
_VERSE_RE = re.compile(
    r"\b(?:Gen|Exod|Lev|Num|Deut|1 Sam|2 Kgs|Isa|Jer|Ezek|Exek|Hos|Amos|Mic|"
    r"Zech|Ps|Prov|Song|Dan|Neh|1 Chron)\.?\s+\d+[.:]\d+(?:-\d+)?[a-z]?"
)


def _section_for_line(line, current):
    headings = (
        ("Isbell 1975 (", "Isbell 1975"),
        ("Naveh and Shaked 1985", "Naveh and Shaked 1985/1993"),
        ("Segal 2000 (", "Segal 2000"),
        ("Levene 2003 (", "Levene 2003"),
        ("Levene 2013 (", "Levene 2013"),
        ("Shaked, Ford, and Bhayro 2013", "Shaked, Ford, and Bhayro 2013"),
        ("Shaked, Ford, and Bhayro 2022", "Shaked, Ford, and Bhayro 2022"),
        ("Ford and Morgenstern 2020", "Ford and Morgenstern 2020"),
        ("Smaller Publications", "Smaller publications"),
    )
    for prefix, section in headings:
        if line.startswith(prefix):
            return section
    return current


def parse_waller_distribution(pdf_path):
    """Parse the verified distribution table on printed pages 153–162.

    The parser is intentionally bounded to this edition and validates the row
    count, so a changed PDF fails loudly instead of silently losing objects.
    """
    reader = PdfReader(str(pdf_path))
    rows = []
    current = None
    section = None
    for pdf_page in range(162, 172):
        text = reader.pages[pdf_page - 1].extract_text() or ""
        for raw_line in text.splitlines():
            line = " ".join(raw_line.split())
            next_section = _section_for_line(line, section)
            if next_section != section:
                if current:
                    rows.append(current)
                    current = None
                section = next_section
                continue
            match = _ROW_RE.match(line)
            if match:
                if current:
                    rows.append(current)
                current = {
                    "designation": " ".join(match.group(1).split()),
                    "section": section,
                    "page": pdf_page - 9,
                    "lines": [line],
                }
            elif current and not (
                re.match(r"^(?:\d+ )?(?:The Bible in the Bowls|Table of Distribution)", line)
                or line.startswith("© 2022")
            ):
                current["lines"].append(line)
    if current:
        rows.append(current)
    if len(rows) != 132:
        raise ValueError("expected 132 rows in Waller distribution table, found %s" % len(rows))
    for row in rows:
        row["text"] = " ".join(part for part in row.pop("lines") if part)
        row["quotations"] = list(dict.fromkeys(_VERSE_RE.findall(row["text"])))
    return rows


def _split_designations(designation):
    match = re.fullmatch(r"CAMIB (\d+)\+(\d+)\+(\d+)", designation)
    if match:
        return ["CAMIB " + value for value in match.groups()]
    return [designation]


def _canonical_identifiers(designation, section, row_text):
    identifiers = [{"scheme": "Waller 2022 table designation", "value": designation}]
    if designation.startswith("Isbell "):
        identifiers.append({"scheme": "publication object key", "value": "Isbell 1975::" + designation.split()[-1]})
    elif designation.startswith("AMB ") or designation.startswith("MSF "):
        identifiers.append({"scheme": "publication object key", "value": "Naveh-Shaked 1985/1993::" + designation})
    elif designation.startswith("CAMIB "):
        number = int(designation.split()[-1])
        identifiers.append({"scheme": "publication object key", "value": "Segal 2000::%03dA" % number})
    elif designation.startswith("JBA "):
        year = "2022" if section and "2022" in section else "2013"
        identifiers.append({"scheme": "publication object key", "value": "Shaked-Ford-Bhayro %s::JBA %s" % (year, int(designation.split()[-1]))})

    collection_prefixes = ("HS ", "IM ", "MS ", "S-", "T ", "VA ", "JNF ", "MFL ", "SD ", "XI-t ", "ZRL ", "A33965", "C10-")
    if designation.startswith(collection_prefixes):
        identifiers.append({"scheme": "collection designation", "value": designation})

    ait = re.search(r"= AIT (\d+)", row_text)
    if ait:
        identifiers.append({"scheme": "publication object key", "value": "Montgomery 1913::%s" % int(ait.group(1))})
    aliases = re.findall(r"=\s*((?:Gordon|HS|CAMIB|ZHS|SHM)\s*[A-Za-z0-9]+)", row_text)
    identifiers.extend({"scheme": "bibliographic concordance", "value": alias} for alias in aliases)
    if designation in ("Isbell 66", "CAMIB 26"):
        identifiers.append({"scheme": "collection designation", "value": "BM 91765", "notes": "Concordance stated in Waller table note 1."})
    if designation in ("Isbell 55", "HS 3005"):
        identifiers.append({"scheme": "collection designation", "value": "HS 3005", "notes": "Concordance stated in Waller table note 1."})
    return identifiers


def _reported_collection(designation, section):
    if designation.startswith("CAMIB ") or section == "Segal 2000":
        return "British Museum"
    if designation.startswith("VA "):
        return "Vorderasiatisches Museum, Berlin"
    if designation.startswith("HS "):
        return "Frau Professor Hilprecht Collection, Jena"
    if designation.startswith("IM "):
        return "Iraq Museum"
    if designation.startswith("JBA ") or designation.startswith("MS "):
        return "The Schøyen Collection"
    if section == "Levene 2003" or designation.startswith("M "):
        return "Moussaieff Collection"
    return None


def collect_waller(conn, archive_root=None):
    source = conn.execute("SELECT * FROM sources WHERE lower(doi)=lower(?)", (WALLER_DOI,)).fetchone()
    if not source:
        raise ValueError("Waller 2022 source record is missing")
    capture = conn.execute(
        "SELECT * FROM captures WHERE source_id=? AND mime_type='application/pdf' ORDER BY retrieved_at DESC LIMIT 1",
        (source["id"],),
    ).fetchone()
    if not capture:
        raise ValueError("archived Waller 2022 PDF is missing")
    root = Path(archive_root or PROJECT_ROOT / "data" / "private" / "archive")
    rows = parse_waller_distribution(root / capture["storage_path"])
    inserted = 0
    appearances = 0
    for row in rows:
        for designation in _split_designations(row["designation"]):
            locator = "p. %s, distribution table, %s" % (row["page"], designation)
            collection = _reported_collection(designation, row["section"])
            claims = [
                {"field": "inscription_language", "value_text": "Jewish Babylonian Aramaic", "locator": locator},
                {"field": "biblical_quotations", "value_json": row["quotations"], "locator": locator},
            ]
            if collection:
                claims.append({"field": "current_or_reported_collection", "value_text": collection, "locator": locator})
            record = {
                "label": "Waller 2022: %s" % designation,
                "record_status": "probable", "authenticity": "accepted",
                "summary": "Published JBA bowl listed with biblical quotation evidence.",
                "source_id": source["id"],
                "appearance": {
                    "locator": locator, "title": designation, "url": source["url"],
                    "description": row["text"],
                },
                "identifiers": _canonical_identifiers(designation, row["section"], row["text"]),
                "claims": claims,
                "texts": [{
                    "text_type": "summary", "language": "English",
                    "content": "Biblical quotations: %s" % (", ".join(row["quotations"]) or "see table row"),
                    "editor": "Daniel James Waller", "locator": locator,
                    "rights_status": "open_license", "public_ok": False,
                    "notes": "CC BY-NC 4.0; retain as non-public pending dashboard rights-policy review.",
                }],
            }
            before = conn.total_changes
            add_candidate(conn, record)
            inserted += int(conn.total_changes > before)
            appearances += 1
    conn.execute(
        "UPDATE coverage_targets SET status='in_progress',"
        "first_searched_at=coalesce(first_searched_at,CURRENT_TIMESTAMP),"
        "last_searched_at=CURRENT_TIMESTAMP,notes=? WHERE source_class='scholarship'",
        ("Parsed all 132 table rows (134 object designations after splitting a three-bowl combined row) in Waller 2022.",),
    )
    conn.commit()
    return {"table_rows": len(rows), "object_designations": appearances, "inserted_or_enriched": inserted}
