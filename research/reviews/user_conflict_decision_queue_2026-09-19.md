# Claim-difference decision queue for Mike

Prepared 19 September 2026 from the current private corpus and
`data/reports/claim_conflict_triage.md`. This is a proposal only: no claim,
disposition, identity, or canonical value was changed while preparing it.

## What the headline number means

The live queue contains 595 claim-field instances requiring a current review.
Of those, 288 have a historical review whose evidence fingerprint or supporting
rule is now stale, and 307 have never had a review. A queued instance is an
apparent difference, not necessarily a contradiction.

My first-pass structural assessment is:

| Provisional route | Instances | Share | What happens next |
|---|---:|---:|---|
| Codex can adjudicate from stored evidence | about 590 | about 99.2% | Review in coherent, exact-evidence batches; normally record `compatible` while preserving every source claim. |
| Fresh source research is clearly needed | about 5 | about 0.8% | Inspect the cited primary catalogue or its history before recording a disposition. |
| Mike must make a factual judgment now | 0 | 0% | None should be settled by preference when the evidence is inadequate. |

The approximately 590 agent-reviewable instances are dominated by orthogonal
or additive facets: date plus period (155), findspot plus production place
(roughly 100), separate publication states (roughly 140), institution-name
variants (most of 75 location rows), broad versus specific language labels,
and equivalent or additive biblical-reference lists. “Compatible” would not
select a preferred value or validate the underlying fact; it would only record
that the cited claims can coexist.

The estimate is intentionally provisional. Each row still has to pass an
exact-evidence review. If a batch exposes a real contradiction, it leaves the
agent lane and enters the source-research or Mike queue.

## Decisions queued for Mike

Reply with “accept recommendations” to take all defaults, or name any item you
want changed (for example, “D2 now; defer D6”).

### D1 — Delegate the compatibility backlog

**Recommended:** Let Codex work through the approximately 590 agent-reviewable
instances in bounded source-coherent batches, with an append-only manifest,
tests, and a before/after report for every batch. Route exceptions back here.

**Alternative:** Review the first batch before allowing subsequent batches.

This is the only decision that materially controls whether the large queue can
move without repeated user intervention.

### D2 — CBS 16020 collection disagreement

**Current evidence:** Penn identifies B16020 as a Penn Museum object; Kedar 2019
assigns NFP 10 / CBS 16020 to the Hilprecht collection in Jena.

**Recommended:** Keep `scholarly_disagreement`; put a primary concordance or
collection-history check on the research queue. Do not choose a collection by
preference.

**Choice:** Prioritize that check now, or leave it behind higher-impact source
acquisitions.

### D3 — VA 3383 script classification

**Current evidence:** Müller-Kessler calls the script Estrangelo; Lidzbarski
described it as Manichaean.

**Recommended:** Retain `scholarly_disagreement` permanently unless a later
specialist study explicitly resolves the terminology. No canonical script
label should be forced from the evidence now held.

**Choice:** Accept that stopping point, or commission specialist follow-up.

### D4 — Apollo lot 272 internal catalogue inconsistency

**Current evidence:** One auction catalogue gives both 5th–6th century CE and
600–800 CE, and alternates between Judeo-Aramaic and the weaker “Aramaic or
Aramaic-like patterns.”

**Recommended:** Retain both `source_inconsistency` decisions and treat the
auction description as low-authority evidence. Do not spend specialist time on
it unless the object becomes important for another reason.

**Choice:** Accept the stopping point, or place the object on a research list.

### D5 — Seven Penn/Montgomery measurement differences

**Current evidence:** Seven bowls have small height or diameter differences
between the 1913 register and current Penn records. The stored evidence cannot
distinguish rounding, measuring convention, restoration, or later correction.

**Recommended:** Keep both source-attributed measurements as `unresolved` and
do not publish a preferred dimension without remeasurement or better
documentation.

**Choice:** Accept the cohort policy, or prioritize physical/catalogue-history
research.

### D6 — Five source-dependent outliers in the pending queue

**Current evidence:**

- CBS 9008: three edition/catalogue sources say Syriac; Penn says “Hebrew
  Language.”
- NLI Ms. Heb. 9467.163: the catalogue code is `heb`, while an inspected study
  calls the inscription Jewish Aramaic; the code's semantics need confirmation.
- CBS 16017: a text heading says CBS 16917 while the register says CBS 16017.
- CBS 16018: the text heading supplies CBS 16018 but the printed register cell
  is blank.
- CBS 2971: the text heading says CBS 2971 while the register says CBS 2972.

**Recommended:** Keep all five out of compatibility batches and investigate
the cited catalogues before disposition. These are research tasks, not matters
for an unsupported user vote.

**Choice:** Run this targeted five-item investigation after the first
compatibility batch, or defer it behind source acquisition work.

## Existing substantive queue

Thirteen instances already have current dispositions and remain visible for
follow-up: two scholarly disagreements, two internal source inconsistencies,
and nine unresolved rows. They comprise D2–D5 above: CBS 16020, VA 3383, two
Apollo lot 272 fields, seven measurement rows, British Museum 117882 language,
and CBS 9010 language. The last two require source/original-script inspection
and do not presently require a user preference.

## Proposed reviewer boundary

Codex should decide whether claims are compatible when that conclusion follows
from their stored fields, wording, and cited sources. Mike should review only:

1. portfolio choices about whether a low-impact uncertainty deserves more
   research;
2. policy choices that affect publication or canonical display; and
3. genuinely irreducible scholarly judgments after the relevant evidence has
   been assembled.

This boundary preserves user control without turning data cleaning into a
595-click approval exercise.
