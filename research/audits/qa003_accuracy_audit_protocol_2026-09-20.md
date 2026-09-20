# QA-003 identity and extraction accuracy audit protocol

## Purpose

This audit measures whether the corpus's identity hypotheses and extracted
factual metadata agree with the evidence actually available to the project. It
does not estimate how many incantation bowls exist in the world, certify
authenticity, choose between scholarly disagreements, or treat an inaccessible
source as an error.

The audit has two samples:

1. A **60-identity representative sample** used for weighted corpus-level
   estimates.
2. A **20-identity high-risk sample** used only to discover failure modes. Its
   results are never pooled into the representative estimate.

The checked-in selection manifest is
`qa003_identity_accuracy_sample_2026-09-20.json`. Re-run it with:

```sh
PYTHONPATH=src .venv/bin/python \
  research/audits/build_qa003_sample.py \
  --check research/audits/qa003_identity_accuracy_sample_2026-09-20.json
```

## Population and selection

The population is all 1,652 current derived identity hypotheses, including
confirmed, probable, candidate, and rejected canonical statuses. Sampling is at
the identity-cluster level, not the source-appearance level.

Representative strata combine:

- canonical record status;
- linkage method: singleton, exact identifier, or checked/explicit
  concordance; and
- dominant source family: museum, scholarship, market, or repository/web.

Every non-empty composite stratum receives one seat. Remaining seats are
allocated by largest remainder in proportion to remaining stratum capacity.
Within each stratum, identities are ranked by SHA-256 of the declared seed,
sample role, and identity ID. The manifest records stratum population,
inclusion probability, and analysis weight for every representative row.

The high-risk sample excludes representative selections and ranks the remaining
population by predeclared signals: multi-record clusters, concordance links,
stored value differences, substantive disagreements, non-priority status,
authenticity-sensitive metadata, and unusually many sources or identifiers.

## Review unit and checks

Each selected identity is reviewed against its complete member list and the
source evidence available to the project. The reviewer records four separate
checks:

| Check | Question |
|---|---|
| Citation | Does each inspected appearance identify a real source and usable locator? |
| Identifier | Does the source evidence support the stored designation, including its assigning body? |
| Identity | For a multi-record cluster, does the exact identifier or explicit concordance support the same-object link? For a singleton, is there any positive evidence in the reviewed material that it was incorrectly left separate? |
| Claim | Do sampled factual claims preserve the source's wording, uncertainty, and locator without unsupported upgrading? |

Evidence priority is: held complete document or archived capture; dated raw
source payload retained by the collector; currently accessible official source;
then a bibliographic pointer. A pointer alone can verify that a citation exists
but cannot verify a reading, measurement, findspot, or identification.

## Outcomes

- `verified` — all applicable checks are supported by inspected evidence.
- `verified_with_notes` — no demonstrated data error, but an applicable check
  has a material limitation or only partial evidence.
- `error` — inspected evidence demonstrates an incorrect identity link,
  identifier, citation, locator, transcription of a factual value, certainty
  upgrade, or source attribution.
- `indeterminate` — the required evidence was unavailable or insufficient.
  Indeterminate rows remain in the denominator and are reported separately;
  they are never silently replaced.

Check-level states are `verified`, `error`, `not_reverifiable`, and
`not_applicable`. Error categories are recorded independently so one identity
may expose more than one failure mode.

## Analysis

Representative proportions use the manifest's inverse-probability analysis
weights. Report at minimum:

- unweighted and weighted outcome totals;
- weighted verified-or-verified-with-notes rate;
- weighted demonstrated-error rate;
- weighted indeterminate rate;
- effective sample size under unequal weights;
- error categories and evidence-access limitations; and
- all high-risk outcomes separately.

Confidence intervals must be described as design-aware approximations. Sixty
rows can expose large systematic problems, but it cannot justify fine-grained
precision or subgroup accuracy claims.

## Decision boundary

The audit may identify and queue errors. It does not silently merge or split
identities, select preferred scholarly claims, declare authenticity, or clear
rights. Any correction follows the repository's existing evidence-bound review
workflow in a later batch.
