"""Reproducible broad metadata sweeps used by the discovery campaign.

These collectors deliberately ingest publication/library *sources*, not bowl
objects.  A metadata hit is not evidence that a distinct physical bowl exists;
object candidates are created only after a catalogue, edition, or object record
has been inspected closely enough to supply a precise locator.
"""

import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .ids import new_id
from .ingest import add_source


OPENALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"
INTERNET_ARCHIVE = "https://archive.org/advancedsearch.php"
USER_AGENT = "IncantationBowlIndexResearch/0.1 (+noncommercial scholarly corpus)"


def _get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def _plain(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split())


def _relevant(text):
    folded = _plain(text).casefold()
    phrases = (
        "incantation bowl", "incantation bowls", "magic bowl", "magic bowls",
        "magical bowl", "magical bowls", "demon bowl", "demon bowls",
        "aramaic bowl", "aramaic bowls", "zauberschale", "zauberschalen",
        "beschwörungsschale", "beschwörungsschalen", "קערת השבעה", "קערות השבעה",
        "bol d'incantation", "bols d'incantation", "bol magique", "bols magiques",
        "магическая чаша", "магические чаши",
    )
    return any(phrase in folded for phrase in phrases)


def _source_type(work_type):
    return {
        "article": "article", "journal-article": "article",
        "book": "book", "monograph": "book", "edited-book": "book",
        "book-chapter": "chapter", "book-section": "chapter",
        "dissertation": "thesis", "posted-content": "repository",
        "proceedings-article": "article", "report": "other",
    }.get(work_type, "other")


def _author_names(authorships):
    names = []
    for authorship in authorships or []:
        author = authorship.get("author") or {}
        if author.get("display_name"):
            names.append(author["display_name"])
    return "; ".join(names) or None


def _crossref_authors(authors):
    names = []
    for author in authors or []:
        name = " ".join(filter(None, (author.get("given"), author.get("family"))))
        if name:
            names.append(name)
    return "; ".join(names) or None


def _log_query(conn, run_id, source_class, language, query, platform, result_count, notes):
    existing = conn.execute(
        "SELECT id FROM search_queries WHERE source_class=? AND language=? AND query=? AND platform=?",
        (source_class, language, query, platform),
    ).fetchone()
    values = (run_id, result_count, 0, "searched", notes)
    if existing:
        conn.execute(
            "UPDATE search_queries SET run_id=?,searched_at=CURRENT_TIMESTAMP,result_count=?,"
            "net_new_candidates=?,status=?,notes=? WHERE id=?",
            values + (existing["id"],),
        )
    else:
        conn.execute(
            "INSERT INTO search_queries(id,run_id,source_class,language,query,platform,searched_at,"
            "result_count,net_new_candidates,status,notes) VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,?,?,?,?)",
            (new_id("search_query"), run_id, source_class, language, query, platform) + values[1:],
        )


def _terms(config_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return [(item["language"], item["query"]) for item in config["terms"]]


def collect_scholarly_metadata(conn, config_path):
    """Search OpenAlex and Crossref for every multilingual matrix term."""
    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,notes) VALUES (?,?,?)",
        (run_id, "OpenAlex and Crossref multilingual metadata sweep", str(config_path)),
    )
    raw_hits = 0
    relevant_hits = 0
    before_sources = conn.execute("SELECT count(*) FROM sources").fetchone()[0]
    errors = []
    for language, query in _terms(config_path):
        term_hits = 0
        params = {"search": query, "per-page": 50, "select": "id,doi,title,publication_year,type,authorships,primary_location"}
        try:
            payload = _get_json(OPENALEX + "?" + urllib.parse.urlencode(params))
            results = payload.get("results") or []
            raw_hits += len(results)
            for work in results:
                title = _plain(work.get("title"))
                if not _relevant(title):
                    continue
                term_hits += 1
                relevant_hits += 1
                location = work.get("primary_location") or {}
                source = location.get("source") or {}
                doi = (work.get("doi") or "").removeprefix("https://doi.org/") or None
                url = work.get("doi") or work.get("id")
                add_source(conn, {
                    "source_type": _source_type(work.get("type")), "title": title,
                    "authors": _author_names(work.get("authorships")),
                    "issued_year": work.get("publication_year"),
                    "container_title": source.get("display_name"), "url": url, "doi": doi,
                    "citation": "%s%s. OpenAlex %s." % (
                        title, " (%s)" % work.get("publication_year") if work.get("publication_year") else "",
                        (work.get("id") or "").rsplit("/", 1)[-1],
                    ),
                    "access_status": "available" if location.get("is_oa") else "unknown",
                    "rights_status": "open_license" if location.get("is_oa") else "unknown",
                    "notes": "Discovered in broad OpenAlex metadata sweep; object-level contents require source inspection.",
                })
        except Exception as exc:
            errors.append("OpenAlex %s: %s" % (query, exc))

        crossref_params = {
            "query.bibliographic": query, "rows": 30,
            "select": "DOI,title,author,published,URL,type,publisher,container-title",
        }
        try:
            payload = _get_json(CROSSREF + "?" + urllib.parse.urlencode(crossref_params))
            items = (payload.get("message") or {}).get("items") or []
            raw_hits += len(items)
            for work in items:
                title = _plain(" ".join(work.get("title") or []))
                if not _relevant(title):
                    continue
                term_hits += 1
                relevant_hits += 1
                date_parts = ((work.get("published") or {}).get("date-parts") or [[]])[0]
                year = date_parts[0] if date_parts else None
                doi = work.get("DOI")
                add_source(conn, {
                    "source_type": _source_type(work.get("type")), "title": title,
                    "authors": _crossref_authors(work.get("author")), "issued_year": year,
                    "container_title": _plain("; ".join(work.get("container-title") or [])) or None,
                    "publisher": work.get("publisher"), "url": work.get("URL"), "doi": doi,
                    "citation": "%s%s. Crossref DOI %s." % (
                        title, " (%s)" % year if year else "", doi or "not assigned",
                    ),
                    "access_status": "unknown", "rights_status": "unknown",
                    "notes": "Discovered in broad Crossref metadata sweep; object-level contents require source inspection.",
                })
        except Exception as exc:
            errors.append("Crossref %s: %s" % (query, exc))

        note = "%s title-relevant hits across OpenAlex/Crossref first-result windows; metadata sources deduplicated by DOI/URL." % term_hits
        for source_class in ("article", "book", "chapter", "thesis", "catalogue"):
            _log_query(conn, run_id, source_class, language, query, "scholarly_index", term_hits, note)

    conn.execute(
        "UPDATE search_runs SET status=?,completed_at=CURRENT_TIMESTAMP,notes=? WHERE id=?",
        ("failed" if errors else "complete", "; ".join(errors) if errors else "All 17 terms searched in both APIs.", run_id),
    )
    conn.commit()
    return {
        "raw_hits": raw_hits, "title_relevant_hits": relevant_hits,
        "new_sources": conn.execute("SELECT count(*) FROM sources").fetchone()[0] - before_sources,
        "errors": errors,
    }


def collect_internet_archive(conn, config_path):
    """Search Internet Archive full text and metadata for every matrix term."""
    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,notes) VALUES (?,?,?)",
        (run_id, "Internet Archive multilingual full-text sweep", str(config_path)),
    )
    before_sources = conn.execute("SELECT count(*) FROM sources").fetchone()[0]
    raw_hits = 0
    relevant_hits = 0
    errors = []
    for language, query in _terms(config_path):
        params = {
            "q": query, "fl[]": ["identifier", "title", "creator", "date", "mediatype"],
            "rows": 50, "page": 1, "output": "json",
        }
        try:
            payload = _get_json(INTERNET_ARCHIVE + "?" + urllib.parse.urlencode(params, doseq=True))
            response = payload.get("response") or {}
            docs = response.get("docs") or []
            count = int(response.get("numFound") or 0)
            raw_hits += count
            term_relevant = 0
            for item in docs:
                title = _plain(item.get("title") if isinstance(item.get("title"), str) else " ".join(item.get("title") or []))
                if not (_relevant(title) or _relevant(query)):
                    continue
                identifier = item.get("identifier")
                if not identifier:
                    continue
                term_relevant += 1
                relevant_hits += 1
                creator = item.get("creator")
                if isinstance(creator, list):
                    creator = "; ".join(str(value) for value in creator)
                date = str(item.get("date") or "")
                year_match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", date)
                url = "https://archive.org/details/%s" % identifier
                add_source(conn, {
                    "source_type": "repository", "title": title or identifier,
                    "authors": creator, "issued_year": int(year_match.group(1)) if year_match else None,
                    "publisher": "Internet Archive", "url": url,
                    "citation": "%s. Internet Archive item %s." % (title or identifier, identifier),
                    "access_status": "available", "rights_status": "unknown",
                    "notes": "Discovered through Internet Archive full-text/metadata search; availability and reuse rights must be checked at item level.",
                })
            note = "%s total IA matches; %s records retained from the first 50 results." % (count, term_relevant)
            for source_class in ("book", "catalogue", "excavation_report"):
                _log_query(conn, run_id, source_class, language, query, "digitized_library", count, note)
        except Exception as exc:
            errors.append("Internet Archive %s: %s" % (query, exc))
            for source_class in ("book", "catalogue", "excavation_report"):
                _log_query(conn, run_id, source_class, language, query, "digitized_library", 0, "Request failed: %s" % exc)
    conn.execute(
        "UPDATE search_runs SET status=?,completed_at=CURRENT_TIMESTAMP,notes=? WHERE id=?",
        ("failed" if errors else "complete", "; ".join(errors) if errors else "All 17 terms searched.", run_id),
    )
    conn.commit()
    return {
        "raw_hits": raw_hits, "retained_hits": relevant_hits,
        "new_sources": conn.execute("SELECT count(*) FROM sources").fetchone()[0] - before_sources,
        "errors": errors,
    }


def collect_repository_metadata(conn, config_path):
    """Search OpenAlex's repository-location index for every matrix term."""
    run_id = new_id("search_run")
    conn.execute(
        "INSERT INTO search_runs(id,strategy,notes) VALUES (?,?,?)",
        (run_id, "OpenAlex institutional-repository location sweep", str(config_path)),
    )
    before_sources = conn.execute("SELECT count(*) FROM sources").fetchone()[0]
    total_hits = 0
    retained_hits = 0
    errors = []
    for language, query in _terms(config_path):
        params = {
            "search": query, "filter": "locations.source.type:repository", "per-page": 50,
            "select": "id,doi,title,publication_year,type,authorships,locations",
        }
        try:
            payload = _get_json(OPENALEX + "?" + urllib.parse.urlencode(params))
            results = payload.get("results") or []
            count = int((payload.get("meta") or {}).get("count") or 0)
            total_hits += count
            term_retained = 0
            for work in results:
                title = _plain(work.get("title"))
                if not _relevant(title):
                    continue
                repository_location = None
                for location in work.get("locations") or []:
                    if ((location.get("source") or {}).get("type") == "repository"):
                        repository_location = location
                        break
                if not repository_location:
                    continue
                term_retained += 1
                retained_hits += 1
                repository = repository_location.get("source") or {}
                doi = (work.get("doi") or "").removeprefix("https://doi.org/") or None
                repository_url = repository_location.get("landing_page_url") or repository_location.get("pdf_url")
                add_source(conn, {
                    "source_type": _source_type(work.get("type")), "title": title,
                    "authors": _author_names(work.get("authorships")),
                    "issued_year": work.get("publication_year"),
                    "container_title": repository.get("display_name"),
                    "url": work.get("doi") or repository_url or work.get("id"), "doi": doi,
                    "citation": "%s%s. Repository location indexed by OpenAlex %s." % (
                        title, " (%s)" % work.get("publication_year") if work.get("publication_year") else "",
                        (work.get("id") or "").rsplit("/", 1)[-1],
                    ),
                    "access_status": "available" if repository_url else "unknown",
                    "rights_status": "open_license" if repository_location.get("is_oa") else "unknown",
                    "notes": "Institutional repository: %s; landing page: %s" % (
                        repository.get("display_name") or "unnamed repository", repository_url or "not exposed",
                    ),
                })
            note = "%s repository-indexed matches; %s title-relevant records retained from first 50." % (count, term_retained)
            for source_class in ("thesis", "article", "excavation_report"):
                _log_query(conn, run_id, source_class, language, query, "institutional_repository", count, note)
        except Exception as exc:
            errors.append("OpenAlex repository %s: %s" % (query, exc))
            for source_class in ("thesis", "article", "excavation_report"):
                _log_query(conn, run_id, source_class, language, query, "institutional_repository", 0, "Request failed: %s" % exc)
    conn.execute(
        "UPDATE search_runs SET status=?,completed_at=CURRENT_TIMESTAMP,notes=? WHERE id=?",
        ("failed" if errors else "complete", "; ".join(errors) if errors else "All 17 terms searched.", run_id),
    )
    conn.commit()
    return {
        "repository_matches": total_hits, "retained_hits": retained_hits,
        "new_sources": conn.execute("SELECT count(*) FROM sources").fetchone()[0] - before_sources,
        "errors": errors,
    }
