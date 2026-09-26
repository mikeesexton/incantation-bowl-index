# Identity and enrichment status

## Identity review

- Working physical identity hypotheses (all statuses): **1736**
- Multi-record identity clusters: **200**
- Underlying source records (all identities): **2053**
- Pending dedupe decisions: **0**

## Identity-level coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 1289 | 74.3% |
| Provenance | 371 | 21.4% |
| Dating | 484 | 27.9% |
| Dimensions | 460 | 26.5% |
| Material | 410 | 23.6% |
| Language | 1041 | 60.0% |
| Script | 94 | 5.4% |
| Text Edition | 17 | 1.0% |
| Translation | 71 | 4.1% |
| Image | 330 | 19.0% |

## Completeness distribution

| Core fields present | Identities |
|---|---:|
| 0–2 of 10 | 811 |
| 3–5 of 10 | 809 |
| 6–8 of 10 | 115 |
| 9–10 of 10 | 1 |

## Next-action queue

| Next action | Identities |
|---|---:|
| Location | 447 |
| Provenance | 1011 |
| Dating | 63 |
| Dimensions | 139 |
| Material | 23 |
| Language | 7 |
| Script | 43 |
| Text Edition | 3 |

## Claim conflicts

**425** identities triggered raw difference flags. Current reviews support **626** compatible field-level instances and **18** substantive instances. **48** instances require review or revalidation; these are not established contradictions. No source claim or historical decision was deleted.

## Recommended private research UI

A local read-only-first interface is justified now because the current generated identity-review queue is clear and the bottleneck has shifted to inspecting claims and filling gaps. Its first release should have four views:

1. **Identity search:** full-text search across labels, accessions, publication sigla, owners, clients, and sources; faceted by location, script/language, authenticity, record status, and completeness.
2. **Identity dossier:** one page per probable physical bowl showing all member records, identifiers, appearances, claims grouped by field and source, texts, media, events, rights, and conflicts.
3. **Review workbench:** side-by-side identity comparison with reversible same/different/insufficient decisions and recorded evidence.
4. **Enrichment queue:** filters for missing fields, blocked sources, conflicts, rights review, and recently changed museum or auction appearances.

The private UI should write only through validated review/enrichment actions and keep the SQLite database on localhost. The eventual public dashboard can reuse the identity dossier and facets against reviewed, rights-safe exports.
