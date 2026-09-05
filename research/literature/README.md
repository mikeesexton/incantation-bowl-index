# Prior scoping review (July 2026)

Before this index existed, a separate systematic scoping review of incantation-bowl
scholarship was carried out and checkpointed on **13 July 2026**. These are the
deliverables of that work, imported unchanged on 5 September 2026.

They are the field-level counterpart to the object-level corpus in
`data/private/ibi.sqlite3`: the review says what the scholarship establishes,
disputes, and cannot yet support; the index says which physical bowls exist and
what each source reports about them. Neither supersedes the other.

## Files

| File | What it is | SHA-256 |
|---|---|---|
| `literature-review-2026-07-13.pdf` | The review itself: 31 pages, coverage 1853 – July 2026 | `d4b9eff5…65ed5f3` (see below) |
| `literature-review-2026-07-13.txt` | Text extraction of the same PDF, for grep and citation lookup | `113226df…65ed5f3` |
| `bibliography-control-2026-07-13.csv` | 26 screened core records with access and screening status | `939ac8ee…8ea2e5ea` |
| `search-log-2026-07-13.csv` | 14 dated searches with query strings and screening results | `a02849b7…567eb8c8` |
| `review-progress-2026-07-13.md` | Checkpoint record: decisions fixed, tasks open | `b56b19f9…dc2259d` |

Full digests:

```
939ac8eec4eacd08b3fd6174bc46651f852fb15fbc9dda29e2f826ed8ea2e5ea  bibliography-control-2026-07-13.csv
d4b9eff54b777d2bda40b76679d95e7595759fb5b2f1157e67482863212dfa43  literature-review-2026-07-13.pdf
113226df251d434c2502d5643cb4f0d2340618656b74d1efa927d5ed565ed5f3  literature-review-2026-07-13.txt
b56b19f95fb1159bfc768dab082a2cff9855b79ec133227e067bc0b39dc2259d  review-progress-2026-07-13.md
a02849b78489227dca55b5e21322e4b244634d07b29bd7bd7e5a2d1c567eb8c8  search-log-2026-07-13.csv
```

The text extraction was produced with `pypdf`; page boundaries are marked
`=== PAGE n ===`. It is a convenience copy — the PDF is authoritative, and the
page numbers printed inside the review are the ones to cite.

A light-theme rendering of the same document exists outside the repository at
`~/Documents/Bowls of Moses/01 Me-Facing/Research/Literature Reviews/`.

## How to use these here

**The review is a source, not a licence.** Its statements enter the corpus the
same way any other source's do: as a claim with a locator, under the ordinary
rules in [`docs/project-rules.md`](../../docs/project-rules.md). Cite it by
printed page (`literature review, printed p. 12`), not by PDF page or by line
number in the `.txt`.

**The review is secondary throughout.** It verifies titles, dates, declared
arguments, and the shape of a debate. It does not verify a reading, a
measurement, a findspot, or an identification — for those, go to the edition or
the catalogue it points at. This is the review's own rule (§1.3) and it matches
the project's: publisher and repository metadata may verify bibliographic facts,
never line-level readings.

**Its evidence grades are worth reusing.** §1.4 grades object evidence A–D:

- **A** — published photograph or drawing *plus* a usable edition; documented collection history where available
- **B** — a scholarly edition exists, but image, provenance, or archaeological context is absent
- **C** — provisional: abstract, catalogue notice, old hand copy, unverified reading
- **D** — unsuitable for historical inference: dealer description, decontextualized image, untraceable claim

The index currently has no equivalent per-object grade. See `TEXT-007` in the
roadmap.

## What the review changes about this index

Recorded in full in [`docs/dataset_maturity_roadmap.md`](../../docs/dataset_maturity_roadmap.md);
in short, it supplies four things the index was missing:

1. **A control list.** Waller's "State of the Art" (in Marcus & Mokhtarian 2025)
   lists JBA bowl publications 1853–2024. That is the nearest thing to a
   completeness check the field offers, and acquiring it is the review's
   standing first priority. Compare `SCHOL-001`.
2. **A named scholarly canon.** The 26-record bibliography plus §10 name the
   editions that actually publish bowls. Many are absent from `sources`. See
   `SCHOL-002`.
3. **A field model.** §9 Phase 2 specifies ten field groups for an object
   ledger — Identity, Provenance, Physical, Text, People, Ritual, Intertexts,
   Visual, Scholarship, Ethics/QA. The index models the first three and part of
   the fourth. See `META-006`.
4. **Interpretive guardrails.** §6.4 and §7 require separating author, textual
   voice, copyist, producer, commissioner, client, and beneficiary rather than
   collapsing them into one "who" field. See `META-007`.

## Its own open tasks

From `review-progress-2026-07-13.md`, still open as of 5 September 2026:

- Obtain the complete Marcus–Mokhtarian 2025 volume (Waller's publication
  control through 2024; Bhayro's dated-object chapter).
- Expand the bibliography from 26 to 100 records.
- Run the database sweep proper — RAMBI, ATLA, Index Islamicus, ProQuest
  Dissertations, WorldCat, Crossref, OpenAlex — with saved result counts. The
  14 logged searches are a targeted verification pass, not a sweep.
- Expand older German, French, Italian, and Hebrew coverage beyond
  bibliographic representation.
- Populate a balanced pilot object set across JBA, Mandaic, Syriac, Pahlavi,
  pseudo-script, excavated, and market-provenanced categories.

The third and fifth of these are now index tasks (`SCHOL-003`, `META-008`)
because the index is the better place to do them.
