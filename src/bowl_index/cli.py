import argparse
import json
import sqlite3
from pathlib import Path

from .archive import capture_file, capture_url, verify_archive
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
from .state import compare_state, write_state
from .roadmap import write_roadmap
from .proofreading import apply_proofreading
from .rights import apply_rights_batch
from .public_export import export_public
from .publication import apply_publication_batch, publication_metrics
from .acquisitions import write_acquisition_report
from .scholarship import apply_scope_batch
from .publications import apply_publication_registry, publication_object_counts
from .publication_assessments import apply_publication_assessments
from .claim_corrections import apply_locator_corrections
from .source_corrections import apply_source_corrections
from .text_metadata import apply_text_metadata
from .cohort import write_montgomery_cohort, apply_montgomery_register
from .concordance import apply_concordance_review
from .relationships import apply_relationship_review
from .documents import apply_document_assessments
from .vault import validate_rich_text_package
from .backup import private_backup_readiness
from .accuracy_audit import apply_accuracy_audit


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
    accuracy_audit = sub.add_parser(
        "ingest-accuracy-audit", help="ingest evidence-bound QA-003 identity accuracy reviews"
    )
    accuracy_audit.add_argument("path")
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
    approve_texts = sub.add_parser(
        "ingest-text-publication", help="apply evidence-bound text publication decisions"
    )
    approve_texts.add_argument("path")
    pubreg = sub.add_parser(
        "ingest-publication-registry", help="resolve publication keys to the publication they designate"
    )
    pubreg.add_argument("path")
    pub_assess = sub.add_parser(
        "ingest-publication-assessments",
        help="record evidence-bound publication links and no-known-edition findings",
    )
    pub_assess.add_argument("path")
    scope = sub.add_parser("ingest-source-scope", help="record what kind of work a source is")
    scope.add_argument("path")
    documents = sub.add_parser(
        "ingest-document-assessment",
        help="record evidence-bound document completeness and transformation states",
    )
    documents.add_argument("path")
    rich_text = sub.add_parser(
        "validate-rich-text-package",
        help="validate a private hash-bound TEI package without importing its text",
    )
    rich_text.add_argument("path")
    sub.add_parser(
        "backup-readiness",
        help="audit encrypted local and off-device private-vault backup readiness",
    )
    rights = sub.add_parser("ingest-rights-review", help="apply evidence-bound media-rights decisions")
    rights.add_argument("path")
    corrections = sub.add_parser("ingest-locator-corrections", help="apply citation-pointer repairs with immutable originals")
    corrections.add_argument("path")
    source_corrections = sub.add_parser(
        "ingest-source-corrections", help="apply bibliographic repairs with immutable originals"
    )
    source_corrections.add_argument("path")
    text_metadata = sub.add_parser(
        "ingest-text-metadata", help="repair text labels and locators with retained originals"
    )
    text_metadata.add_argument("path")
    object_scope = sub.add_parser(
        "ingest-object-scope", help="record researcher decisions that an object is outside the corpus"
    )
    object_scope.add_argument("path")
    register = sub.add_parser("ingest-montgomery-register", help="append scan-checked register claims")
    register.add_argument("path")
    cohort = sub.add_parser("report-montgomery-cohort", help="account for all forty main Montgomery texts")
    cohort.add_argument("--register", default=str(PROJECT_ROOT / "research/enrichment/montgomery_register_checked_2026-09-04.json"))
    cohort.add_argument("--destination", default=str(PROJECT_ROOT / "data/reports/montgomery_cohort_current.md"))
    acq = sub.add_parser("report-acquisitions", help="what we hold and what we still need to read")
    acq.add_argument("--destination", default=str(PROJECT_ROOT / "data/reports/acquisition_status.md"))
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
    deposit = sub.add_parser(
        "deposit", help="archive a researcher-supplied local document by content hash"
    )
    deposit.add_argument("path")
    deposit.add_argument("--source-id")
    deposit.add_argument("--rights-status", default="unknown")
    deposit.add_argument("--note")
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
    state = sub.add_parser(
        "state", help="compare the working database against the state recorded in Git"
    )
    state.add_argument("--write", action="store_true", help="record the current state")
    state.add_argument("--agent", help="who is recording the state, e.g. claude or codex")
    state.add_argument("--note", help="one line on what this session changed")
    state.add_argument(
        "--check", action="store_true", help="exit non-zero when the database has drifted"
    )
    serve_parser = sub.add_parser("serve", help="run the private localhost research console")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    for command, help_text in (
        ("audit-init", "initialize Mike's saved personal audit queue"),
        ("audit-daily", "prepare five bowls or unfinished carryover, with a read-only corpus"),
        ("audit-status", "show personal audit progress and open follow-ups"),
        ("audit-record", "record Mike's explicit personal review of a presented bowl"),
        ("audit-resolve", "record Mike's resolution of an operational audit issue"),
        ("audit-delivery", "record reporting or failure of a prepared daily packet"),
        ("audit-show", "show a previously issued bowl again for an explicit recheck"),
        ("audit-schedule", "save the app reminder's identity in the private ledger"),
    ):
        audit = sub.add_parser(command, help=help_text)
        audit.add_argument("--ledger", help="override the private operational audit ledger")
        audit.add_argument("--format", choices=("json", "markdown"), default="json")
        if command == "audit-init":
            audit.add_argument("--reader-base", default="http://127.0.0.1:8765/")
        elif command == "audit-record":
            audit.add_argument("bowl", help="bowl number, identity ID, object ID, or audit item ID")
            audit.add_argument("--batch", type=int, required=True)
            audit.add_argument("--result", choices=("no_issues", "followup", "not_finished"), required=True)
            audit.add_argument("--fingerprint", required=True)
            audit.add_argument("--notes", default="")
            audit.add_argument("--request-id", help="stable ID for retry-safe recording of a user message")
        elif command == "audit-resolve":
            audit.add_argument("issue")
            audit.add_argument("--notes", required=True)
            audit.add_argument("--retire", action="store_true")
        elif command == "audit-delivery":
            audit.add_argument("attempt")
            audit.add_argument("--outcome", choices=("reported", "failed"), required=True)
            audit.add_argument("--notes", default="")
        elif command == "audit-show":
            audit.add_argument("bowl")
            audit.add_argument("--batch", type=int, required=True)
        elif command == "audit-schedule":
            audit.add_argument("automation_id")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    # Audit preparation must never enter connect()/migrate(): even a new schema
    # migration must not turn an unattended reminder into a corpus write.
    if args.command.startswith("audit-"):
        from . import personal_audit as audit
        options = {"path": Path(args.ledger) if args.ledger else audit.DEFAULT_LEDGER}
        corpus = {"database": args.db, "project_root": PROJECT_ROOT if not args.db else None}
        try:
            if args.command == "audit-init":
                result = audit.initialize(reader_base=args.reader_base, **options, **corpus)
            elif args.command == "audit-daily":
                result = audit.prepare(**options, **corpus)
            elif args.command == "audit-status":
                result = audit.read_status(**options)
            elif args.command == "audit-record":
                result = audit.record(args.bowl, args.result, args.fingerprint, args.batch,
                                      notes=args.notes, request_id=args.request_id, **options, **corpus)
            elif args.command == "audit-resolve":
                result = audit.close_issue(args.issue, args.notes, retire=args.retire, **options, **corpus)
            elif args.command == "audit-delivery":
                result = audit.delivery(args.attempt, args.outcome, notes=args.notes, **options)
            elif args.command == "audit-show":
                result = audit.show(args.bowl, args.batch, **options, **corpus)
            elif args.command == "audit-schedule":
                result = audit.configure_reminder(args.automation_id, **options)
            if args.format == "markdown" and args.command in {"audit-daily", "audit-show"}:
                print(audit.markdown(result))
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            if result.get("error"):
                raise SystemExit(1)
        except (ValueError, OSError, sqlite3.Error) as exc:
            raise SystemExit("Personal audit: %s" % exc) from exc
        return
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
    elif args.command == "ingest-accuracy-audit":
        print(json.dumps(
            apply_accuracy_audit(conn, args.path, PROJECT_ROOT), indent=2, sort_keys=True
        ))
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
    elif args.command == "ingest-text-publication":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_publication_batch(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-publication-registry":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_publication_registry(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-publication-assessments":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_publication_assessments(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-source-scope":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_scope_batch(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-document-assessment":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(
            apply_document_assessments(conn, review, PROJECT_ROOT), indent=2, sort_keys=True
        ))
    elif args.command == "validate-rich-text-package":
        print(json.dumps(
            validate_rich_text_package(conn, args.path), indent=2, sort_keys=True
        ))
    elif args.command == "backup-readiness":
        print(json.dumps(
            private_backup_readiness(PROJECT_ROOT), indent=2, sort_keys=True
        ))
    elif args.command == "ingest-rights-review":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_rights_batch(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-locator-corrections":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_locator_corrections(conn, review, PROJECT_ROOT), indent=2, sort_keys=True))
    elif args.command == "ingest-text-metadata":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_text_metadata(conn, review, PROJECT_ROOT), indent=2, sort_keys=True))
    elif args.command == "ingest-object-scope":
        from .object_scope import apply_object_scope_reviews
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_object_scope_reviews(conn, review), indent=2, sort_keys=True))
    elif args.command == "ingest-source-corrections":
        review = json.loads(Path(args.path).read_text())
        print(json.dumps(apply_source_corrections(conn, review, PROJECT_ROOT), indent=2, sort_keys=True))
    elif args.command == "ingest-montgomery-register":
        print(json.dumps(apply_montgomery_register(conn, args.path), indent=2, sort_keys=True))
    elif args.command == "report-montgomery-cohort":
        print(json.dumps(write_montgomery_cohort(conn, args.register, args.destination), indent=2, sort_keys=True))
    elif args.command == "report-acquisitions":
        print(json.dumps(write_acquisition_report(conn, args.destination), indent=2, sort_keys=True))
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
    elif args.command == "deposit":
        print(json.dumps(capture_file(
            conn, args.path, args.source_id, args.rights_status, args.note
        ), indent=2, sort_keys=True))
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
    elif args.command == "state":
        if args.write:
            written = write_state(conn, PROJECT_ROOT, args.agent, args.note)
            print(json.dumps({
                "recorded_at": written["recorded_at"],
                "recorded_by": written["recorded_by"],
                "corpus_digest": written["corpus_digest"],
            }, indent=2, sort_keys=True))
        else:
            result = compare_state(conn, PROJECT_ROOT)
            print(json.dumps(result, indent=2, sort_keys=True))
            if args.check and result["status"] != "match":
                conn.close()
                raise SystemExit(1)
    elif args.command == "serve":
        database = conn.execute("PRAGMA database_list").fetchone()[2]
        conn.close()
        from .web import serve
        serve(database, args.host, args.port)
        return
    conn.close()


if __name__ == "__main__":
    main()
