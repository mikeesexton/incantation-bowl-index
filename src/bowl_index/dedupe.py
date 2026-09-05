import re
import unicodedata
from difflib import SequenceMatcher

from .ids import new_id


UNIQUE_IDENTIFIER_SCOPES = (
    ("National Library of Israel", "NLI MMS ID"),
    ("National Library of Israel", "NLI bowl number"),
    ("The British Museum", "British Museum object key"),
    ("The British Museum", "British Museum museum number"),
    ("The British Museum", "British Museum registration URL value"),
    ("Penn Museum", "Penn web object ID"),
    ("USC Digital Library", "DOI dataset"),
    ("USC Digital Library", "USC Digital Library asset"),
    ("The Metropolitan Museum of Art", "Met object ID"),
    ("The Schøyen Collection", "collection designation"),
    ("Hilprecht Collection", "collection designation"),
    ("State Hermitage Museum", "collection designation"),
    ("Ābgīne Museum, Tehran", "collection designation"),
    ("Nippur excavations", "field number"),
    ("Iraq Museum", "collection designation"),
    ("Yale Babylonian Collection", "collection designation"),
    ("British Museum", "British Museum museum number"),
    ("Royal Ontario Museum", "collection designation"),
    ("Staatliche Museen zu Berlin", "museum object ID"),
    ("Vorderasiatisches Museum", "collection designation"),
    ("Apollo Art Auctions", "auction lot component key"),
    ("Apollo Art Auctions via LiveAuctioneers", "auction lot component number"),
)

NAMESPACED_IDENTIFIER_SCOPES = (
    ("As reported by Apotropaic Arts", "collection designation", "designation_prefix"),
    ("Source-scoped concordance", "publication object key", "double_colon"),
    ("Ford and Morgenstern", "publication object key", "double_colon"),
)

DISTINCT_ENUMERATION_SOURCES = {
    "The Bible in the Bowls: A Catalogue of Biblical Quotations in Published Jewish Babylonian Aramaic Magic Bowls": (
        "Separate rows in Waller's catalogue denote separate published bowl entries; shared canonical "
        "identifiers were resolved before this rule."
    ),
    "Index of Aramaic Incantation Bowls": (
        "Separate index entries are distinct unless the index supplies a concordance; explicit "
        "concordances were resolved before this rule."
    ),
    "Apollo Art Auctions catalogue 10068": "The catalogue describes separate lots or physical components.",
    "The Ancient Items at the Library: Magical Bowls of Babylonian Jewry": (
        "The source explicitly describes seven distinct donated bowls."
    ),
    "Aramaic Incantation Bowls Project": "The source explicitly describes four distinct project bowls.",
    "Archaeological Center Auction 57": "The catalogue assigns these objects separate lots.",
    "Mandaic Magic Bowls in the Moussaieff Collection: A Preliminary Survey": (
        "The survey enumerates these as separate physical bowls."
    ),
    "Working List of Syriac ‘Manichaean’ Incantation Bowls": (
        "The working list assigns separate object designations."
    ),
    "Who Wrote the Incantation Bowls?": "The source identifies separate collection objects.",
}


def _identifiers(conn, object_id):
    return {
        (row["scheme"].casefold(), row["normalized_value"].casefold())
        for row in conn.execute(
            "SELECT scheme, normalized_value FROM identifiers WHERE object_id=? "
            "AND lower(scheme) NOT IN ('bibliographic concordance', "
            "'brand 2021 working-list number', 'montgomery 1913 text number', "
            "'segal 2000 text number')",
            (object_id,),
        )
    }


def _unique_identifier_map(conn):
    allowed = {(body.casefold(), scheme.casefold()) for body, scheme in UNIQUE_IDENTIFIER_SCOPES}
    result = {}
    for row in conn.execute(
        "SELECT object_id,assigning_body,scheme,normalized_value FROM identifiers "
        "WHERE assigning_body IS NOT NULL"
    ):
        scope = (row["assigning_body"].casefold(), row["scheme"].casefold())
        if scope in allowed:
            result.setdefault(row["object_id"], {}).setdefault(scope, set()).add(
                row["normalized_value"].casefold()
            )
    return result


def _identifier_namespace(value, mode):
    value = value.casefold().strip()
    if mode == "double_colon":
        head, separator, _ = value.partition("::")
        return head if separator else None
    if mode == "designation_prefix":
        compact = re.sub(r"[\s._-]+", "", value)
        match = re.match(r"^([a-zà-öø-ÿ]+(?:\d+/)?)", compact)
        return match.group(1) if match else None
    return None


def _concordance_key(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(character for character in value if character.isalnum())
    penn_legacy = re.fullmatch(r"b0*(\d+)", value)
    if penn_legacy:
        return "cbs" + penn_legacy.group(1)
    return value


def _identity_roots(conn):
    object_ids = [row[0] for row in conn.execute("SELECT id FROM objects")]
    parent = {object_id: object_id for object_id in object_ids}

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first, second):
        root_first, root_second = find(first), find(second)
        if root_first != root_second:
            parent[max(root_first, root_second)] = min(root_first, root_second)

    for row in conn.execute(
        "SELECT object_a_id,object_b_id FROM dedupe_candidates WHERE status='same_object'"
    ):
        union(row["object_a_id"], row["object_b_id"])
    return {object_id: find(object_id) for object_id in object_ids}


def _namespaced_identifier_map(conn):
    allowed = {
        (body.casefold(), scheme.casefold()): mode
        for body, scheme, mode in NAMESPACED_IDENTIFIER_SCOPES
    }
    result = {}
    for row in conn.execute(
        "SELECT object_id,assigning_body,scheme,normalized_value FROM identifiers "
        "WHERE assigning_body IS NOT NULL"
    ):
        scope = (row["assigning_body"].casefold(), row["scheme"].casefold())
        mode = allowed.get(scope)
        if not mode:
            continue
        namespace = _identifier_namespace(row["normalized_value"], mode)
        if namespace:
            result.setdefault(row["object_id"], {}).setdefault(
                (scope[0], scope[1], namespace), set()
            ).add(row["normalized_value"].casefold())
    return result


def _unique_identifier_conflict(
    unique_map, object_a_id, object_b_id, namespaced_map=None
):
    identifiers_a = unique_map.get(object_a_id, {})
    identifiers_b = unique_map.get(object_b_id, {})
    for body, scheme in UNIQUE_IDENTIFIER_SCOPES:
        scope = (body.casefold(), scheme.casefold())
        values_a = identifiers_a.get(scope)
        values_b = identifiers_b.get(scope)
        if values_a and values_b and values_a.isdisjoint(values_b):
            return body, scheme, sorted(values_a), sorted(values_b)
    namespaces_a = (namespaced_map or {}).get(object_a_id, {})
    namespaces_b = (namespaced_map or {}).get(object_b_id, {})
    for scope in sorted(set(namespaces_a) & set(namespaces_b)):
        values_a = namespaces_a[scope]
        values_b = namespaces_b[scope]
        if values_a.isdisjoint(values_b):
            body, scheme, namespace = scope
            return body, "%s namespace %s" % (scheme, namespace), sorted(values_a), sorted(values_b)
    return None


def score_pair(conn, object_a_id, object_b_id):
    a = conn.execute("SELECT * FROM objects WHERE id=?", (object_a_id,)).fetchone()
    b = conn.execute("SELECT * FROM objects WHERE id=?", (object_b_id,)).fetchone()
    if not a or not b:
        raise ValueError("both objects must exist")
    ids_a, ids_b = _identifiers(conn, object_a_id), _identifiers(conn, object_b_id)
    exact_ids = ids_a & ids_b
    if exact_ids:
        return 0.99, "exact_identifier", "Shared identifier(s): %s" % sorted(exact_ids)
    label_score = SequenceMatcher(None, a["label"].casefold(), b["label"].casefold()).ratio()
    return round(label_score * 0.55, 4), "label_similarity", "Label similarity %.3f; review required" % label_score


def queue_all(conn, threshold=0.35):
    objects = conn.execute(
        "SELECT id,label FROM objects WHERE record_status <> 'merged' ORDER BY id"
    ).fetchall()
    unique_map = _unique_identifier_map(conn)
    namespaced_map = _namespaced_identifier_map(conn)
    queued = 0
    # Exact identifier matches can be generated set-wise. This keeps discovery
    # sweeps fast as the corpus grows into thousands of records.
    weak = (
        "bibliographic concordance", "brand 2021 working-list number",
        "montgomery 1913 text number", "segal 2000 text number",
    )
    exact_pairs = conn.execute(
        "SELECT DISTINCT i1.object_id AS object_a_id,i2.object_id AS object_b_id,"
        "i1.scheme,i1.normalized_value FROM identifiers i1 JOIN identifiers i2 "
        "ON lower(i1.scheme)=lower(i2.scheme) AND lower(i1.normalized_value)=lower(i2.normalized_value) "
        "AND i1.object_id < i2.object_id JOIN objects a ON a.id=i1.object_id "
        "JOIN objects b ON b.id=i2.object_id WHERE a.record_status<>'merged' "
        "AND b.record_status<>'merged' AND lower(i1.scheme) NOT IN (?,?,?,?)",
        weak,
    ).fetchall()
    for pair in exact_pairs:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO dedupe_candidates "
            "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
            (
                new_id("dedupe"), pair["object_a_id"], pair["object_b_id"], 0.99,
                "exact_identifier", "Shared identifier: %s=%s" % (
                    pair["scheme"], pair["normalized_value"]
                ),
            ),
        )
        queued += int(cursor.rowcount > 0)
    # Label-only similarity never reaches more than 0.55, so skip the O(n²)
    # fuzzy pass when the requested threshold cannot possibly admit a pair.
    if threshold > 0.55:
        conn.commit()
        return queued
    # The fuzzy pass intentionally uses labels only and is preloaded in memory.
    # Calling score_pair for every pair would issue millions of tiny identifier
    # queries on a discovery-sized corpus even though exact identifiers were
    # already handled set-wise above.
    for index, object_a in enumerate(objects):
        for object_b in objects[index + 1:]:
            if _unique_identifier_conflict(
                unique_map, object_a["id"], object_b["id"], namespaced_map
            ):
                continue
            label_score = SequenceMatcher(
                None, object_a["label"].casefold(), object_b["label"].casefold()
            ).ratio()
            score = round(label_score * 0.55, 4)
            if score < threshold:
                continue
            cursor = conn.execute(
                "INSERT OR IGNORE INTO dedupe_candidates "
                "(id,object_a_id,object_b_id,score,method,rationale) VALUES (?,?,?,?,?,?)",
                (
                    new_id("dedupe"), object_a["id"], object_b["id"], score,
                    "label_similarity", "Label similarity %.3f; review required" % label_score,
                ),
            )
            queued += int(cursor.rowcount > 0)
    conn.commit()
    return queued


def adjudicate_conflicting_unique_identifiers(
    conn, decided_by="automated unique-identifier conflict rule"
):
    """Reject fuzzy matches with different IDs in a documented unique namespace.

    The allowlist is intentionally limited to stable record IDs whose issuing
    institutions use one value per catalogue object. Generic collection and
    publication designations are excluded because aliases and composites are
    common in incantation-bowl scholarship.
    """
    unique_map = _unique_identifier_map(conn)
    namespaced_map = _namespaced_identifier_map(conn)
    rows = conn.execute(
        "SELECT id,object_a_id,object_b_id FROM dedupe_candidates "
        "WHERE status='pending' AND method='label_similarity' ORDER BY id"
    ).fetchall()
    adjudicated = 0
    for row in rows:
        conflict = _unique_identifier_conflict(
            unique_map, row["object_a_id"], row["object_b_id"], namespaced_map
        )
        if not conflict:
            continue
        body, scheme, values_a, values_b = conflict
        conn.execute(
            "UPDATE dedupe_candidates SET status='different_objects',"
            "decided_at=CURRENT_TIMESTAMP,decided_by=? WHERE id=?",
            (decided_by, row["id"]),
        )
        conn.execute(
            "INSERT INTO dedupe_evidence "
            "(id,dedupe_id,evidence_type,value_a,value_b,weight,supports_match,notes) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                new_id("dedupe_evidence"), row["id"], "conflicting_unique_identifier",
                " | ".join(values_a), " | ".join(values_b), 1.0, -1,
                "%s assigns distinct %s values to these records." % (body, scheme),
            ),
        )
        adjudicated += 1
    conn.commit()
    return adjudicated


def adjudicate_explicit_concordances(
    conn, decided_by="automated unambiguous explicit-concordance rule"
):
    """Resolve cross-scheme aliases explicitly reported by a source.

    A concordance is accepted only when all records using the alias and all
    records bearing the target designation each collapse to one already-known
    identity component. Ambiguous aliases such as the printed CBS 2972 conflict
    therefore remain unresolved.
    """
    roots = _identity_roots(conn)
    bibliography = {}
    targets = {}
    for row in conn.execute(
        "SELECT object_id,scheme,value FROM identifiers WHERE lower(scheme) IN "
        "('bibliographic concordance','collection designation','waller 2022 table designation')"
    ):
        key = _concordance_key(row["value"])
        if not key:
            continue
        destination = (
            bibliography if row["scheme"].casefold() == "bibliographic concordance" else targets
        )
        destination.setdefault(key, set()).add(row["object_id"])

    adjudicated = 0
    for key in sorted(set(bibliography) & set(targets)):
        source_objects = bibliography[key]
        target_objects = targets[key]
        source_roots = {roots[object_id] for object_id in source_objects}
        target_roots = {roots[object_id] for object_id in target_objects}
        if len(source_roots) != 1 or len(target_roots) != 1 or source_roots == target_roots:
            continue
        object_a_id, object_b_id = sorted((min(source_objects), min(target_objects)))
        existing = conn.execute(
            "SELECT id,status FROM dedupe_candidates WHERE object_a_id=? AND object_b_id=?",
            (object_a_id, object_b_id),
        ).fetchone()
        if existing and existing["status"] not in ("pending", "same_object"):
            continue
        if existing and existing["status"] == "same_object":
            continue
        if existing:
            dedupe_id = existing["id"]
            conn.execute(
                "UPDATE dedupe_candidates SET score=.95,method='explicit_concordance',"
                "rationale=?,status='same_object',decided_at=CURRENT_TIMESTAMP,decided_by=? "
                "WHERE id=?",
                ("Unambiguous cross-scheme concordance: %s" % key, decided_by, dedupe_id),
            )
        else:
            dedupe_id = new_id("dedupe")
            conn.execute(
                "INSERT INTO dedupe_candidates "
                "(id,object_a_id,object_b_id,score,status,method,rationale,decided_at,decided_by) "
                "VALUES (?,?,?,?,?,'explicit_concordance',?,CURRENT_TIMESTAMP,?)",
                (
                    dedupe_id, object_a_id, object_b_id, .95, "same_object",
                    "Unambiguous cross-scheme concordance: %s" % key, decided_by,
                ),
            )
        conn.execute(
            "INSERT INTO dedupe_evidence "
            "(id,dedupe_id,evidence_type,value_a,value_b,weight,supports_match,notes) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                new_id("dedupe_evidence"), dedupe_id, "explicit_bibliographic_concordance",
                key, key, .95, 1,
                "A source-attributed bibliographic concordance matches an object designation; "
                "both sides are unambiguous after existing identity components are collapsed.",
            ),
        )
        adjudicated += 1
    conn.commit()
    return adjudicated


def adjudicate_distinct_enumerated_source_items(
    conn, decided_by="automated reviewed-enumeration rule"
):
    """Reject label matches between distinct items in reviewed enumerations."""
    rows = conn.execute(
        "SELECT d.id,s.id AS source_id,s.title FROM dedupe_candidates d "
        "JOIN appearance_object_links la ON la.object_id=d.object_a_id "
        "JOIN appearances aa ON aa.id=la.appearance_id "
        "JOIN appearance_object_links lb ON lb.object_id=d.object_b_id "
        "JOIN appearances ab ON ab.id=lb.appearance_id AND ab.source_id=aa.source_id "
        "JOIN sources s ON s.id=aa.source_id "
        "WHERE d.status='pending' AND la.relation_type<>'rejected' "
        "AND lb.relation_type<>'rejected' ORDER BY d.id,s.id"
    ).fetchall()
    matches = {}
    for row in rows:
        if row["title"] in DISTINCT_ENUMERATION_SOURCES:
            matches.setdefault(row["id"], row)
    for dedupe_id, row in matches.items():
        rationale = DISTINCT_ENUMERATION_SOURCES[row["title"]]
        conn.execute(
            "UPDATE dedupe_candidates SET status='different_objects',"
            "decided_at=CURRENT_TIMESTAMP,decided_by=? WHERE id=?",
            (decided_by, dedupe_id),
        )
        conn.execute(
            "INSERT INTO dedupe_evidence "
            "(id,dedupe_id,evidence_type,value_a,value_b,weight,supports_match,source_id,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                new_id("dedupe_evidence"), dedupe_id, "distinct_enumerated_item",
                row["title"], row["title"], 1.0, -1, row["source_id"], rationale,
            ),
        )
    conn.commit()
    return len(matches)


def adjudicate_exact_identifiers(conn, decided_by="automated exact-identifier rule"):
    """Resolve only source-scoped or institutional exact identifier matches.

    Weak bibliography/list-number schemes are excluded when pairs are created,
    so this operation is deliberately narrower than generic fuzzy adjudication.
    It records evidence and never rewrites or deletes either object record.
    """
    rows = conn.execute(
        "SELECT * FROM dedupe_candidates WHERE status='pending' AND method='exact_identifier'"
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE dedupe_candidates SET status='same_object',decided_at=CURRENT_TIMESTAMP,"
            "decided_by=? WHERE id=?", (decided_by, row["id"]),
        )
        conn.execute(
            "INSERT INTO dedupe_evidence "
            "(id,dedupe_id,evidence_type,value_a,value_b,weight,supports_match,notes) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                new_id("dedupe_evidence"), row["id"], "exact_identifier",
                row["rationale"], row["rationale"], 1.0, 1,
                "Automatically adjudicated from an exact strong identifier; records retained separately.",
            ),
        )
    conn.commit()
    return len(rows)
