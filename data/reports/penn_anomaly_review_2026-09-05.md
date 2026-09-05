# Penn anomaly review: Montgomery reference cohort

Reviewed: `2026-09-05T19:24:04+00:00`

## Outcome

- All nine newly exposed core-field differences now have current, evidence-bound decisions.
- Seven dimension pairs remain unresolved because Penn reports **Outside Diameter** while Montgomery reports **Diameter**, and the consulted evidence does not document remeasurement, rounding, restoration effects or equivalence of convention.
- Penn's **Hebrew Language** labels for B9010 / Montgomery 9 and B9008 / Montgomery 31 remain unresolved against the edition-based Jewish Babylonian Aramaic and Syriac claims. The latter has a second independent Syriac attribution. Original-script review is required before assigning a source error.
- Five directed relationship assertions now preserve Penn's `Duplicate of`, `Same as` and `Part of` notes. One explicit physical-part assertion is accepted; four relationship scopes remain unresolved. No object identities were merged.
- Montgomery's dating discussion was reviewed at section 14, printed pages 103–105 (PDF pages 109–111). It places the Nippur group in the late pre-Islamic period, no later than the sixth or beginning of the seventh century, with an archaeological terminus near 600 CE. This is stored as `dating_context` for B2963 / text 3 and is not treated as an object-specific replacement for Penn's reported `ca. 200 BCE`.

## Relationship findings

| Subject | Source wording | Target | Stored interpretation |
|---|---|---|---|
| B16007 | `Duplicate of16081` | B16081 | Directed duplicate assertion; scope unresolved |
| B16086 | `Same as B16062\B6354` | B16062 | Directed same-as assertion; scope unresolved |
| B16086 | `Same as B16062\B6354` | B6354 | Directed same-as assertion; scope unresolved |
| B16062 | `Same as B16086` | B16086 | Reciprocal same-as assertion; scope unresolved |
| B6354 | `Part of B6353, 6355, 6356, 6357, 6358, 6359, 16062` | B16062 | Physical-part assertion accepted as reported |

B16007 is described with 17 inscription lines and 12 joined fragments, while B16081 has 11 lines and 4 fragments. That difference makes a physical-identity merge unsafe without clearer catalogue or object evidence. B16062 reciprocates B16086's same-as wording, and B6354 documents a fragment-group relationship, but these facts still do not define the scope of Penn's `Same as` label.

## Audit trail

- Field decisions: `research/reviews/penn_field_conflicts_2026-09-05.json`
- Relationship decisions: `research/reviews/penn_object_relationships_2026-09-05.json`
- Dating context ingest: `research/enrichment/montgomery_text3_dating_context_2026-09-05.jsonl`
- Follow-up state: `research/reviews/penn_concordance_followups_2026-09-05.jsonl`

Both checked importers replay as no-ops. The relationship ledger is append-only and the field decisions remain bound to exact claim evidence. The work changed no identity decisions and deleted no source claims.
