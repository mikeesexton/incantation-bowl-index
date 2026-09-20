#!/usr/bin/env python3
"""Render the public-methodology QA-003 results report from checked manifests."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def pct(value):
    return "%.1f%%" % (100 * value)


def wilson(p, n_eff, z=1.96):
    denominator = 1 + z * z / n_eff
    center = (p + z * z / (2 * n_eff)) / denominator
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n_eff)) / n_eff) / denominator
    return max(0, center - half), min(1, center + half)


def render(selection, review):
    representative = {
        item["identity_id"]: item for item in selection["representative"]
    }
    rep_entries = [
        item for item in review["entries"] if item["sample_role"] == "representative"
    ]
    risk_entries = [
        item for item in review["entries"] if item["sample_role"] == "high_risk"
    ]
    weights = [representative[item["identity_id"]]["analysis_weight"] for item in rep_entries]
    weight_total = sum(weights)
    n_eff = weight_total * weight_total / sum(value * value for value in weights)
    outcomes = Counter(item["outcome"] for item in rep_entries)
    weighted = {
        outcome: sum(
            representative[item["identity_id"]]["analysis_weight"]
            for item in rep_entries if item["outcome"] == outcome
        ) / weight_total
        for outcome in ("verified", "verified_with_notes", "error", "indeterminate")
    }
    supported = weighted["verified"] + weighted["verified_with_notes"]
    intervals = {
        "supported": wilson(supported, n_eff),
        "error": wilson(weighted["error"], n_eff),
        "indeterminate": wilson(weighted["indeterminate"], n_eff),
    }
    check_counts = {
        name: Counter(item[name] for item in rep_entries)
        for name in ("citation_check", "identifier_check", "identity_check", "claim_check")
    }
    risk_outcomes = Counter(item["outcome"] for item in risk_entries)
    limited_claims = check_counts["claim_check"]["not_reverifiable"]
    limited_with_notes = sum(
        item["claim_check"] == "not_reverifiable"
        and item["outcome"] == "verified_with_notes"
        for item in rep_entries
    )
    lines = [
        "# QA-003 stratified identity and extraction accuracy audit",
        "",
        "**Audit date:** 2026-09-20  ",
        "**Population:** %d current working identity hypotheses  " % selection["population_n"],
        "**Representative sample:** %d identities across %d non-empty strata  " % (
            len(rep_entries), len(selection["population_counts_by_stratum"]),
        ),
        "**High-risk diagnostic sample:** %d additional identities" % len(risk_entries),
        "",
        "## Result",
        "",
        "The representative sample found no demonstrated citation, identifier, identity-link, "
        "or sampled factual-claim error. This is evidence of substantial corpus maturity, not a "
        "certificate that every record is correct. Thirty-six rows were fully verified, 23 were "
        "verified with documented evidence limitations, and one was indeterminate because the "
        "BM068A catalogue reading was not available for reinspection.",
        "",
        "| Outcome | Unweighted | Weighted estimate |",
        "|---|---:|---:|",
        "| Verified | %d/%d | %s |" % (outcomes["verified"], len(rep_entries), pct(weighted["verified"])),
        "| Verified with notes | %d/%d | %s |" % (outcomes["verified_with_notes"], len(rep_entries), pct(weighted["verified_with_notes"])),
        "| Demonstrated error | %d/%d | %s |" % (outcomes["error"], len(rep_entries), pct(weighted["error"])),
        "| Indeterminate | %d/%d | %s |" % (outcomes["indeterminate"], len(rep_entries), pct(weighted["indeterminate"])),
        "| Verified or verified with notes | %d/%d | %s |" % (
            outcomes["verified"] + outcomes["verified_with_notes"], len(rep_entries), pct(supported),
        ),
        "",
        "Inverse-probability weights sum to %.0f, reproducing the population denominator. "
        "Unequal weights reduce the Kish effective sample size from 60 to %.1f." % (weight_total, n_eff),
        "",
        "For scale only, Wilson intervals calculated with that effective sample size give an "
        "approximate 95%% interval of %s–%s for verified-or-noted, %s–%s for demonstrated "
        "error, and %s–%s for indeterminate. These are heuristic design-aware intervals, not a "
        "full survey-variance estimate; clustering, reviewer dependence, and the small sample "
        "preclude fine-grained subgroup claims." % (
            pct(intervals["supported"][0]), pct(intervals["supported"][1]),
            pct(intervals["error"][0]), pct(intervals["error"][1]),
            pct(intervals["indeterminate"][0]), pct(intervals["indeterminate"][1]),
        ),
        "",
        "## Check-level coverage",
        "",
        "| Check | Verified | Not re-verifiable | Not applicable | Error |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, label in (
        ("citation_check", "Citation"), ("identifier_check", "Identifier"),
        ("identity_check", "Identity"), ("claim_check", "Claim"),
    ):
        counts = check_counts[name]
        lines.append("| %s | %d | %d | %d | %d |" % (
            label, counts["verified"], counts["not_reverifiable"],
            counts["not_applicable"], counts["error"],
        ))
    lines += [
        "",
        "%d representative claim checks were not fully re-verifiable. In %d cases, retained "
        "or live evidence still supported enough of the record for a conservative "
        "`verified_with_notes` outcome. BM068A remained indeterminate. A missing capture was never "
        "silently replaced with a different source." % (limited_claims, limited_with_notes),
        "",
        "## High-risk diagnostic sample",
        "",
        "All %d high-risk identities were `verified_with_notes`. Their exact identifiers or "
        "explicit concordances supported the current clusters, and the inspected value "
        "differences remained source-attributed rather than silently canonicalized. These rows "
        "were selected for failure-mode discovery and are not included in the representative "
        "estimate." % len(risk_entries),
        "",
        "Outcome counts: " + ", ".join(
            "%s %d" % (key, risk_outcomes[key]) for key in sorted(risk_outcomes)
        ) + ".",
        "",
        "## Decisions and follow-up",
        "",
        "No correction or user adjudication is queued from this audit because no inspected "
        "evidence demonstrated a wrong value or identity link. The one open item is an acquisition "
        "task: obtain or inspect the Segal catalogue entry for BM068A, then supersede the "
        "indeterminate audit row. Existing scholarly disagreements and source inconsistencies "
        "remain preserved under their source-level conflict decisions; this audit does not choose "
        "preferred values, authenticity, or rights.",
        "",
        "## Reproduction",
        "",
        "The selection, protocol, review manifest, and rendering scripts are checked in under "
        "`research/audits/`. The selection is deterministic from the declared seed. The append-only "
        "ledger binds each judgment to a digest of the exact objects, sources, captures, "
        "appearances, identifiers, claims, and dedupe evidence inspected; later evidence changes "
        "make replay fail stale rather than preserving false currency.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("selection", type=Path)
    parser.add_argument("reviews", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    rendered = render(selection, reviews)
    if args.check:
        if args.check.read_text(encoding="utf-8") != rendered:
            raise SystemExit("checked QA-003 report does not reproduce")
        print("QA-003 report matches checked manifests")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
