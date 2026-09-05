# Evidence-bound conflict review

Use `ibi triage-conflicts PATH` with a version 2 manifest for a reviewed subset. Count-only legacy overrides are rejected, and legacy bulk triage cannot overwrite checked decisions.

Each manifest has `schema_version: 2`, a named `reviewed_by`, a UTC ISO 8601 `reviewed_at`, and an `entries` array. Each entry must have:

- `identity_id` and `field_group` identifying a currently flagged field.
- `evidence_sha256` from `evidence_fingerprint(instance["member_ids"], instance["claims"])`, using `conflict_instances(conn)`.
- `disposition`, `rationale`, and `review_basis` stating exactly what was inspected and its limits.
- Optional `supporting_references` pointing to source pages, captures, or local manifests.

Use the [three-bowl manifest](../research/reviews/bm_three_bowl_revalidation_2026-09-04.json) as a complete example. Its `inspected_evidence` records the readable snapshot; the digest is checked against the database, not trusted merely because this copy exists. Explicitly distinguish stored-claim comparison from fresh primary-source verification. A compatible decision does not validate a physical measurement, identity merge, provenance history, or source accuracy.

The loader obtains a write transaction before reading current evidence, validates the entire subset before writing, and rejects missing/duplicate conflicts and changed evidence. It only changes listed reviews. An identical replay does not write another history row. To reconsider a decision on unchanged evidence, submit a new reviewed rationale and timestamp; this creates a new historical snapshot.

Migration 005 snapshots all existing decisions before any changes and records every subsequent insert or update. SQL triggers prohibit updates/deletions of history and deletions of current reviews. Supersede a decision through a new review. SQLite remains a local research database, not a tamper-proof security boundary against someone with administrative file access.

A review is effective only while the recorded cluster membership and claim evidence remain current. Changes to claim values, certainty, locators, or cited source titles/URLs reopen review. A fingerprint detects drift; it cannot certify that a research judgment is correct.

Before a production migration or substantial review batch, use SQLite's backup API to make a consistent private backup. After application, regenerate the roadmap, conflict report, enrichment report, and a private export. Public release remains blocked on the separate media and text review policy.
