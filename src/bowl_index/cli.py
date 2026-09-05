import argparse
import json
from pathlib import Path

from .archive import capture_url, verify_archive
from .collectors import (
    collect_apotropaic, collect_british_museum_related, collect_met, collect_penn,
    collect_nli, collect_schoyen, load_british_museum_page_mappings,
)
from .conflicts import triage_claim_conflicts, write_conflict_report
from .db import PROJECT_ROOT, connect, migrate
from .dedupe import (
    adjudicate_conflicting_unique_identifiers, adjudicate_exact_identifiers,
    adjudicate_distinct_enumerated_source_items, adjudicate_explicit_concordances, queue_all,
)
from .discovery import (
    collect_internet_archive, collect_repository_metadata, collect_scholarly_metadata,
)
from .export import export_all
from .enrichment import run_source_preserving_enrichment
from .ingest import load_compact_list, load_jsonl
from .identity import write_enrichment_report
from .montgomery import ingest_montgomery_review
from .pdf_catalogues import collect_waller
from .queries import load_audit_log, load_coverage_log, load_saturation_log, load_search_log, seed_queries
from .report import statistics, write_report
from .review import load_dedupe_reviews
from .roadmap import write_roadmap
from .proofreading import apply_proofreading
from .rights import apply_rights_batch
from .public_export import export_public
from .claim_corrections import apply_locator_corrections
from .cohort import write_montgomery_cohort, apply_montgomery_register
from .concordance import apply_concordance_review
from .relationships import apply_relationship_review


def build_parser():
    parser = argparse.ArgumentParser(prog="ibi", description="Incantation Bowl Index research CLI")
    parser.add_argument("--db", help="override the working SQLite path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="initialize or migrate the database")
    sub.add_parser("stats", help="print corpus statistics")
    sub.add_parser("seed-queries", help="load the multilingual discovery matrix")
    search_log = sub.add_parser("ingest-search-log", help="ingest checked JSONL search-ledger rows")
    search_log.add_argument("path")
    coverage_log = sub.add_parser("ingest-coverage-log", help="ingest checked JSONL coverage assessments")
    coverage_log.add_argument("path")
    saturation_log = sub.add_parser("ingest-saturation-log", help="ingest measured broad-sweep results")
    saturation_log.add_argument("path")
    audit_log = sub.add_parser("ingest-audit-log", help="ingest a checked manual-audit sample")
    audit_log.add_argument("path")
    dedupe_review = sub.add_parser(
        "ingest-dedupe-review", help="ingest reversible checked dedupe decisions from JSONL"
    )
    dedupe_review.add_argument("path")
    conflict_review = sub.add_parser(
        "triage-conflicts", help="classify identity-level claim differences from a checked review"
    )
    conflict_review.add_argument("path")
    proofreading = sub.add_parser("ingest-proofreading", help="apply scan-checked text revisions with retained originals")
    proofreading.add_argument("path")
    concordance = sub.add_parser("ingest-concordance-review", help="record dated museum checks of existing Montgomery links")
    concordance.add_argument("path")
    relationships = sub.add_parser(
        "ingest-relationship-review",
        help="record source-reported object relationships without merging identities",
    )
    relationships.add_argument("path")
    rights = sub.add_parser("ingest-rights-review", help="apply evidence-bound media-rights decisions")
    rights.add_argument("path")
    corrections = sub.add_parser("ingest-locator-corrections", help="apply citation-pointer repairs with immutable originals")
    corrections.add_argument("path")
    register = sub.add_parser("ingest-montgomery-register", help="append scan-checked register claims")
    register.add_argument("path")
    cohort = sub.add_parser("report-montgomery-cohort", help="account for all forty main Montgomery texts")
    cohort.add_argument("--register", default=str(PROJECT_ROOT / "research/enrichment/montgomery_register_checked_2026-09-04.json"))
    cohort.add_argument("--destination", default=str(PROJECT_ROOT / "data/reports/montgomery_cohort_current.md"))
    public = sub.add_parser("export-public", help="write a narrow media-gated reference scaffold, without publishing")
    public.add_argument("--destination", required=True)
    conflict_report = sub.add_parser(
        "report-conflicts", help="write the identity-level claim conflict triage report"
    )
    conflict_report.add_argument(
        "--destination",
        default=str(PROJECT_ROOT / "data" / "reports" / "claim_conflict_triage.md"),
    )
    collect = sub.add_parser("collect", help="run a structured collection connector")
    collect.add_argument(
        "collection",
        choices=(
            "apotropaic", "british-museum", "internet-archive", "met", "nli", "penn",
            "repository-metadata", "scholarly-metadata", "schoyen", "waller",
        ),
    )
    ingest = sub.add_parser("ingest", help="ingest source, candidate, or lead JSONL")
    ingest.add_argument("record_type", choices=("source", "candidate", "lead"))
    ingest.add_argument("path")
    compact = sub.add_parser("ingest-list", help="ingest a checked compact scholarly-list manifest")
    compact.add_argument("path")
    bm_enrichment = sub.add_parser(
        "ingest-bm-enrichment", help="ingest checked British Museum item-page mappings"
    )
    bm_enrichment.add_argument("path")
    montgomery = sub.add_parser(
        "ingest-montgomery", help="ingest checked text and concordance evidence from Montgomery 1913"
    )
    montgomery.add_argument("pdf")
    montgomery.add_argument("review")
    capture = sub.add_parser("capture", help="archive a robots-permitted public URL")
    capture.add_argument("url")
    capture.add_argument("--source-id")
    capture.add_argument("--rights-status", default="unknown")
    sub.add_parser("verify-archive", help="verify every archived file against its manifest hash")
    sub.add_parser(
        "enrich", help="derive conservative source-preserving normalized claims"
    )
    dedupe = sub.add_parser("dedupe", help="queue possible duplicate object pairs")
    dedupe.add_argument("--threshold", type=float, default=0.35)
    sub.add_parser("adjudicate-exact", help="mark pending strong exact-identifier pairs as the same object")
    sub.add_parser(
        "adjudicate-conflicts",
        help="reject fuzzy pairs with conflicting IDs in documented unique namespaces",
    )
    sub.add_parser(
        "adjudicate-concordances",
        help="accept unambiguous source-attributed cross-scheme concordances",
    )
    sub.add_parser(
        "adjudicate-enumerations",
        help="reject fuzzy pairs between separate items in reviewed source enumerations",
    )
    export = sub.add_parser("export", help="write reproducible CSV and JSONL exports")
    export.add_argument("--destination", default=str(PROJECT_ROOT / "data" / "private" / "exports" / "latest"))
    report = sub.add_parser("report", help="write the campaign status report")
    report.add_argument("--destination", default=str(PROJECT_ROOT / "data" / "reports" / "campaign_status.md"))
    enrichment_report = sub.add_parser(
        "report-enrichment", help="write identity-level enrichment coverage and UI guidance"
    )
    enrichment_report.add_argument(
        "--destination",
        default=str(PROJECT_ROOT / "data" / "reports" / "enrichment_status.md"),
    )
    roadmap = sub.add_parser(
        "roadmap", help="render the living dataset-maturity roadmap from corpus metrics"
    )
    roadmap.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "research" / "roadmap" / "dataset_maturity.json"),
    )
    roadmap.add_argument(
        "--destination",
        default=str(PROJECT_ROOT / "docs" / "dataset_maturity_roadmap.md"),
    )
    serve_parser = sub.add_parser("serve", help="run the private localhost research console")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = connect(args.db)
    migrate(conn)
    if args.command == "init":
        print("initialized %s" % (args.db or "default database"))
    elif args.command == "stats":
        print(json.dumps(statistics(conn), indent=2, sort_keys=True))
    elif args.command == "seed-queries":
        print("seeded %s rows" % seed_queries(conn, PROJECT_ROOT / "config" / "query_matrix.json"))
    elif args.command == "ingest-search-log":
        print("ingested %s search-log rows" % load_search_log(conn, args.path))
    elif args.command == "ingest-coverage-log":
        print("ingested %s coverage rows" % load_coverage_log(conn, args.path))
    elif args.command == "ingest-saturation-log":
        print("ingested %s saturation rows" % load_saturation_log(conn, args.path))
    elif args.command == "ingest-audit-log":
        print("ingested %s manual-audit rows" % load_audit_log(conn, args.path))
    elif args.command == "ingest-dedupe-review":
        print("ingested %s dedupe reviews" % load_dedupe_reviews(conn, args.path))
    elif args.command == "triage-conflicts":
        print(json.dumps(triage_claim_conflicts(conn, args.path), indent=2, sort_keys=True))
    elif args.command == "ingest-proofreading":
        print(json.dumps(apply_proofreading(conn, args.path, PROJECT_ROOT), indent=2, sort_keys=True))
    elif args.command == "ingest-concordance-review":
        print(json.dumps(apply_concordance_review(conn, args.path), indent=2, sort_keys=True))
    elif args.command == "ingest-relationship-review":
        print(json.dumps(apply_relationship_review(conn, args.path), indent=2, sort_keys=True))
    elif args.command == "ingest-rights-review":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_rights_batch(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-locator-corrections":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_locator_corrections(conn, review, PROJECT_ROOT), indent=2, sort_keys=True))
    elif args.command == "ingest-montgomery-register":
        print(json.dumps(apply_montgomery_register(conn, args.path), indent=2, sort_keys=True))
    elif args.command == "report-montgomery-cohort":
        print(json.dumps(write_montgomery_cohort(conn, args.register, args.destination), indent=2, sort_keys=True))
    elif args.command == "export-public":
        print(json.dumps(export_public(conn, args.destination), indent=2, sort_keys=True))
    elif args.command == "report-conflicts":
        print(json.dumps(
            write_conflict_report(conn, args.destination), indent=2, sort_keys=True
        ))
    elif args.command == "collect":
        if args.collection == "apotropaic":
            print(json.dumps(collect_apotropaic(conn), indent=2, sort_keys=True))
        elif args.collection == "british-museum":
            print(json.dumps(collect_british_museum_related(conn), indent=2, sort_keys=True))
        elif args.collection == "met":
            print(json.dumps(collect_met(conn), indent=2, sort_keys=True))
        elif args.collection == "nli":
            print(json.dumps(collect_nli(conn), indent=2, sort_keys=True))
        elif args.collection == "scholarly-metadata":
            print(json.dumps(collect_scholarly_metadata(
                conn, PROJECT_ROOT / "config" / "query_matrix.json"
            ), indent=2, sort_keys=True))
        elif args.collection == "internet-archive":
            print(json.dumps(collect_internet_archive(
                conn, PROJECT_ROOT / "config" / "query_matrix.json"
            ), indent=2, sort_keys=True))
        elif args.collection == "repository-metadata":
            print(json.dumps(collect_repository_metadata(
                conn, PROJECT_ROOT / "config" / "query_matrix.json"
            ), indent=2, sort_keys=True))
        elif args.collection == "penn":
            print(json.dumps(collect_penn(conn), indent=2, sort_keys=True))
        elif args.collection == "schoyen":
            print(json.dumps(collect_schoyen(conn), indent=2, sort_keys=True))
        elif args.collection == "waller":
            print(json.dumps(collect_waller(conn), indent=2, sort_keys=True))
    elif args.command == "ingest":
        print("ingested %s records" % load_jsonl(conn, args.path, args.record_type))
    elif args.command == "ingest-list":
        print("ingested %s listed candidates" % load_compact_list(conn, args.path))
    elif args.command == "ingest-bm-enrichment":
        print(json.dumps(load_british_museum_page_mappings(conn, args.path), indent=2, sort_keys=True))
    elif args.command == "ingest-montgomery":
        print(json.dumps(
            ingest_montgomery_review(conn, args.pdf, args.review), indent=2, sort_keys=True
        ))
    elif args.command == "capture":
        print(json.dumps(capture_url(conn, args.url, args.source_id, args.rights_status), indent=2, sort_keys=True))
    elif args.command == "verify-archive":
        problems = verify_archive(conn)
        print(json.dumps({"problems": problems, "valid": not problems}, indent=2))
        if problems:
            raise SystemExit(1)
    elif args.command == "enrich":
        print(json.dumps(run_source_preserving_enrichment(conn), indent=2, sort_keys=True))
    elif args.command == "dedupe":
        print("queued %s candidate pairs" % queue_all(conn, args.threshold))
    elif args.command == "adjudicate-exact":
        print("adjudicated %s exact-identifier pairs" % adjudicate_exact_identifiers(conn))
    elif args.command == "adjudicate-conflicts":
        print(
            "adjudicated %s conflicting-identifier pairs"
            % adjudicate_conflicting_unique_identifiers(conn)
        )
    elif args.command == "adjudicate-concordances":
        print(
            "adjudicated %s explicit concordances" % adjudicate_explicit_concordances(conn)
        )
    elif args.command == "adjudicate-enumerations":
        print(
            "adjudicated %s distinct enumerated-item pairs"
            % adjudicate_distinct_enumerated_source_items(conn)
        )
    elif args.command == "export":
        print(json.dumps(export_all(conn, Path(args.destination)), indent=2, sort_keys=True))
    elif args.command == "report":
        print(json.dumps(write_report(conn, Path(args.destination)), indent=2, sort_keys=True))
    elif args.command == "report-enrichment":
        print(json.dumps(
            write_enrichment_report(conn, Path(args.destination)), indent=2, sort_keys=True
        ))
    elif args.command == "roadmap":
        print(json.dumps(
            write_roadmap(conn, args.config, args.destination), indent=2, sort_keys=True
        ))
    elif args.command == "serve":
        database = conn.execute("PRAGMA database_list").fetchone()[2]
        conn.close()
        from .web import serve
        serve(database, args.host, args.port)
        return
    conn.close()


if __name__ == "__main__":
    main()
