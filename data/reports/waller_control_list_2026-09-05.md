# Measured against Waller's control list — 5 September 2026

The first external check this index has had on its own completeness.

## The control list

Daniel J. Waller, "The Study of the Jewish Babylonian Aramaic Magic Bowls: State of the
Art: With a List of JBA Bowl Publications (1853–2024) and a Map of Known Excavation
Sites," in Marcus and Mokhtarian 2025, printed pp. 3–47. The full chapter is now held
privately (`SRC-19F191B3F5C5`, archive SHA-256 `b60b030f…4237c77`), superseding the
two-page excerpt reviewed earlier the same day. The list runs at printed pp. 40–47 and is
transcribed to `research/sources/waller_2025_jba_publication_list.jsonl`:
**115 entries by 52 authors**, checked by inspection after parsing.

It is the nearest thing the field has to a definition of "published," and it is JBA only.
Mandaic and Syriac publications are outside its scope and therefore outside this measurement.

## The result

| | Publications | Share |
|---|---:|---:|
| In `sources` | 46 | 40% |
| **Not in `sources`** | **69** | **60%** |
| — author absent entirely | 45 | |
| — author held, but a different work | 24 | |

Matching is by surname and year, so this is an indicator rather than a concordance. The 24
"different work" cases were spot-checked and are genuine misses: the index holds Abousamra
2012 and 2019 but not 2010 or 2016; Geller 1976 but not 1980, 1986 or 1997; no Isbell at all,
only pages that cite his numbering. In the other direction the check is generous — a surname
and year hit counts as held without verifying it is the same edition — so 60% is a floor.

## Where the gap is

| Author | Missing | Years |
|---|---:|---|
| Gordon | 8 | 1934, 1934, 1934, 1937, 1941, 1951, 1978, 1984 |
| Al-Jubouri | 3 | 2011, 2013, 2015 |
| Geller | 3 | 1980, 1986, 1997 |
| Herman | 3 | 1997, 2000, 2021 |
| Levene | 3 | 2003, 2003, 2014 |
| Moriggi | 3 | 2001, 2005, 2005 |
| Schwab | 3 | 1886, 1915, 1916 |
| Shaked | 3 | 1995, 2005, 2006 |
| Abousamra | 2 | 2010, 2016 |
| Borisov | 2 | 1939, 1969 |
| Isbell | 2 | 1975, 1976 |
| Kaufman | 2 | 1973, 1975 |
| Levy | 2 | 1855, 1861 |
| Müller-Kessler | 2 | 1994, 2005 |
| Naveh | 2 | 1993, 1998 |
| Wohlstein | 2 | 1893, 1894 |
| Babelon | 1 | 1882 |
| Billiet | 1 | 1931 |
| Chwolson | 1 | 1992 |
| Ellis | 1 | 1853 |

Plus 20 further authors missing one publication each.

**Gordon is the single largest hole: eight publications, none held.** That confirms the
prediction made from the scoping review before this list was available.

### By decade

| Decade | On the list | Missing | Missing share |
|---|---:|---:|---:|
| 1850s | 2 | 2 | 100% |
| 1860s | 1 | 1 | 100% |
| 1870s | 1 | 1 | 100% |
| 1880s | 4 | 4 | 100% |
| 1890s | 8 | 5 | 62% |
| 1900s | 1 | 1 | 100% |
| 1910s | 3 | 2 | 67% |
| 1920s | 1 | 1 | 100% |
| 1930s | 7 | 7 | 100% |
| 1940s | 2 | 2 | 100% |
| 1950s | 1 | 1 | 100% |
| 1960s | 4 | 3 | 75% |
| 1970s | 8 | 6 | 75% |
| 1980s | 4 | 3 | 75% |
| 1990s | 9 | 8 | 89% |
| 2000s | 18 | 11 | 61% |
| 2010s | 30 | 8 | 27% |
| 2020s | 10 | 3 | 30% |

The nineteenth-century layer is almost entirely absent — Ellis 1853, Levy 1855 and 1861,
Halévy 1877, Babelon 1882, Hyvernat 1885, Harkavy 1889, Wohlstein 1893 and 1894, Fraenkel
1894, Lacau 1894, Stübe 1895 — which is exactly where the least reliable findspots and the
earliest object attributions were established. That bears on META-005 as much as on
bibliography.

## A second benchmark: language distribution

Waller cites Ford and Abudraham 2018 for the distribution of Aramaic varieties across the
bowls as a whole: **approximately 62% JBA, 23% Mandaic, 13% Syriac** (printed p. 3 n. 1). That
is a better external yardstick than the EJCM working counts META-008 has been using.

| | In the index | Share | Expected | Gap |
|---|---:|---:|---:|---:|
| JBA / Aramaic | 583 | 80.0% | 62% | +18.0 |
| Mandaic | 77 | 10.6% | 23% | −12.4 |
| Syriac | 69 | 9.5% | 13% | −3.5 |

729 of 1,588 records carry a language classification. At Waller's proportion the index is short
roughly **91 Mandaic objects**. Syriac is close; JBA is over-represented by about the margin the
scoping review predicts, since publication bias favours legible JBA bowls and this index was
built from published and catalogued records.

## What follows

1. `SCHOL-002` — ingest the 69 missing publications as source records, with citations sourced to
   this list rather than transcribed from memory. A bounded, evidenced task now.
2. `META-008` — the Mandaic shortfall has a number and a cause. Pognon 1898 and Yamauchi 1967
   are absent, and Waller's list does not cover Mandaic, so a separate control list is needed;
   Ford and Abudraham 2018 is the obvious candidate.
3. `META-005` — the missing nineteenth-century layer is where unverified findspots come from.
4. The saturation claim should be read against this. Two sweeps under 1% net-new measured
   marginal yield *within the searched classes*; against an external control list, published-
   corpus coverage is 40%.

## Reproduction

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli verify-archive
```

The parse and the surname-and-year check are recorded in the JSONL artifact, one row per entry
with its `held_in_sources` verdict and `check_basis`. No corpus writes were made beyond
depositing the chapter itself.

---

## Addendum: after SCHOL-002 (same day)

The 69 missing publications were ingested as source records, citations verbatim
from Waller's list. Coverage of the control list is now **115 / 115**.

**That number means less than it looks.** It measures whether the index holds a
*bibliographic record* for each publication. It does not mean the publications
have been read, that their editions have been located, or — most importantly —
that the **bowls they publish are in the corpus**. Waller's list names
publications; each one publishes somewhere between one and several hundred
objects, and almost none of those object-to-publication links exist yet.

So the honest pair of statements is:

- Publication-record coverage of the JBA control list: **100%** (115/115).
- Object-level coverage of what those publications contain: **unmeasured, and
  mostly zero.** Gordon's eight publications are now cited; not one of his bowls
  is linked to them.

The second number is the real one, and producing it is `SCHOL-004`'s job — making
publications first-class records so a bowl can be asked "which edition publishes
you," and `TEXT-001`'s, replacing the identifier-scheme proxy with checked
edition locators. Until then, treat 100% as *we now know what to read*, not *we
have it*.

Titles and source types in the ingested records are parsed from the citation
strings and are the least reliable part of each record; the verbatim citation is
the authoritative field. The four works that appeared both here and in the
earlier hand-written seed — Myhrman 1909, Isbell 1975, Naveh–Shaked 1993,
Müller-Kessler 2005 — were resolved in favour of Waller's sourced citation.
