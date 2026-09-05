import json
import re

from .ids import new_id


NLI_DIMENSIONS = re.compile(
    r"גובה:\s*(\d+)\s*מ(?:[\"״']?מ)?\s*,\s*הקף:\s*(\d+)\s*מ(?:[\"״']?מ)?"
)


def derive_normalized_dimensions(conn):
    """Add queryable dimensions while preserving NLI's ambiguous Hebrew label.

    The second catalogue measure is deliberately not translated as diameter or
    circumference. Its original label (הקף) is retained in both text and JSON.
    """
    rows = conn.execute(
        "SELECT id,object_id,appearance_id,source_id,value_text,certainty,locator "
        "FROM claims WHERE field='dimensions_source_text' ORDER BY id"
    ).fetchall()
    inserted = 0
    for row in rows:
        match = NLI_DIMENSIONS.search(row["value_text"])
        if not match:
            continue
        value_json = json.dumps(
            {
                "height_mm": int(match.group(1)),
                "source_second_measure_label": "הקף",
                "source_second_measure_mm": int(match.group(2)),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        value_text = "Height %s mm; source field ‘הקף’ %s mm" % match.groups()
        if conn.execute(
            "SELECT 1 FROM claims WHERE object_id=? AND source_id=? AND field='dimensions' "
            "AND value_json=?",
            (row["object_id"], row["source_id"], value_json),
        ).fetchone():
            continue
        conn.execute(
            "INSERT INTO claims "
            "(id,object_id,appearance_id,source_id,field,value_text,value_json,certainty,"
            "locator,notes,supersedes_claim_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                new_id("claim"), row["object_id"], row["appearance_id"], row["source_id"],
                "dimensions", value_text, value_json, row["certainty"], row["locator"],
                "Derived from the preserved NLI source string without interpreting the "
                "ambiguous second-measure label.",
                row["id"],
            ),
        )
        inserted += 1
    conn.commit()
    return inserted


def run_source_preserving_enrichment(conn):
    return {"normalized_dimensions_added": derive_normalized_dimensions(conn)}
