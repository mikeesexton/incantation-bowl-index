# Identity and enrichment status

## Identity review

- Working physical identity hypotheses (all statuses): **1846**
- Multi-record identity clusters: **219**
- Underlying source records (all identities): **2195**
- Pending dedupe decisions: **0**

## Identity-level coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 1288 | 69.8% |
| Provenance | 375 | 20.3% |
| Dating | 484 | 26.2% |
| Dimensions | 670 | 36.3% |
| Material | 410 | 22.2% |
| Language | 1029 | 55.7% |
| Script | 94 | 5.1% |
| Text Edition | 519 | 28.1% |
| Translation | 538 | 29.1% |
| Image | 614 | 33.3% |

## Completeness distribution

| Core fields present | Identities |
|---|---:|
| 0–2 of 10 | 585 |
| 3–5 of 10 | 944 |
| 6–8 of 10 | 303 |
| 9–10 of 10 | 14 |

## Next-action queue

| Next action | Identities |
|---|---:|
| Location | 558 |
| Provenance | 1005 |
| Dating | 68 |
| Dimensions | 139 |
| Material | 23 |
| Language | 7 |
| Script | 43 |
| Text Edition | 2 |
| Rights Review | 1 |

## Claim conflicts

**533** identities triggered raw difference flags. Current reviews support **568** compatible field-level instances and **16** substantive instances. **602** instances require review or revalidation; these are not established contradictions. No source claim or historical decision was deleted.

## Recommended private research UI

A local read-only-first interface is justified now because the current generated identity-review queue is clear and the bottleneck has shifted to inspecting claims and filling gaps. Its first release should have four views:

1. **Identity search:** full-text search across labels, accessions, publication sigla, owners, clients, and sources; faceted by location, script/language, authenticity, record status, and completeness.
2. **Identity dossier:** one page per probable physical bowl showing all member records, identifiers, appearances, claims grouped by field and source, texts, media, events, rights, and conflicts.
3. **Review workbench:** side-by-side identity comparison with reversible same/different/insufficient decisions and recorded evidence.
4. **Enrichment queue:** filters for missing fields, blocked sources, conflicts, rights review, and recently changed museum or auction appearances.

The private UI should write only through validated review/enrichment actions and keep the SQLite database on localhost. The eventual public dashboard can reuse the identity dossier and facets against reviewed, rights-safe exports.
