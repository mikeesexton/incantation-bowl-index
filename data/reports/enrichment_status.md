# Identity and enrichment status

## Identity review

- Working physical identity hypotheses (all statuses): **1929**
- Multi-record identity clusters: **221**
- Underlying source records (all identities): **2281**
- Pending dedupe decisions: **0**

## Identity-level coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 1310 | 67.9% |
| Provenance | 645 | 33.4% |
| Dating | 484 | 25.1% |
| Dimensions | 694 | 36.0% |
| Material | 419 | 21.7% |
| Language | 1210 | 62.7% |
| Script | 106 | 5.5% |
| Text Edition | 613 | 31.8% |
| Translation | 630 | 32.7% |
| Image | 622 | 32.2% |

## Completeness distribution

| Core fields present | Identities |
|---|---:|
| 0–2 of 10 | 629 |
| 3–5 of 10 | 965 |
| 6–8 of 10 | 318 |
| 9–10 of 10 | 17 |

## Next-action queue

| Next action | Identities |
|---|---:|
| Location | 619 |
| Provenance | 757 |
| Dating | 337 |
| Dimensions | 139 |
| Material | 22 |
| Language | 7 |
| Script | 45 |
| Text Edition | 2 |
| Rights Review | 1 |

## Claim conflicts

**698** identities triggered raw difference flags. Current reviews support **566** compatible field-level instances and **16** substantive instances. **876** instances require review or revalidation; these are not established contradictions. No source claim or historical decision was deleted.

## Recommended private research UI

A local read-only-first interface is justified now because the current generated identity-review queue is clear and the bottleneck has shifted to inspecting claims and filling gaps. Its first release should have four views:

1. **Identity search:** full-text search across labels, accessions, publication sigla, owners, clients, and sources; faceted by location, script/language, authenticity, record status, and completeness.
2. **Identity dossier:** one page per probable physical bowl showing all member records, identifiers, appearances, claims grouped by field and source, texts, media, events, rights, and conflicts.
3. **Review workbench:** side-by-side identity comparison with reversible same/different/insufficient decisions and recorded evidence.
4. **Enrichment queue:** filters for missing fields, blocked sources, conflicts, rights review, and recently changed museum or auction appearances.

The private UI should write only through validated review/enrichment actions and keep the SQLite database on localhost. The eventual public dashboard can reuse the identity dossier and facets against reviewed, rights-safe exports.
