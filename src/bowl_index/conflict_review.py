"""Conservative review validity: bind decisions to the evidence actually inspected."""

import json
import hashlib
import unicodedata


EVIDENCE_FIELDS = (
    "id", "object_id", "source_id", "field", "value_text", "value_json",
    "normalized_value", "certainty", "locator", "source_title", "source_url",
)


def evidence_fingerprint(member_ids, claims):
    """Digest a complete field snapshot, independent of query ordering."""
    payload = {"member_ids": sorted(member_ids), "claims": sorted(
        [{key: claim[key] for key in EVIDENCE_FIELDS} for claim in claims],
        key=lambda row: row["id"],
    )}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


def _canonical(value):
    # Preserve digits, units, qualifiers, negation, and non-Latin writing.
    return " ".join(unicodedata.normalize("NFC", value or "").casefold().split())


def _safe_classification(field_group, values_by_field):
    values = {_canonical(v) for group in values_by_field.values() for v in group if v}
    if len(values) == 1:
        return "compatible", "equivalent_wording", "Values differ only in case or whitespace."
    if field_group == "location":
        aliases = (
            {"the british museum", "british museum", "british museum, london"},
            {"penn museum", "university of pennsylvania museum",
             "university of pennsylvania museum of archaeology and anthropology"},
        )
        if values and any(values <= group for group in aliases):
            return "compatible", "institution_name_variant", "Exact documented institution-name variants."
    return "unresolved", "no_safe_rule", "The values require source-level review."


def review_is_current(review, member_ids, claims):
    """Legacy decisions remain in the ledger but cannot hide changed or unsafe evidence."""
    if not review:
        return False
    try:
        details = json.loads(review["details_json"])
        if sorted(details["member_ids"]) != sorted(member_ids):
            return False
        def signature(rows):
            return sorted(
                json.dumps({key: row[key] for key in EVIDENCE_FIELDS},
                           ensure_ascii=False, sort_keys=True)
                for row in rows
            )
        if signature(details["claim_evidence"]) != signature(claims):
            return False
    except (KeyError, TypeError, ValueError):
        return False
    if review["disposition"] == "compatible" and review["review_method"] != "checked_override":
        values_by_field = {}
        for claim in claims:
            value = claim["normalized_value"] or claim["value_text"] or claim["value_json"]
            if value:
                values_by_field.setdefault(claim["field"], set()).add(value)
        return _safe_classification(review["field_group"], values_by_field)[0] == "compatible"
    return True
