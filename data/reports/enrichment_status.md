# Identity and enrichment status

## Identity review

- Working physical identity hypotheses (all statuses): **1322**
- Multi-record identity clusters: **173**
- Underlying source records (all identities): **1590**
- Pending dedupe decisions: **0**

## Identity-level coverage

| Field | Identities | Coverage |
|---|---:|---:|
| Location | 910 | 68.8% |
| Provenance | 327 | 24.7% |
| Dating | 482 | 36.5% |
| Dimensions | 380 | 28.7% |
| Material | 408 | 30.9% |
| Language | 663 | 50.2% |
| Script | 91 | 6.9% |
| Text Edition | 1 | 0.1% |
| Translation | 48 | 3.6% |
| Image | 324 | 24.5% |

## Completeness distribution

| Core fields present | Identities |
|---|---:|
| 0–2 of 10 | 499 |
| 3–5 of 10 | 712 |
| 6–8 of 10 | 110 |
| 9–10 of 10 | 1 |

## Next-action queue

| Next action | Identities |
|---|---:|
| Location | 412 |
| Provenance | 640 |
| Dating | 55 |
| Dimensions | 139 |
| Material | 23 |
| Language | 7 |
| Script | 43 |
| Text Edition | 3 |

## Claim conflicts

**215** identities triggered raw difference flags. Current reviews support **37** compatible field-level instances and **15** substantive instances. **315** instances require review or revalidation; these are not established contradictions. No source claim or historical decision was deleted.

## Recommended private research UI

A local read-only-first interface is justified now because the current generated identity-review queue is clear and the bottleneck has shifted to inspecting claims and filling gaps. Its first release should have four views:

1. **Identity search:** full-text search across labels, accessions, publication sigla, owners, clients, and sources; faceted by location, script/language, authenticity, record status, and completeness.
2. **Identity dossier:** one page per probable physical bowl showing all member records, identifiers, appearances, claims grouped by field and source, texts, media, events, rights, and conflicts.
3. **Review workbench:** side-by-side identity comparison with reversible same/different/insufficient decisions and recorded evidence.
4. **Enrichment queue:** filters for missing fields, blocked sources, conflicts, rights review, and recently changed museum or auction appearances.

The private UI should write only through validated review/enrichment actions and keep the SQLite database on localhost. The eventual public dashboard can reuse the identity dossier and facets against reviewed, rights-safe exports.
