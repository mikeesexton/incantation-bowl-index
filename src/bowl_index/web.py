"""Local research console for browsing and reviewing the private corpus."""

import json
import mimetypes
import secrets
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .db import PROJECT_ROOT, connect, migrate
from .identity import CORE_COVERAGE, identity_rows
from .ids import new_id
from .proofreading import current_text_reviews
from .rights import current_media_reviews


WEB_ROOT = PROJECT_ROOT / "web"
DECISION_STATUSES = {"same_object", "different_objects", "insufficient_evidence"}


def _as_dicts(rows):
    return [dict(row) for row in rows]


def _placeholders(values):
    return ",".join("?" for _ in values)


def _claim_value(row):
    return row.get("normalized_value") or row.get("value_text") or row.get("value_json") or ""


class CorpusCatalog:
    """A compact in-memory identity index backed by read-through SQLite dossiers."""

    def __init__(self, database):
        self.database = Path(database)
        self.refresh()

    def connection(self):
        conn = connect(self.database)
        migrate(conn)
        return conn

    def refresh(self):
        with closing(self.connection()) as conn:
            rows = identity_rows(conn)
            member_to_identity = {}
            for row in rows:
                for member_id in json.loads(row["member_ids_json"]):
                    member_to_identity[member_id] = row["identity_id"]

            claim_values = defaultdict(lambda: defaultdict(set))
            search_terms = defaultdict(list)
            for claim in conn.execute(
                "SELECT object_id,field,value_text,value_json,normalized_value FROM claims"
            ):
                identity_id = member_to_identity.get(claim["object_id"])
                if not identity_id:
                    continue
                value = _claim_value(dict(claim)).strip()
                if value:
                    claim_values[identity_id][claim["field"]].add(value)
                    search_terms[identity_id].append(value)

            for identifier in conn.execute(
                "SELECT object_id,scheme,value,assigning_body FROM identifiers "
                "WHERE object_id IS NOT NULL"
            ):
                identity_id = member_to_identity.get(identifier["object_id"])
                if identity_id:
                    search_terms[identity_id].extend(filter(None, (
                        identifier["scheme"], identifier["value"], identifier["assigning_body"]
                    )))

            for item in conn.execute(
                "SELECT l.object_id,a.title,a.locator,a.description,s.title source_title,s.authors "
                "FROM appearance_object_links l JOIN appearances a ON a.id=l.appearance_id "
                "JOIN sources s ON s.id=a.source_id WHERE l.relation_type<>'rejected'"
            ):
                identity_id = member_to_identity.get(item["object_id"])
                if identity_id:
                    search_terms[identity_id].extend(filter(None, (
                        item["title"], item["locator"], item["description"],
                        item["source_title"], item["authors"],
                    )))

            for item in conn.execute(
                "SELECT object_id,text_type,language,script,content,editor FROM texts"
            ):
                identity_id = member_to_identity.get(item["object_id"])
                if identity_id:
                    search_terms[identity_id].extend(filter(None, (
                        item["text_type"], item["language"], item["script"],
                        item["content"], item["editor"],
                    )))

            self.rows = []
            self.by_id = {}
            self.member_to_identity = member_to_identity
            for original in rows:
                row = dict(original)
                values = claim_values[row["identity_id"]]
                row["locations"] = sorted({
                    value for field in CORE_COVERAGE["location"] for value in values[field]
                })
                row["languages"] = sorted({
                    value for field in CORE_COVERAGE["language"] for value in values[field]
                })
                row["dating"] = sorted({
                    value for field in CORE_COVERAGE["dating"] for value in values[field]
                })
                row["object_types"] = []
                row["conflict_fields"] = json.loads(row.pop("conflict_fields_json"))
                row["raw_conflict_fields"] = json.loads(row.pop("raw_conflict_fields_json"))
                row["untriaged_conflict_fields"] = json.loads(row.pop("untriaged_conflict_fields_json"))
                row["stale_conflict_fields"] = json.loads(row.pop("stale_conflict_fields_json"))
                row["member_ids"] = json.loads(row.pop("member_ids_json"))
                row["identifiers"] = json.loads(row.pop("identifiers_json"))
                row["search_blob"] = " ".join(
                    [row["identity_id"], row["label"]] + search_terms[row["identity_id"]]
                ).casefold()
                self.rows.append(row)
                self.by_id[row["identity_id"]] = row

            object_types = defaultdict(set)
            for item in conn.execute("SELECT id,object_type FROM objects"):
                identity_id = member_to_identity.get(item["id"])
                if identity_id:
                    object_types[identity_id].add(item["object_type"])
            for identity_id, values in object_types.items():
                self.by_id[identity_id]["object_types"] = sorted(values)

    def stats(self):
        coverage_fields = (
            "location", "provenance", "dating", "dimensions", "material", "language",
            "script", "text_edition", "translation", "image",
        )
        return {
            "identities": len(self.rows),
            "source_records": sum(row["member_count"] for row in self.rows),
            "multi_record_identities": sum(row["member_count"] > 1 for row in self.rows),
            "conflicted_identities": sum(bool(row["conflict_fields"]) for row in self.rows),
            "pending_reviews": self._pending_review_count(),
            "coverage": {
                field: sum(row["has_" + field] for row in self.rows)
                for field in coverage_fields
            },
            "next_actions": dict(sorted(Counter(row["next_action"] for row in self.rows).items())),
        }

    def _pending_review_count(self):
        with closing(self.connection()) as conn:
            return conn.execute(
                "SELECT count(*) FROM dedupe_candidates WHERE status='pending'"
            ).fetchone()[0]

    def search(self, params):
        query = params.get("q", [""])[0].strip().casefold()
        tokens = query.split()
        status = params.get("status", [""])[0]
        authenticity = params.get("authenticity", [""])[0]
        action = params.get("next_action", [""])[0]
        coverage = params.get("coverage", [""])[0]
        conflict = params.get("conflict", [""])[0]
        object_type = params.get("object_type", [""])[0]
        sort = params.get("sort", ["completeness_desc"])[0]
        try:
            page = max(1, int(params.get("page", ["1"])[0]))
            page_size = min(100, max(10, int(params.get("page_size", ["40"])[0])))
        except ValueError:
            page, page_size = 1, 40

        items = []
        for row in self.rows:
            if tokens and not all(token in row["search_blob"] for token in tokens):
                continue
            if status and row["record_status"] != status:
                continue
            if authenticity and row["authenticity"] != authenticity:
                continue
            if action and row["next_action"] != action:
                continue
            if coverage and row.get("has_" + coverage, 0):
                continue
            if conflict == "yes" and not row["conflict_fields"]:
                continue
            if conflict == "no" and row["conflict_fields"]:
                continue
            if object_type and object_type not in row["object_types"]:
                continue
            items.append(row)

        sorters = {
            "completeness_desc": lambda row: (-row["completeness_score"], row["label"].casefold()),
            "completeness_asc": lambda row: (row["completeness_score"], row["label"].casefold()),
            "label": lambda row: row["label"].casefold(),
            "sources": lambda row: (-row["source_count"], row["label"].casefold()),
        }
        items.sort(key=sorters.get(sort, sorters["completeness_desc"]))
        start = (page - 1) * page_size
        public_items = [{key: value for key, value in item.items() if key != "search_blob"}
                        for item in items[start:start + page_size]]
        return {
            "items": public_items,
            "total": len(items),
            "page": page,
            "page_size": page_size,
            "facets": {
                "statuses": sorted({row["record_status"] for row in self.rows}),
                "authenticities": sorted({row["authenticity"] for row in self.rows}),
                "next_actions": sorted({row["next_action"] for row in self.rows}),
                "object_types": sorted({value for row in self.rows for value in row["object_types"]}),
            },
        }

    def dossier(self, identity_id):
        summary = self.by_id.get(identity_id)
        if not summary:
            return None
        member_ids = summary["member_ids"]
        placeholders = _placeholders(member_ids)
        with closing(self.connection()) as conn:
            members = _as_dicts(conn.execute(
                "SELECT * FROM objects WHERE id IN (%s) ORDER BY label" % placeholders,
                member_ids,
            ))
            identifiers = _as_dicts(conn.execute(
                "SELECT i.*,s.title source_title,s.url source_url FROM identifiers i "
                "JOIN sources s ON s.id=i.source_id WHERE i.object_id IN (%s) "
                "ORDER BY i.scheme,i.value" % placeholders, member_ids,
            ))
            claims = _as_dicts(conn.execute(
                "SELECT c.*,s.title source_title,s.url source_url,s.citation source_citation "
                "FROM claims c JOIN sources s ON s.id=c.source_id "
                "WHERE c.object_id IN (%s) ORDER BY c.field,c.created_at" % placeholders,
                member_ids,
            ))
            appearances = _as_dicts(conn.execute(
                "SELECT a.id,a.source_id,a.locator,a.title,a.url,a.observed_at,a.description,"
                "l.object_id,l.relation_type,l.confidence,l.rationale,s.title source_title,"
                "s.source_type,s.citation source_citation,s.url source_url,s.access_status,"
                "s.rights_status FROM appearance_object_links l "
                "JOIN appearances a ON a.id=l.appearance_id JOIN sources s ON s.id=a.source_id "
                "WHERE l.object_id IN (%s) AND l.relation_type<>'rejected' "
                "ORDER BY s.issued_year,s.title,a.locator" % placeholders, member_ids,
            ))
            texts = _as_dicts(conn.execute(
                "SELECT t.*,s.title source_title,s.url source_url,s.citation source_citation "
                "FROM texts t JOIN sources s ON s.id=t.source_id "
                "WHERE t.object_id IN (%s) ORDER BY t.text_type,t.created_at" % placeholders,
                member_ids,
            ))
            events = _as_dicts(conn.execute(
                "SELECT e.*,s.title source_title,s.url source_url,s.citation source_citation "
                "FROM events e JOIN sources s ON s.id=e.source_id "
                "WHERE e.object_id IN (%s) ORDER BY coalesce(e.start_date,''),e.event_type" % placeholders,
                member_ids,
            ))
            media = _as_dicts(conn.execute(
                "SELECT m.*,s.title source_title,s.url source_url FROM media m "
                "JOIN sources s ON s.id=m.source_id WHERE m.object_id IN (%s) "
                "ORDER BY m.media_type,m.id" % placeholders, member_ids,
            ))
            text_checks = current_text_reviews(conn)
            rights_checks = current_media_reviews(conn)
            for item in texts:
                check = text_checks.get(item["id"])
                item["proofreading_status"] = check["status"] if check else "not_checked"
                item["proofreading_policy"] = check["editorial_policy"] if check else None
                item["proofreading_review_id"] = check["id"] if check else None
            for item in media:
                check = rights_checks.get(item["id"])
                item["public_reuse_decision"] = check["public_reuse_decision"] if check else "needs_review"
            reviews = _as_dicts(conn.execute(
                "SELECT d.*,oa.label object_a_label,ob.label object_b_label "
                "FROM dedupe_candidates d JOIN objects oa ON oa.id=d.object_a_id "
                "JOIN objects ob ON ob.id=d.object_b_id "
                "WHERE d.object_a_id IN (%s) OR d.object_b_id IN (%s) "
                "ORDER BY d.decided_at DESC,d.score DESC LIMIT 250" % (placeholders, placeholders),
                member_ids + member_ids,
            ))
        public_summary = {key: value for key, value in summary.items() if key != "search_blob"}
        return {
            "summary": public_summary,
            "members": members,
            "identifiers": identifiers,
            "claims": claims,
            "appearances": appearances,
            "texts": texts,
            "events": events,
            "media": media,
            "reviews": reviews,
        }

    def reviews(self, params):
        status = params.get("status", ["unresolved"])[0]
        query = params.get("q", [""])[0].strip().casefold()
        try:
            limit = min(200, max(10, int(params.get("limit", ["50"])[0])))
        except ValueError:
            limit = 50
        predicates = []
        values = []
        if status == "unresolved":
            predicates.append("d.status IN ('pending','insufficient_evidence')")
        elif status in {"pending", "same_object", "different_objects", "insufficient_evidence"}:
            predicates.append("d.status=?")
            values.append(status)
        if query:
            predicates.append("lower(oa.label || ' ' || ob.label || ' ' || d.rationale) LIKE ?")
            values.append("%" + query + "%")
        where = " WHERE " + " AND ".join(predicates) if predicates else ""
        with closing(self.connection()) as conn:
            rows = _as_dicts(conn.execute(
                "SELECT d.*,oa.label object_a_label,ob.label object_b_label "
                "FROM dedupe_candidates d JOIN objects oa ON oa.id=d.object_a_id "
                "JOIN objects ob ON ob.id=d.object_b_id" + where
                + " ORDER BY CASE d.status WHEN 'pending' THEN 0 WHEN 'insufficient_evidence' THEN 1 "
                  "ELSE 2 END,d.score DESC,d.decided_at DESC LIMIT ?",
                values + [limit],
            ))
        for row in rows:
            row["identity_a_id"] = self.member_to_identity.get(row["object_a_id"])
            row["identity_b_id"] = self.member_to_identity.get(row["object_b_id"])
        return {"items": rows, "status": status}

    def review(self, dedupe_id):
        with closing(self.connection()) as conn:
            row = conn.execute(
                "SELECT d.*,oa.label object_a_label,ob.label object_b_label "
                "FROM dedupe_candidates d JOIN objects oa ON oa.id=d.object_a_id "
                "JOIN objects ob ON ob.id=d.object_b_id WHERE d.id=?", (dedupe_id,),
            ).fetchone()
            if not row:
                return None
            item = dict(row)
            item["evidence"] = _as_dicts(conn.execute(
                "SELECT e.*,s.title source_title,s.url source_url FROM dedupe_evidence e "
                "LEFT JOIN sources s ON s.id=e.source_id WHERE e.dedupe_id=? ORDER BY e.id",
                (dedupe_id,),
            ))
        item["identity_a_id"] = self.member_to_identity.get(item["object_a_id"])
        item["identity_b_id"] = self.member_to_identity.get(item["object_b_id"])
        item["identity_a"] = self.dossier(item["identity_a_id"])
        item["identity_b"] = self.dossier(item["identity_b_id"])
        return item

    def decide(self, dedupe_id, status, note):
        if status not in DECISION_STATUSES:
            raise ValueError("Unsupported review decision")
        note = (note or "").strip()
        if len(note) < 12:
            raise ValueError("A concise evidence note of at least 12 characters is required")
        with closing(self.connection()) as conn:
            row = conn.execute(
                "SELECT status FROM dedupe_candidates WHERE id=?", (dedupe_id,)
            ).fetchone()
            if not row:
                return None
            previous = row["status"]
            decided_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute(
                "UPDATE dedupe_candidates SET status=?,decided_at=?,decided_by=? WHERE id=?",
                (status, decided_at, "local research UI", dedupe_id),
            )
            supports = 1 if status == "same_object" else -1 if status == "different_objects" else 0
            conn.execute(
                "INSERT INTO dedupe_evidence "
                "(id,dedupe_id,evidence_type,weight,supports_match,notes) VALUES (?,?,?,?,?,?)",
                (new_id("dedupe_evidence"), dedupe_id, "manual_ui_review", 1.0, supports,
                 "Decision changed from %s to %s. %s" % (previous, status, note)),
            )
            conn.commit()
        self.refresh()
        return self.review(dedupe_id)


def make_handler(catalog, token):
    class ResearchConsoleHandler(BaseHTTPRequestHandler):
        server_version = "IBIResearchConsole/0.1"

        def log_message(self, format, *args):
            print("[%s] %s" % (self.log_date_time_string(), format % args))

        def _headers(self, status, content_type, length=None):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data: https:; connect-src 'self'; frame-ancestors 'none'",
            )
            if length is not None:
                self.send_header("Content-Length", str(length))
            self.end_headers()

        def _json(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self._headers(status, "application/json; charset=utf-8", len(body))
            self.wfile.write(body)

        def _error(self, status, message):
            self._json({"error": message}, status)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = unquote(parsed.path)
            params = parse_qs(parsed.query)
            try:
                if path == "/api/config":
                    self._json({"csrf_token": token, "local_only": True})
                elif path == "/api/stats":
                    self._json(catalog.stats())
                elif path == "/api/identities":
                    self._json(catalog.search(params))
                elif path.startswith("/api/identities/"):
                    result = catalog.dossier(path.rsplit("/", 1)[-1])
                    self._json(result) if result else self._error(404, "Identity not found")
                elif path == "/api/reviews":
                    self._json(catalog.reviews(params))
                elif path.startswith("/api/reviews/"):
                    result = catalog.review(path.rsplit("/", 1)[-1])
                    self._json(result) if result else self._error(404, "Review not found")
                elif path.startswith("/api/"):
                    self._error(404, "API route not found")
                else:
                    self._static(path)
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as exc:
                self._error(500, str(exc))

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path != "/api/refresh" and not parsed.path.startswith("/api/reviews/"):
                self._error(404, "API route not found")
                return
            if self.headers.get("X-IBI-Token") != token:
                self._error(403, "Missing or invalid local review token")
                return
            if "application/json" not in self.headers.get("Content-Type", ""):
                self._error(415, "Review actions require JSON")
                return
            try:
                length = min(int(self.headers.get("Content-Length", "0")), 16384)
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if parsed.path == "/api/refresh":
                    catalog.refresh()
                    self._json(catalog.stats())
                    return
                result = catalog.decide(
                    unquote(parsed.path.rsplit("/", 1)[-1]),
                    payload.get("status", ""), payload.get("note", ""),
                )
                self._json(result) if result else self._error(404, "Review not found")
            except (ValueError, json.JSONDecodeError) as exc:
                self._error(400, str(exc))
            except Exception as exc:
                self._error(500, str(exc))

        def _static(self, path):
            relative = "index.html" if path in ("", "/") else path.lstrip("/")
            candidate = (WEB_ROOT / relative).resolve()
            if WEB_ROOT.resolve() not in candidate.parents and candidate != WEB_ROOT.resolve():
                self._error(404, "Not found")
                return
            if not candidate.is_file():
                candidate = WEB_ROOT / "index.html"
            body = candidate.read_bytes()
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
                content_type += "; charset=utf-8"
            self._headers(200, content_type, len(body))
            self.wfile.write(body)

    return ResearchConsoleHandler


def serve(database, host="127.0.0.1", port=8765):
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("The private research console may only bind to localhost")
    catalog = CorpusCatalog(database)
    token = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer((host, port), make_handler(catalog, token))
    print("Incantation Bowl Index research console: http://%s:%s" % server.server_address)
    print("Private corpus: %s identities; localhost only" % len(catalog.rows))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
