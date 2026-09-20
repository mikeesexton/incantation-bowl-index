# Claim-difference decision queue for Mike

Updated 19 September 2026 from the current private corpus and
`data/reports/claim_conflict_triage.md`. No claim, identity, or canonical value
was changed.

## Outcome

Mike authorized the agent-adjudicable lane. Codex reviewed all 595 differences
that initially lacked a current evidence-bound decision:

- Seven exact-evidence manifests classified 589 additive, orthogonal, or
  equivalent differences as `compatible`.
- A source-level six-exception manifest classified CBS 16018 as `compatible`,
  documented the CBS 16017 and CBS 2971 identifier pairs as internal
  `source_inconsistency`, and refreshed or added non-resolving dispositions for
  the three remaining scholarly questions.
- All 644 generated claim-field differences now have a current decision. The
  current ledger contains 626 compatible and 18 substantive dispositions; no
  row is waiting for first-pass evidence review.

The six-exception review is recorded in
`claim_conflict_six_exception_review_2026-09-19.json`. It was dry-run against a
database copy, replayed as a no-op, and then applied with all source claims
preserved.

## How much needs Mike's review?

None of the 595 rows required Mike to choose a factual winner. The work now
separates data maintenance from research prioritization:

| Route | Instances from the original 595 | Outcome |
|---|---:|---|
| Agent-adjudicated compatibility | 590 | Complete; no canonical value selected. |
| Agent-documented source inconsistency | 2 | Complete; contradictory historical source readings remain visible. |
| Specialist or collection-history follow-up | 3 | Correctly left unresolved or as scholarly disagreement. |
| Mike must make a factual judgment now | 0 | Unsupported preference would reduce, not improve, evidence quality. |

Mike's useful decisions are therefore portfolio decisions: whether any of the
three remaining research questions deserves scarce specialist or provenance
work now.

## Decisions queued for Mike

### D1 — CBS 9008 language

**Evidence:** Montgomery 1913, Moriggi 2014, and Brand 2021 classify CBS 9008
as Syriac; Penn's dated catalogue record says “Hebrew Language.”

**Current disposition:** `unresolved`. The specialist evidence leans strongly
toward Syriac, but it does not establish whether Penn's field is erroneous,
historical, or governed by another catalogue convention.

**Recommended portfolio choice:** Leave it unresolved unless CBS 9008 becomes
important enough to justify original-script review and a Penn catalogue-history
query.

### D2 — NLI Ms. Heb. 9467.163 language

**Evidence:** The NLI record supplies `heb`; the official MARC language list
maps that code to Hebrew. Abudraham 2026 classifies the inscription as Jewish
Aramaic. The live NLI record and the 2026 article were not available for full
inspection in this pass.

**Current disposition:** `unresolved`. Because `heb` is a language code rather
than merely a script code, the values should not be flattened into automatic
compatibility.

**Recommended portfolio choice:** Acquire the article and request or inspect
the NLI record history before spending specialist time on the object.

### D3 — HS 3003 collection history

**Evidence:** Ford and Morgenstern's 2020 Hilprecht collection catalogue and
Waller 2022 place HS 3003 in Jena. Kedar 2019 associates it with a private
Berlin collection in a densely punctuated note.

**Current disposition:** `scholarly_disagreement`. The held evidence does not
distinguish transfer, miscitation, punctuation trouble, or mistaken
concordance.

**Recommended portfolio choice:** Prioritize a Hilprecht collection/provenance
check only if collection history is a near-term research focus.

## Agent-resolved exceptions

- **CBS 16017 / Montgomery text 14:** `source_inconsistency`. The heading reads
  CBS 16917; the register reads CBS 16017; current Penn concordance evidence
  supports CBS 16017. The historical heading remains preserved.
- **CBS 16018 / Montgomery text 19:** `compatible`. The heading supplies CBS
  16018 and the register cell is blank; absence of a repeated identifier is not
  a competing identifier. Current Penn evidence agrees with the heading.
- **CBS 2971 / Montgomery text 40:** `source_inconsistency`. The heading reads
  CBS 2971 and the register reads CBS 2972; Penn explicitly notes that text 40
  is really B2971. Both historical readings remain preserved.

## Other substantive follow-up

The current substantive queue contains 18 rows: three scholarly disagreements,
four source inconsistencies, and eleven unresolved cases. Besides D1–D3, it
includes CBS 16020 collection history, VA 3383 script terminology, two Apollo
lot 272 catalogue inconsistencies, seven Penn/Montgomery measurement
differences, British Museum 117882 language, and CBS 9010 language.

These are not unreviewed data-cleaning rows. Each has a current disposition and
remains visible because the evidence itself warrants uncertainty or follow-up.

## Reviewer boundary

Codex may classify claims as compatible when that follows from exact stored
evidence, and may document an explicit source inconsistency without correcting
the source. Mike should review only:

1. portfolio choices about whether a low-impact uncertainty deserves more
   research;
2. policy choices that affect publication or canonical display; and
3. genuinely irreducible scholarly judgments after the relevant evidence has
   been assembled.

This boundary preserves user control without turning routine evidence hygiene
into hundreds of approval clicks.
