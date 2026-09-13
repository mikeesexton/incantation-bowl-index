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


# Facets where a clean disagreement is genuine evidence that two records describe
# different objects. These are properties of the physical bowl: where it is, how big
# it is, what it is made of, what is written on it and who is named.
#
# Everything else in COVERAGE_GROUPS is corroborating-only. `publication` is the
# instructive case: two records of the same bowl routinely cite different
# publications, because that is what separate sources do. Counting that as a
# conflict marks genuine duplicates as suspect. Agreement on a corroborating facet
# still counts in favour; disagreement simply says nothing either way.
#
# `biblical_intertexts` is deliberately corroborating-only for the same reason —
# sources list subsets of the verses on a bowl, so two disjoint lists are not a
# contradiction. A shared verse is still real evidence: MS 1927/64 was confirmed
# that way, its context citation naming Zech 3:2 and the archive record listing it
# for JBA 5, the only bowl among JBA 1-64 carrying that verse.
IDENTITY_DISCRIMINATING_GROUPS = frozenset({
    "location", "provenance", "dating", "dimensions", "material",
    "language", "script", "vessel_form", "text_form", "client",
})

# Long and short forms of one collection name, which compare as different strings
# and are not separated by stripping a definite article alone.
_COLLECTION_NAME_FORMS = {
    "frau professor hilprecht collection of babylonian antiquities, jena":
        "frau professor hilprecht collection, jena",
    "frau professor hilprecht collection, friedrich schiller university jena":
        "frau professor hilprecht collection, jena",
    "vorderasiatisches museum, berlin": "vorderasiatisches museum",
    "penn museum, philadelphia": "penn museum",
    "university of pennsylvania museum": "penn museum",
}


def normalize_claim_value(group, value):
    """Compare claim values as values, not as strings.

    "The Schøyen Collection" and "Schøyen Collection" are one collection. Twenty-one
    of the seventy-seven pairs reviewed on 13 September 2026 looked like conflicts
    for no better reason than a definite article.
    """
    text = unicodedata.normalize("NFC", str(value or "")).strip().casefold().rstrip(".")
    text = re.sub(r"^the\s+", "", text)
    text = re.sub(r"\s+", " ", text)
    if group == "location":
        text = _COLLECTION_NAME_FORMS.get(text, text)
    return text


def _compatible(group, values_a, values_b):
    """Whether two sets of values for one facet can describe the same object."""
    if values_a & values_b:
        return True
    if group == "language":
        # One attribution refining another is not a contradiction. "Jewish Babylonian
        # Aramaic and/or Hebrew" and "Jewish Babylonian Aramaic with some Mandaic
        # features" both extend a base reading that a second source states plainly.
        # Matching on a prefix rather than any substring keeps that narrow: it admits
        # a qualifier appended to a shared reading, and still separates "Syriac" from
        # "Hebrew Language", which is a real disagreement for a reviewer to settle.
        return any(
            x.startswith(y) or y.startswith(x)
            for x in values_a for y in values_b
        )
    return False


def _claims_by_group(conn, object_id):
    # Imported here rather than at module scope: identity imports this module, so a
    # module-level import would close the cycle.
    from .identity import COVERAGE_GROUPS

    field_to_group = {f: g for g, fields in COVERAGE_GROUPS.items() for f in fields}
    grouped = {}
    for row in conn.execute(
        "SELECT field,value_text,normalized_value FROM claims WHERE object_id=?", (object_id,)
    ):
        group = field_to_group.get(row["field"])
        if group is None:
            continue
        value = normalize_claim_value(group, row["normalized_value"] or row["value_text"])
        if value:
            grouped.setdefault(group, set()).add(value)
    return grouped


def pair_evidence(conn, object_a_id, object_b_id):
    """What the stored claims say about whether two records are one object.

    Compares by coverage group rather than by field name. `current_location` and
    `current_or_reported_collection` carry the same fact under different names, as do
    the four spellings of the biblical-quotation field and the three of client;
    comparing raw field names reports two records as having nothing in common when
    they in fact agree.

    Returns agreeing and conflicting group names and the resulting band. This is
    evidence for a reviewer, never a decision: an exact identifier is strong evidence,
    not a merge instruction, and `no_overlap` means the records are silent about each
    other rather than that they disagree.
    """
    a, b = _claims_by_group(conn, object_a_id), _claims_by_group(conn, object_b_id)
    shared = set(a) & set(b)
    agreeing = sorted(g for g in shared if _compatible(g, a[g], b[g]))
    conflicting = sorted(
        g for g in shared
        if not _compatible(g, a[g], b[g]) and g in IDENTITY_DISCRIMINATING_GROUPS
    )
    differing_non_discriminating = sorted(
        g for g in shared
        if not _compatible(g, a[g], b[g]) and g not in IDENTITY_DISCRIMINATING_GROUPS
    )
    band = "conflict" if conflicting else ("corroborated" if agreeing else "no_overlap")
    return {
        "band": band,
        "agreeing_groups": agreeing,
        "conflicting_groups": conflicting,
        "differing_non_discriminating_groups": differing_non_discriminating,
        "groups_on_one_side_only": sorted(set(a) ^ set(b)),
    }
