import json
import html
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from .ingest import add_candidate
from .ids import new_id


MET_API = "https://collectionapi.metmuseum.org/public/collection/v1"
NLI_SRU = "https://nli.alma.exlibrisgroup.com/view/sru/972NNL_INST"


def normalize_penn_identifier(value):
    if re.fullmatch(r"B\d+", value, re.IGNORECASE):
        return "cbs " + value[1:].lstrip("0")
    return value.strip().casefold()


def _get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "IncantationBowlIndexResearch/0.1 (+noncommercial scholarly corpus)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_met(conn):
    query_url = MET_API + "/search?" + urllib.parse.urlencode({"q": "incantation bowl"})
    result = _get_json(query_url)
    inserted = 0
    skipped = 0
    for object_id in result.get("objectIDs") or []:
        item = _get_json(MET_API + "/objects/%s" % object_id)
        title = item.get("title") or ""
        if "incantation bowl" not in title.casefold():
            skipped += 1
            continue
        object_url = item.get("objectURL") or "https://www.metmuseum.org/art/collection/search/%s" % object_id
        claims = []
        for field, api_field in (
            ("dating", "objectDate"), ("period", "period"), ("culture", "culture"),
            ("material", "medium"), ("dimensions", "dimensions"), ("provenance_summary", "creditLine"),
            ("current_location", "repository"),
        ):
            if item.get(api_field):
                claims.append({"field": field, "value_text": item[api_field], "locator": object_url})
        geography = ", ".join(
            value for value in (item.get("country"), item.get("region"), item.get("city")) if value
        )
        if geography:
            claims.append({"field": "geography", "value_text": geography, "locator": object_url})
        language = None
        if "pseudo-aramaic" in title.casefold():
            language = "Pseudo-Aramaic"
        elif "mandaic" in title.casefold():
            language = "Mandaic"
        elif "aramaic" in title.casefold():
            language = "Aramaic"
        if language:
            claims.append({"field": "inscription_language", "value_text": language, "locator": object_url})
        record = {
            "label": "Met %s: %s" % (item.get("accessionNumber"), title),
            "record_status": "probable",
            "authenticity": "pseudo_script" if "pseudo" in title.casefold() else "accepted",
            "summary": title,
            "source": {
                "source_type": "museum_record",
                "title": title,
                "publisher": "The Metropolitan Museum of Art",
                "url": object_url,
                "citation": "The Metropolitan Museum of Art, object %s (%s)" % (
                    item.get("accessionNumber"), object_url
                ),
                "access_status": "available",
                "rights_status": "public_domain" if item.get("isPublicDomain") else "copyrighted",
            },
            "appearance": {
                "locator": "Met object %s" % object_id,
                "title": title,
                "url": object_url,
                "description": item.get("objectName"),
                "raw": item,
            },
            "identifiers": [
                {"scheme": "Met object ID", "value": str(object_id), "assigning_body": "The Metropolitan Museum of Art"},
                {"scheme": "accession number", "value": item.get("accessionNumber"), "assigning_body": "The Metropolitan Museum of Art"},
            ],
            "claims": claims,
            "media": ([{
                "media_type": "image", "url": item.get("primaryImage"),
                "rights_status": "public_domain" if item.get("isPublicDomain") else "copyrighted",
            }] if item.get("primaryImage") else []),
        }
        before = conn.total_changes
        add_candidate(conn, record)
        inserted += int(conn.total_changes > before)
    conn.commit()
    return {"inserted": inserted, "skipped_non_bowls": skipped, "api_results": len(result.get("objectIDs") or [])}


def _get_text(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "IncantationBowlIndexResearch/0.1 (+noncommercial scholarly corpus)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


MARC_NS = {"m": "http://www.loc.gov/MARC21/slim"}
SRU_NS = {"s": "http://www.loc.gov/zing/srw/", **MARC_NS}


def _marc_fields(record, tag):
    """Return MARC data fields as ``{code: [values]}`` dictionaries."""
    result = []
    for field in record.findall("./m:datafield[@tag='%s']" % tag, MARC_NS):
        values = {}
        for subfield in field.findall("./m:subfield", MARC_NS):
            values.setdefault(subfield.get("code"), []).append(subfield.text or "")
        result.append(values)
    return result


def _marc_first(record, tag, code="a"):
    fields = _marc_fields(record, tag)
    return fields[0].get(code, [None])[0] if fields else None


def _parse_nli_sru(xml_bytes):
    """Parse the bowl records from one NLI Alma SRU response page."""
    root = ET.fromstring(xml_bytes)
    total = int(root.findtext("./s:numberOfRecords", default="0", namespaces=SRU_NS))
    bowls = []
    for record in root.findall(".//m:record", SRU_NS):
        title = _marc_first(record, "245") or ""
        match = re.match(r"^קערת השבעה מס['׳]?\s*(\d+)", title)
        if not match:
            continue
        mms_id = record.findtext("./m:controlfield[@tag='001']", default="", namespaces=MARC_NS)
        shelfmark = _marc_first(record, "090")
        dimensions = _marc_first(record, "340")
        languages = []
        for field in _marc_fields(record, "041"):
            languages.extend(field.get("a", []))
        public_domain = any(
            "public domain" in value.casefold()
            for tag in ("903", "939")
            for field in _marc_fields(record, tag)
            for values in field.values()
            for value in values
        )
        bowls.append({
            "number": int(match.group(1)),
            "title": title.rstrip(". "),
            "mms_id": mms_id,
            "shelfmark": shelfmark,
            "dimensions_source_text": dimensions,
            "language_codes": sorted(set(languages)),
            "public_domain": public_domain,
            "modified_at": record.findtext(
                "./m:controlfield[@tag='005']", default="", namespaces=MARC_NS
            ),
        })
    return total, bowls


def collect_nli(conn):
    """Collect NLI's numbered incantation-bowl series through its public SRU.

    The broad title search includes books and other records, so only MARC 245
    titles matching the Hebrew numbered-series form are ingested.  Images are
    not downloaded; each source appearance links to the library record and
    preserves rights metadata exposed in MARC 903/939.
    """
    query = 'alma.title="קערת השבעה"'
    first_params = {
        "version": "1.2", "operation": "searchRetrieve", "recordSchema": "marcxml",
        "maximumRecords": 50, "startRecord": 1, "query": query,
    }
    first_url = NLI_SRU + "?" + urllib.parse.urlencode(first_params)
    first_xml = _get_text(first_url).encode("utf-8")
    total, first_bowls = _parse_nli_sru(first_xml)
    bowls = list(first_bowls)
    for start in range(51, total + 1, 50):
        params = dict(first_params, startRecord=start)
        page_xml = _get_text(NLI_SRU + "?" + urllib.parse.urlencode(params)).encode("utf-8")
        _, page_bowls = _parse_nli_sru(page_xml)
        bowls.extend(page_bowls)

    unique = {item["mms_id"]: item for item in bowls if item["mms_id"]}
    if len(unique) != len(bowls):
        raise ValueError("NLI SRU response contained duplicate or blank MMS identifiers")
    prior_objects = {row[0] for row in conn.execute("SELECT id FROM objects")}
    touched = []
    for item in sorted(bowls, key=lambda value: value["number"]):
        record_url = "https://www.nli.org.il/en/manuscripts/NNL_ALEPH%s/NLI" % item["mms_id"]
        shelfmark = item["shelfmark"] or "MMS %s" % item["mms_id"]
        claims = [
            {"field": "current_location", "value_text": "National Library of Israel, Jerusalem"},
            {
                "field": "dating", "value_text": "400–899 CE", "certainty": "reported",
                "notes": "Broad date range shown by the NLI catalogue for this numbered series.",
            },
        ]
        if item["dimensions_source_text"]:
            claims.append({
                "field": "dimensions_source_text",
                "value_text": item["dimensions_source_text"],
                "notes": "Preserved verbatim because the Hebrew catalogue label may be ambiguous.",
            })
        if item["language_codes"]:
            claims.append({
                "field": "catalogue_language_codes",
                "value_text": "; ".join(item["language_codes"]),
                "notes": "MARC 041 values; not automatically treated as a verified inscription-language claim.",
            })
        record = {
            "label": "NLI incantation bowl %s (%s)" % (item["number"], shelfmark),
            "record_status": "confirmed",
            "authenticity": "unassessed",
            "summary": "Numbered incantation-bowl object record in the National Library of Israel.",
            "source": {
                "source_type": "museum_record",
                "title": item["title"],
                "authors": "National Library of Israel",
                "publisher": "National Library of Israel",
                "url": record_url,
                "citation": "National Library of Israel, %s, %s, MMS %s." % (
                    item["title"], shelfmark, item["mms_id"]
                ),
                "access_status": "available",
                "rights_status": "public_domain" if item["public_domain"] else "unknown",
                "notes": "Discovered through the library's public Alma SRU endpoint.",
            },
            "appearance": {
                "locator": "MMS %s" % item["mms_id"],
                "title": item["title"],
                "url": record_url,
                "observed_at": "2026-09-04",
                "raw": item,
            },
            "identifiers": [
                {"scheme": "NLI MMS ID", "value": item["mms_id"], "assigning_body": "National Library of Israel"},
                {"scheme": "NLI bowl number", "value": str(item["number"]), "assigning_body": "National Library of Israel"},
            ] + ([{
                "scheme": "collection designation", "value": item["shelfmark"],
                "assigning_body": "National Library of Israel",
            }] if item["shelfmark"] else []),
            "claims": claims,
        }
        object_id = add_candidate(conn, record)
        touched.append(object_id)

    inserted = len(set(touched) - prior_objects)
    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,status,completed_at,notes) "
        "VALUES (?,?,'complete',CURRENT_TIMESTAMP,?)",
        (run_id, "NLI Alma SRU numbered-bowl sweep", "%s broad records; %s numbered bowls" % (total, len(unique))),
    )
    existing_query = conn.execute(
        "SELECT id FROM search_queries WHERE source_class='museum' AND language='he' "
        "AND query=? AND platform='National Library of Israel Alma SRU'", (query,),
    ).fetchone()
    values = (
        total, inserted, "searched",
        "All %s broad-title MARC results paged; %s exact numbered bowl records ingested." % (total, len(unique)),
    )
    if existing_query:
        conn.execute(
            "UPDATE search_queries SET searched_at=CURRENT_TIMESTAMP,result_count=?,"
            "net_new_candidates=?,status=?,notes=? WHERE id=?", values + (existing_query["id"],),
        )
    else:
        conn.execute(
            "INSERT INTO search_queries "
            "(id,run_id,source_class,language,query,platform,searched_at,result_count,"
            "net_new_candidates,status,notes) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,?,?,?,?)",
            (new_id("search_query"), run_id, "museum", "he", query, "National Library of Israel Alma SRU") + values,
        )
    conn.execute(
        "UPDATE coverage_targets SET status='in_progress',"
        "first_searched_at=coalesce(first_searched_at,CURRENT_TIMESTAMP),"
        "last_searched_at=CURRENT_TIMESTAMP,notes=? WHERE source_class='museum'",
        ("NLI public SRU yielded %s numbered incantation-bowl records." % len(unique),),
    )
    conn.commit()
    return {"broad_results": total, "numbered_bowls": len(unique), "inserted": inserted}


def _parse_penn_jsonld(block, result_title, museum_number, object_url):
    try:
        item = json.loads(html.unescape(block), strict=False)
    except json.JSONDecodeError:
        description_match = re.search(
            r'"description"\s*:\s*"(.*?)"\s*,\s*"identifier"\s*:', block, re.DOTALL
        )
        thumbnail_match = re.search(r'"thumbnailUrl"\s*:\s*"([^"]+)"', block)
        modified_match = re.search(r'"dateModified"\s*:\s*"([^"]+)"', block)
        description = html.unescape(description_match.group(1)) if description_match else ""
        description = description.replace("\\r", " ").replace("\\n", " ").replace("\\\"", '"')
        item = {
            "@type": "CreativeWork",
            "url": object_url,
            "description": description,
            "identifier": museum_number,
            "name": result_title,
            "thumbnailUrl": html.unescape(thumbnail_match.group(1)) if thumbnail_match else None,
            "dateModified": modified_match.group(1) if modified_match else None,
            "parse_note": "Recovered from malformed JSON-LD",
        }
    for key in ("description", "name", "identifier", "material", "thumbnailUrl", "dateModified"):
        value = item.get(key)
        if not isinstance(value, list):
            continue
        if key in ("description", "material"):
            item[key] = " ".join(str(part) for part in value)
        else:
            item[key] = str(value[0]) if value else None
    return item


def collect_penn(conn, delay=0.1):
    """Collect Penn's exact-title `Hebrew Bowl` result set using embedded JSON-LD.

    Penn currently returns no robots.txt, so this collector stores only structured
    record metadata and links. It deliberately does not archive page bodies.
    """
    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,notes) VALUES (?,?,?)",
        (run_id, "Penn Museum exact-title sweep", "Exact phrase search for Hebrew Bowl; throttled metadata retrieval"),
    )
    base = "https://collections.penn.museum/collections/search.php"
    params = {"term": '"Hebrew Bowl"', "submit_term": "Submit"}
    first_url = base + "?" + urllib.parse.urlencode(params)
    first = _get_text(first_url)
    count_match = re.search(r"of\s+([0-9,]+)\s+Records", first)
    expected = int(count_match.group(1).replace(",", "")) if count_match else 0
    pages = max(1, (expected + 31) // 32)
    cards = {}
    card_re = re.compile(
        r'alt="([^"]+)".{0,900}?href="/collections/object/(\d+)".{0,300}?<span>([^<]+)</span>',
        re.DOTALL,
    )
    for page in range(1, pages + 1):
        page_html = first if page == 1 else _get_text(first_url + "&page=%s" % page)
        for museum_number, object_id, title in card_re.findall(page_html):
            cards[object_id] = (html.unescape(museum_number), html.unescape(title))
        if page < pages:
            time.sleep(delay)

    inserted = 0
    already_present = 0
    errors = []
    for index, (object_id, (museum_number, result_title)) in enumerate(cards.items(), 1):
        if conn.execute(
            "SELECT 1 FROM identifiers WHERE scheme='Penn web object ID' AND normalized_value=?",
            (object_id.casefold(),),
        ).fetchone():
            already_present += 1
            continue
        object_url = "https://collections.penn.museum/collections/object/%s" % object_id
        try:
            page_html = _get_text(object_url)
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.DOTALL)
            if not match:
                raise ValueError("JSON-LD not found")
            item = _parse_penn_jsonld(match.group(1), result_title, museum_number, object_url)
            title = item.get("name") or result_title
            description = item.get("description") or ""
            if "hebrew bowl" not in result_title.casefold():
                # The exact phrase search also surfaces a few bowl sherds and
                # Aramaic ostraca through their descriptions. They remain in
                # scope under the broad-evidence policy.
                if not any(term in description.casefold() for term in ("bowl", "aramaic", "manichean")):
                    continue
            if not any(term in (title + " " + description).casefold() for term in ("bowl", "aramaic", "manichean")):
                continue
            lower = description.casefold()
            if "pseudo" in lower or "fake" in lower or "scrawl" in lower:
                authenticity = "pseudo_script"
            else:
                authenticity = "unassessed"
            object_type = "fragment" if any(
                word in lower for word in ("fragment", "incomplete", "sherd")
            ) else "whole_bowl"
            claims = [
                {"field": "current_location", "value_text": "Penn Museum", "locator": object_url},
                {"field": "catalogue_description", "value_text": description, "locator": object_url},
            ]
            material = item.get("material")
            if material:
                claims.append({
                    "field": "material",
                    "value_text": "; ".join(material) if isinstance(material, list) else str(material),
                    "locator": object_url,
                })
            record = {
                "label": "Penn %s: %s" % (museum_number, title),
                "object_type": object_type,
                "record_status": "candidate",
                "authenticity": authenticity,
                "summary": description[:500] or title,
                "source": {
                    "source_type": "museum_record",
                    "title": "%s %s" % (title, museum_number),
                    "publisher": "Penn Museum",
                    "url": object_url,
                    "citation": "Penn Museum Online Collections, %s, web object %s" % (museum_number, object_id),
                    "access_status": "available",
                    "rights_status": "unknown",
                },
                "appearance": {
                    "locator": "Penn web object %s" % object_id,
                    "title": title,
                    "url": object_url,
                    "observed_at": item.get("dateModified"),
                    "description": description,
                    "raw": item,
                },
                "identifiers": [
                    {"scheme": "Penn web object ID", "value": object_id, "assigning_body": "Penn Museum"},
                    {
                        "scheme": "collection designation", "value": museum_number,
                        "normalized_value": normalize_penn_identifier(museum_number),
                        "assigning_body": "Penn Museum",
                    },
                ],
                "claims": claims,
                "media": ([{
                    "media_type": "image", "url": item.get("thumbnailUrl"), "rights_status": "unknown"
                }] if item.get("thumbnailUrl") else []),
            }
            before = conn.total_changes
            add_candidate(conn, record)
            inserted += int(conn.total_changes > before)
        except Exception as exc:
            errors.append({"object_id": object_id, "error": str(exc)})
        if index < len(cards):
            time.sleep(delay)

    query_row = conn.execute(
        "SELECT id,coalesce(net_new_candidates,0) AS prior_new FROM search_queries "
        "WHERE source_class='museum' AND language='en' AND query=? AND platform=?",
        ('"Hebrew Bowl"', "Penn Museum Online Collections"),
    ).fetchone()
    query_notes = (
        "Structured metadata only; full-page archival withheld because robots.txt was unavailable. "
        "%s parse errors remain." % len(errors)
    )
    if query_row:
        conn.execute(
            "UPDATE search_queries SET searched_at=CURRENT_TIMESTAMP,result_count=?,net_new_candidates=?,"
            "status=?,notes=? WHERE id=?",
            (expected, query_row["prior_new"] + inserted, "searched" if not errors else "follow_up", query_notes, query_row["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO search_queries "
            "(id,run_id,source_class,language,query,platform,searched_at,result_count,net_new_candidates,status,notes) "
            "VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,?,?,?,?)",
            (
                new_id("search_query"), run_id, "museum", "en", '"Hebrew Bowl"', "Penn Museum Online Collections",
                expected, inserted, "searched" if not errors else "follow_up", query_notes,
            ),
        )
    conn.execute(
        "UPDATE search_runs SET status='complete',completed_at=CURRENT_TIMESTAMP WHERE id=?", (run_id,)
    )
    conn.execute(
        "UPDATE coverage_targets SET status='in_progress',first_searched_at=coalesce(first_searched_at,CURRENT_TIMESTAMP),"
        "last_searched_at=CURRENT_TIMESTAMP,notes=? WHERE source_class='museum'",
        ("Penn exact-title sweep collected %s of %s parsed cards; %s errors" % (len(cards), expected, len(errors)),),
    )
    if not conn.execute(
        "SELECT 1 FROM leads WHERE description LIKE 'Penn Museum robots.txt%'"
    ).fetchone():
        conn.execute(
            "INSERT INTO leads(id,lead_type,description,url,status,priority) VALUES (?,?,?,?,?,?)",
            (
                new_id("lead"), "restricted_source",
                "Penn Museum robots.txt was unavailable; metadata was collected slowly, but full page captures were not archived.",
                "https://collections.penn.museum/robots.txt", "blocked", 1,
            ),
        )
    conn.commit()
    return {
        "expected": expected, "cards": len(cards), "inserted": inserted,
        "already_present": already_present, "errors": errors,
    }


APOTROPAIC_INDEX = "https://apotropaicarts.com/articles/amuletindices/bowlsa/"


def _clean_index_token(value):
    """Recover the final bold designation when malformed HTML swallows a citation."""
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    parts = [part.strip() for part in value.splitlines() if part.strip()]
    return parts[-1] if parts else ""


def _parse_apotropaic_entries(page_html):
    matches = list(re.finditer(r"<b[^>]*>(.*?)</b>", page_html, re.IGNORECASE | re.DOTALL))
    entries = {}
    for index, match in enumerate(matches):
        designation = _clean_index_token(match.group(1))
        if index == 0 or designation.startswith("Note"):
            continue
        tail_end = matches[index + 1].start() if index + 1 < len(matches) else len(page_html)
        tail = page_html[match.end():tail_end]
        tail = re.split(r"<(?:br|/p)\b", tail, maxsplit=1, flags=re.IGNORECASE)[0]
        note = html.unescape(re.sub(r"<[^>]+>", "", tail)).strip()
        record = entries.setdefault(designation, {"designation": designation, "notes": []})
        if note and note not in record["notes"]:
            record["notes"].append(note)
    return list(entries.values())


def _source_scoped_index_key(designation):
    match = re.fullmatch(r"AIT(\d+)", designation, re.IGNORECASE)
    if match:
        return "Montgomery 1913::%s" % int(match.group(1))
    match = re.fullmatch(r"BM(\d{3}(?:A|M|ES|SY|Ps))", designation, re.IGNORECASE)
    if match:
        suffix = match.group(1)
        suffix = suffix[:-2] + "Ps" if suffix.casefold().endswith("ps") else suffix.upper()
        return "Segal 2000::%s" % suffix
    return None


def collect_apotropaic(conn):
    """Collect the public Apotropaic Arts Aramaic-bowl index as leads.

    This is a secondary discovery index rather than an authority. It is useful
    because it exposes publication and collection designations that can be
    chased into primary catalogues. Parenthetical concordances remain weak
    evidence until checked against those publications.
    """
    page_html = _get_text(APOTROPAIC_INDEX)
    entries = _parse_apotropaic_entries(page_html)
    source = {
        "source_type": "database",
        "title": "Index of Aramaic Incantation Bowls",
        "authors": "Apotropaic Arts",
        "url": APOTROPAIC_INDEX,
        "citation": "Apotropaic Arts, ‘Index of Aramaic Incantation Bowls’ (online index).",
        "access_status": "available",
        "rights_status": "copyrighted",
        "notes": (
            "Secondary discovery index. Designations and concordances require verification "
            "against the cited editions; page body not archived because robots.txt is unavailable."
        ),
    }
    inserted = 0
    for entry in entries:
        designation = entry["designation"]
        note = "; ".join(entry["notes"])
        identifiers = [{
            "scheme": "collection designation",
            "value": designation,
            "assigning_body": "As reported by Apotropaic Arts",
            "confidence": 0.7,
            "notes": "Secondary index; assigning collection varies by prefix.",
        }]
        canonical_key = _source_scoped_index_key(designation)
        if canonical_key:
            identifiers.append({
                "scheme": "publication object key", "value": canonical_key,
                "assigning_body": "Source-scoped concordance", "confidence": 0.95,
            })
        aliases = re.findall(
            r"(?:=|a\.k\.a\.)\s*([A-Za-z][A-Za-z0-9./-]*)", note, re.IGNORECASE
        )
        identifiers.extend({
            "scheme": "bibliographic concordance", "value": alias,
            "assigning_body": "As reported by Apotropaic Arts", "confidence": 0.6,
        } for alias in aliases)
        lower_note = note.casefold()
        record = {
            "label": "Apotropaic index %s" % designation,
            "object_type": "fragment" if "fragmentary" in lower_note else "uncertain",
            "record_status": "candidate",
            "authenticity": "unassessed",
            "summary": "Secondary-index entry%s" % (": " + note if note else ""),
            "source": source,
            "appearance": {
                "locator": "index entry %s" % designation,
                "title": designation,
                "url": APOTROPAIC_INDEX + "#" + urllib.parse.quote(designation),
                "description": note or None,
            },
            "identifiers": identifiers,
            "claims": ([{
                "field": "condition", "value_text": "fragmentary",
                "certainty": "reported", "locator": "index entry %s" % designation,
            }] if "fragmentary" in lower_note else []),
        }
        before = conn.total_changes
        add_candidate(conn, record)
        inserted += int(conn.total_changes > before)

    if not conn.execute(
        "SELECT 1 FROM leads WHERE url=? AND lead_type='citation'", (APOTROPAIC_INDEX,)
    ).fetchone():
        conn.execute(
            "INSERT INTO leads(id,source_id,lead_type,description,url,status,priority) "
            "SELECT ?,id,'citation',?,?,?,3 FROM sources WHERE url=?",
            (
                new_id("lead"),
                "Verify every Apotropaic Arts designation and concordance against its cited primary edition.",
                APOTROPAIC_INDEX, "open", APOTROPAIC_INDEX,
            ),
        )
    conn.execute(
        "UPDATE coverage_targets SET status='in_progress',"
        "first_searched_at=coalesce(first_searched_at,CURRENT_TIMESTAMP),"
        "last_searched_at=CURRENT_TIMESTAMP,notes=? WHERE source_class='bibliography'",
        ("Collected %s unique Aramaic-bowl designations from a secondary publication index." % len(entries),),
    )
    conn.commit()
    return {"unique_designations": len(entries), "inserted_or_enriched": inserted}


SCHOYEN_SITEMAP = (
    "http://www.schoyencollection.com/index.php?option=com_jmap&view=sitemap&format=xml"
)


def _british_museum_registration(object_url):
    """Render a stable, human-readable registration value from a BM object URL.

    The URL key remains the authoritative exact identifier.  This rendering is
    intentionally conservative because older BM registration series use several
    punctuation conventions (for example ``N-1692`` and ``Rm-III-31``).
    """
    key = object_url.rstrip("/").rsplit("/", 1)[-1]
    return key[2:] if key.startswith("W_") else key


def collect_british_museum_related(conn, seed_path=None):
    """Ingest the 159 objects in the BM relation for Segal (2000).

    The British Museum currently presents this relation in a browser-rendered
    two-page view rather than a public API response.  The checked seed records
    the visible fields and exact object URLs without copying descriptions,
    inscription text, or images from the individual object pages.
    """
    if seed_path is None:
        seed_path = (
            Path(__file__).resolve().parents[2]
            / "research" / "seeds" / "british_museum_segal_related_159.json"
        )
    with open(seed_path, encoding="utf-8") as handle:
        dataset = json.load(handle)
    records = dataset.get("records", [])
    if dataset.get("relation_count") != 159 or len(records) != 159:
        raise ValueError("British Museum Segal relation seed must contain exactly 159 records")
    if len({record["url"] for record in records}) != 159:
        raise ValueError("British Museum Segal relation seed contains duplicate object URLs")

    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,notes) VALUES (?,?,?)",
        (
            run_id,
            "British Museum Segal 2000 relation sweep",
            "Browser-visible extraction of both Related objects pages (100 + 59).",
        ),
    )
    source = {
        "source_type": "museum_record",
        "title": "159 objects related to Segal 2000a",
        "authors": "The British Museum",
        "publisher": "The British Museum",
        "url": "https://www.britishmuseum.org/collection/term/BIB3908?id=BIB3908&page=1",
        "citation": (
            "The British Museum, Collections Online, 159 objects related to "
            "‘Catalogue of the Aramaic and Mandaic Incantation Bowls in the British Museum; "
            "Segal 2000a’ (browser-visible relation, retrieved %s)."
            % dataset.get("retrieved_at", "2026-09-04")
        ),
        "access_status": "available",
        "rights_status": "copyrighted",
        "notes": dataset.get("extraction_note"),
    }
    inserted = 0
    for item in records:
        object_url = item["url"]
        museum_number = item["Museum number"]
        title = item.get("title") or "incantation bowl"
        locator = "Related objects: %s" % _british_museum_registration(object_url)
        claims = [{
            "field": "current_location", "value_text": "The British Museum", "locator": locator,
        }]
        for source_field, claim_field in (
            ("Cultures/periods", "period"),
            ("Production date", "dating"),
            ("Production place", "production_place"),
            ("Findspot", "findspot"),
        ):
            if item.get(source_field):
                claims.append({
                    "field": claim_field,
                    "value_text": item[source_field],
                    "locator": locator,
                })
        events = []
        findspot = item.get("Findspot")
        if findspot:
            event_type = "excavation" if findspot.startswith("Excavated/") else "find"
            events.append({
                "event_type": event_type,
                "place": findspot.split(":", 1)[-1].strip(),
                "details": findspot,
                "locator": locator,
            })
        record = {
            "label": "British Museum %s: %s" % (museum_number, title),
            "object_type": "whole_bowl",
            "record_status": "probable",
            "authenticity": "unassessed",
            "summary": "%s related by the British Museum to Segal 2000a." % title,
            "source": source,
            "appearance": {
                "locator": locator,
                "title": title,
                "url": object_url,
                "observed_at": dataset.get("retrieved_at"),
                "description": "; ".join(
                    "%s: %s" % (key, item[key])
                    for key in ("Museum number", "Cultures/periods", "Production date", "Production place", "Findspot")
                    if item.get(key)
                ),
                "raw": item,
            },
            "identifiers": [
                {
                    "scheme": "British Museum object key",
                    "value": object_url.rstrip("/").rsplit("/", 1)[-1],
                    "assigning_body": "The British Museum",
                },
                {
                    "scheme": "British Museum museum number",
                    "value": museum_number,
                    "assigning_body": "The British Museum",
                },
                {
                    "scheme": "British Museum registration URL value",
                    "value": _british_museum_registration(object_url),
                    "assigning_body": "The British Museum",
                    "notes": "Literal value from the stable object URL; punctuation is not editorially normalized.",
                },
            ],
            "claims": claims,
            "events": events,
        }
        before = conn.total_changes
        add_candidate(conn, record)
        inserted += int(conn.total_changes > before)

    query = "Segal 2000a Related objects"
    existing_query = conn.execute(
        "SELECT id FROM search_queries WHERE source_class='museum' AND language='en' "
        "AND query=? AND platform='British Museum Collections Online'",
        (query,),
    ).fetchone()
    query_values = (
        len(records), inserted, "searched",
        "All two browser-visible result pages extracted; 100 records on page 1 and 59 on page 2.",
    )
    if existing_query:
        conn.execute(
            "UPDATE search_queries SET searched_at=CURRENT_TIMESTAMP,result_count=?,"
            "net_new_candidates=?,status=?,notes=? WHERE id=?",
            query_values + (existing_query["id"],),
        )
    else:
        conn.execute(
            "INSERT INTO search_queries "
            "(id,run_id,source_class,language,query,platform,searched_at,result_count,"
            "net_new_candidates,status,notes) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,?,?,?,?)",
            (
                new_id("search_query"), run_id, "museum", "en", query,
                "British Museum Collections Online",
            ) + query_values,
        )
    conn.execute(
        "UPDATE search_runs SET status='complete',completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (run_id,),
    )
    conn.execute(
        "UPDATE coverage_targets SET status='in_progress',"
        "first_searched_at=coalesce(first_searched_at,CURRENT_TIMESTAMP),"
        "last_searched_at=CURRENT_TIMESTAMP,notes=? WHERE source_class='museum'",
        (
            "British Museum Segal relation fully enumerated (159 records); individual page "
            "enrichment and 142-text concordance remain.",
        ),
    )
    conn.execute(
        "UPDATE leads SET status='in_progress',resolution_notes=? "
        "WHERE description LIKE 'Identify and account for the difference between the 142%'",
        (
            "The 159 museum records are now fully enumerated. Explaining the 17-record difference "
            "and mapping each record to a Segal text number still requires the catalogue concordance.",
        ),
    )
    conn.commit()
    return {"relation_records": len(records), "inserted_or_enriched": inserted}


def load_british_museum_page_mappings(conn, path):
    """Ingest checked item-page metadata that is absent from the BM relation export."""
    with open(path, encoding="utf-8") as handle:
        dataset = json.load(handle)
    records = dataset.get("records", [])
    if len({record["segal"] for record in records}) != len(records):
        raise ValueError("British Museum enrichment contains duplicate Segal designations")
    touched = []
    for item in records:
        object_key = item["url"].rstrip("/").rsplit("/", 1)[-1]
        locator = "object %s" % object_key
        claims = [
            {"field": "current_location", "value_text": "The British Museum", "locator": locator},
            {"field": "material", "value_text": item.get("material", "pottery"), "locator": locator},
        ]
        for input_field, claim_field in (
            ("dating", "dating"), ("dimensions", "dimensions"),
            ("inscription_language", "inscription_language"), ("client", "client"),
            ("text_purpose", "text_purpose"), ("condition", "condition"),
            ("findspot", "findspot"),
        ):
            if item.get(input_field):
                claims.append({
                    "field": claim_field, "value_text": item[input_field], "locator": locator,
                    "certainty": "reported",
                })
        record = {
            "object_id": item["object_id"],
            "label": "British Museum %s (Segal %s)" % (item["museum_number"], item["segal"]),
            "record_status": "confirmed",
            "authenticity": "unassessed",
            "summary": item.get("description") or "British Museum incantation bowl.",
            "source": {
                "source_type": "museum_record",
                "title": "incantation bowl: %s" % item["museum_number"],
                "authors": "The British Museum",
                "publisher": "The British Museum",
                "url": item["url"],
                "citation": (
                    "The British Museum, Collections Online, incantation bowl %s, "
                    "Segal %s; accessed %s."
                    % (item["museum_number"], item["segal"], dataset["observed_at"])
                ),
                "access_status": "available",
                "rights_status": "copyrighted",
                "notes": "Checked item-page metadata; no inscription or image content copied.",
            },
            "appearance": {
                "locator": locator, "title": "incantation bowl", "url": item["url"],
                "observed_at": dataset["observed_at"], "description": item.get("description"),
            },
            "identifiers": [
                {
                    "scheme": "British Museum object key", "value": object_key,
                    "assigning_body": "The British Museum",
                },
                {
                    "scheme": "British Museum museum number", "value": item["museum_number"],
                    "assigning_body": "The British Museum",
                },
                {
                    "scheme": "publication object key", "value": "Segal 2000::%s" % item["segal"],
                    "assigning_body": "J. B. Segal, with a contribution by Erica C. D. Hunter",
                    "notes": "Siglum displayed in the British Museum page's Segal 2000a reference.",
                },
            ],
            "claims": claims,
        }
        touched.append(add_candidate(conn, record))
    conn.commit()
    return {"checked_page_records": len(records), "objects_touched": len(set(touched))}


def _clean_html(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def _schoyen_attributes(page_html):
    attributes = {}
    for row in re.findall(r'<tr class="djc_attribute.*?</tr>', page_html, re.DOTALL):
        label = re.search(r'djc_attribute-label">(.*?)</span>', row, re.DOTALL)
        value = re.search(r'<td\s+class="djc_value">(.*?)</td>', row, re.DOTALL)
        if label and value:
            attributes[_clean_html(label.group(1))] = _clean_html(value.group(1))
    return attributes


def _schoyen_urls(sitemap):
    urls = re.findall(r"<loc>(.*?)</loc>", sitemap, re.DOTALL)
    return sorted({html.unescape(url.strip()) for url in urls if (
        "incantation-bowl-ms-" in url
        or "zoroastrianism/incantations-angra-mainu-ms-" in url
        or "zoroastrianism/incantations-against-demons-ms-" in url
    )})


def _schoyen_claims(attributes, locator):
    claims = [{"field": "current_location", "value_text": "The Schøyen Collection", "locator": locator}]
    for source_label, field in (
        ("Description", "catalogue_description"), ("Place of origin", "origin"),
        ("Dates", "dating"), ("Published", "publication_status"),
        ("Exhibited", "exhibition_history"),
    ):
        if attributes.get(source_label):
            claims.append({"field": field, "value_text": attributes[source_label], "locator": locator})
    description = attributes.get("Description", "")
    if "Jewish-Aramaic" in description:
        claims.append({"field": "inscription_language", "value_text": "Jewish Babylonian Aramaic", "locator": locator})
    elif "Zoroastrian Middle Persian" in description:
        claims.append({"field": "inscription_language", "value_text": "Middle Persian", "locator": locator})
    if " on clay" in description:
        claims.append({"field": "material", "value_text": "clay", "locator": locator})
    dimension = re.search(r"\b(\d{1,2},\s*\d\s*x\s*\d{1,2},\d|\d{1,2},\d\s*x\s*\d{1,2},\d)\s*cm", description)
    if dimension:
        claims.append({"field": "dimensions", "value_text": dimension.group(1).replace(",", ".") + " cm", "locator": locator})
    return claims


def collect_schoyen(conn, delay=0.2):
    sitemap = _get_text(SCHOYEN_SITEMAP)
    urls = _schoyen_urls(sitemap)
    inserted = 0
    primary = 0
    related = 0
    source_ids = []
    for page_index, url in enumerate(urls):
        page_html = _get_text(url)
        attributes = _schoyen_attributes(page_html)
        manuscript = attributes.get("MS")
        title = attributes.get("MS Short Title")
        description = attributes.get("Description", "")
        if not manuscript or "incantation bowl" not in (title + " " + description).casefold():
            continue
        designation = "MS " + manuscript
        source = {
            "source_type": "museum_record",
            "title": "%s %s" % (designation, title.title()),
            "authors": "The Schøyen Collection",
            "publisher": "The Schøyen Collection",
            "url": url,
            "citation": "The Schøyen Collection, %s, online collection record." % designation,
            "access_status": "available",
            "rights_status": "copyrighted",
        }
        record = {
            "label": "%s: %s" % (designation, title.title()),
            "record_status": "probable",
            "authenticity": "accepted",
            "summary": description,
            "source": source,
            "appearance": {"locator": "Schøyen record %s" % designation, "title": title, "url": url, "raw": attributes},
            "identifiers": [{"scheme": "collection designation", "value": designation, "assigning_body": "The Schøyen Collection"}],
            "claims": _schoyen_claims(attributes, "Schøyen record %s" % designation),
            "texts": ([{
                "text_type": "translation" if "Jewish-Aramaic" in description else "summary",
                "language": "English", "content": attributes["Text"],
                "editor": "The Schøyen Collection / credited specialist",
                "locator": "Text field in online record", "rights_status": "copyrighted",
                "public_ok": False, "notes": attributes.get("Published"),
            }] if attributes.get("Text") else []),
        }
        before = conn.total_changes
        object_id = add_candidate(conn, record)
        inserted += int(conn.total_changes > before)
        primary += 1
        source_id = conn.execute("SELECT id FROM sources WHERE url=?", (url,)).fetchone()[0]
        source_ids.append(source_id)

        # MS 2053/196's Context field explicitly identifies dozens of other
        # bowls by manuscript number. Each becomes a citation-backed lead.
        context = attributes.get("Context", "")
        for sentence in re.split(r"(?<=\.)\s+", context):
            quoted = re.match(r"(.+?)\s+(?:is|are)\s+cited on MSS?\s+(.+)", sentence)
            if not quoted:
                continue
            reference, designation_list = quoted.groups()
            for family, number in re.findall(r"\b(19\d{2}|2053)/(\d+)\b", designation_list):
                related_designation = "MS %s/%s" % (family, int(number))
                if related_designation == designation:
                    continue
                related_record = {
                    "label": "Schøyen %s (context citation)" % related_designation,
                    "object_type": "uncertain", "record_status": "candidate",
                    "authenticity": "unassessed",
                    "summary": "%s is cited in the context note for %s." % (reference, designation),
                    "source_id": source_id,
                    "appearance": {
                        "locator": "%s context: %s" % (designation, related_designation),
                        "title": related_designation, "url": url,
                        "description": sentence,
                    },
                    "identifiers": [{
                        "scheme": "collection designation", "value": related_designation,
                        "assigning_body": "The Schøyen Collection",
                    }],
                    "claims": [
                        {"field": "current_location", "value_text": "The Schøyen Collection"},
                        {"field": "biblical_quotation", "value_text": reference, "certainty": "reported"},
                    ],
                }
                before = conn.total_changes
                add_candidate(conn, related_record)
                inserted += int(conn.total_changes > before)
                related += 1
        if page_index + 1 < len(urls):
            time.sleep(delay)

    conn.execute(
        "UPDATE coverage_targets SET status='in_progress',"
        "first_searched_at=coalesce(first_searched_at,CURRENT_TIMESTAMP),"
        "last_searched_at=CURRENT_TIMESTAMP,notes=? WHERE source_class='museum'",
        ("Schøyen sitemap sweep: %s detailed bowl pages and %s context designations." % (primary, related),),
    )
    if not conn.execute(
        "SELECT 1 FROM leads WHERE url=? AND description LIKE 'Reconcile the Schøyen%';",
        ("https://www.schoyencollection.com/magical-literature-introduction",),
    ).fetchone():
        overview_id = conn.execute(
            "SELECT id FROM sources WHERE url=?",
            ("https://www.schoyencollection.com/magical-literature-introduction",),
        ).fetchone()
        conn.execute(
            "INSERT INTO leads(id,source_id,lead_type,description,url,status,priority) VALUES (?,?,?,?,?,?,?)",
            (
                new_id("lead"), overview_id[0] if overview_id else None, "collection",
                "Reconcile the Schøyen overview's aggregate 654 Jewish-Aramaic bowls and jugs with individually identifiable MS records and the seven-volume publication programme.",
                "https://www.schoyencollection.com/magical-literature-introduction", "open", 3,
            ),
        )
    conn.commit()
    return {"detailed_records": primary, "context_designations": related, "inserted_or_enriched": inserted, "source_ids": source_ids}
