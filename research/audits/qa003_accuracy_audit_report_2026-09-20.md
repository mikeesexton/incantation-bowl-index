# QA-003 stratified identity and extraction accuracy audit

**Audit date:** 2026-09-20  
**Population:** 1652 current working identity hypotheses  
**Representative sample:** 60 identities across 24 non-empty strata  
**High-risk diagnostic sample:** 20 additional identities

## Result

The representative sample found no demonstrated citation, identifier, identity-link, or sampled factual-claim error. This is evidence of substantial corpus maturity, not a certificate that every record is correct. Thirty-six rows were fully verified, 23 were verified with documented evidence limitations, and one was indeterminate because the BM068A catalogue reading was not available for reinspection.

| Outcome | Unweighted | Weighted estimate |
|---|---:|---:|
| Verified | 36/60 | 74.9% |
| Verified with notes | 23/60 | 23.7% |
| Demonstrated error | 0/60 | 0.0% |
| Indeterminate | 1/60 | 1.3% |
| Verified or verified with notes | 59/60 | 98.7% |

Inverse-probability weights sum to 1652, reproducing the population denominator. Unequal weights reduce the Kish effective sample size from 60 to 47.5.

For scale only, Wilson intervals calculated with that effective sample size give an approximate 95% interval of 90.2%–99.8% for verified-or-noted, 0.0%–7.5% for demonstrated error, and 0.2%–9.8% for indeterminate. These are heuristic design-aware intervals, not a full survey-variance estimate; clustering, reviewer dependence, and the small sample preclude fine-grained subgroup claims.

## Check-level coverage

| Check | Verified | Not re-verifiable | Not applicable | Error |
|---|---:|---:|---:|---:|
| Citation | 60 | 0 | 0 | 0 |
| Identifier | 60 | 0 | 0 | 0 |
| Identity | 16 | 0 | 44 | 0 |
| Claim | 47 | 9 | 4 | 0 |

9 representative claim checks were not fully re-verifiable. In 8 cases, retained or live evidence still supported enough of the record for a conservative `verified_with_notes` outcome. BM068A remained indeterminate. A missing capture was never silently replaced with a different source.

## High-risk diagnostic sample

All 20 high-risk identities were `verified_with_notes`. Their exact identifiers or explicit concordances supported the current clusters, and the inspected value differences remained source-attributed rather than silently canonicalized. These rows were selected for failure-mode discovery and are not included in the representative estimate.

Outcome counts: verified_with_notes 20.

## Decisions and follow-up

No correction or user adjudication is queued from this audit because no inspected evidence demonstrated a wrong value or identity link. The one open item is an acquisition task: obtain or inspect the Segal catalogue entry for BM068A, then supersede the indeterminate audit row. Existing scholarly disagreements and source inconsistencies remain preserved under their source-level conflict decisions; this audit does not choose preferred values, authenticity, or rights.

## Reproduction

The selection, protocol, review manifest, and rendering scripts are checked in under `research/audits/`. The selection is deterministic from the declared seed. The append-only ledger binds each judgment to a digest of the exact objects, sources, captures, appearances, identifiers, claims, and dedupe evidence inspected; later evidence changes make replay fail stale rather than preserving false currency.
