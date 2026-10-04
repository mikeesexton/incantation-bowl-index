"""Mike's personal audit queue; operational state, never a corpus write.

The ledger is an atomic snapshot with an append-only event history. Database
connections are read-only, including the CLI path (no automatic migrations).
"""

import fcntl
import hashlib
import json
import os
import random
import secrets
import sqlite3
import tempfile
from collections import defaultdict
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo

from .db import PROJECT_ROOT, db_path
from .identity import CORE_ORDER, identity_rows
from .proofreading import current_text_reviews
from .presentation import format_dimensions, format_fact_value
from .state import compare_state


DEFAULT_LEDGER = PROJECT_ROOT / "data/private/personal-audit/ledger.json"
DEFAULT_READER = "http://127.0.0.1:8765/"
LOCAL_ZONE = ZoneInfo("America/New_York")
RESULTS = {"no_issues", "followup", "not_finished"}
POLICY = {"cadence": "daily_five", "review_basis": "presented_version"}
OBJECT_COLUMNS = {
    "object_id", "object_a_id", "object_b_id", "from_object_id", "into_object_id",
    "subject_object_id", "target_object_id", "canonical_object_id",
}
CHILD_LINKS = {
    "text_id": "texts", "media_id": "media", "claim_id": "claims",
    "dedupe_id": "dedupe_candidates", "review_id": "claim_conflict_reviews",
}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _now(value=None):
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("Audit time must include a timezone")
    return value.astimezone(timezone.utc)


def _timestamp(value):
    return value.isoformat(timespec="seconds")


def _day(value):
    return value.astimezone(LOCAL_ZONE).date().isoformat()


def _id():
    return "IBI-AUDIT-" + secrets.token_hex(6).upper()


def _event(state, kind, now, **values):
    event = {"id": _id(), "type": kind, "at": _timestamp(now), **values}
    state["events"].append(event)
    return event


def _atomic_write(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".audit-", delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(_json(value) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def _locked(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (path.parent / (path.name + ".lock")).open("a+") as lock:
        os.chmod(lock.name, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            if state is not None and state.get("version") != 1:
                raise ValueError("Unsupported audit ledger version")
            yield state
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


class Evidence:
    """One consistent SQLite read snapshot, including private evidence hashes."""

    def __init__(self, database=None, project_root=None):
        database = Path(database or db_path()).resolve()
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            conn.execute("BEGIN")
            if project_root is not None:
                state = compare_state(conn, project_root)
                if state["status"] != "match":
                    raise ValueError("Corpus state is %s; investigate before preparing an audit" %
                                     state["status"])
            self.identities = identity_rows(conn)
            self.text_reviews = current_text_reviews(conn)
            self.tables = {
                name: [dict(row) for row in conn.execute('SELECT * FROM "%s"' % name)]
                for (name,) in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' AND name<>'schema_migrations' ORDER BY name"
                )
            }
        self.by_members = {tuple(json.loads(row["member_ids_json"])): row
                           for row in self.identities if row["record_status"] != "rejected"}
        self.sources = {row["id"]: row for row in self.tables["sources"]}
        self.snapshots = {}
        # Index once: otherwise daily reconciliation scans the full corpus per bowl.
        self.by_object = defaultdict(lambda: defaultdict(list))
        self.by_identity = defaultdict(lambda: defaultdict(list))
        self.by_source = defaultdict(lambda: defaultdict(list))
        self.children = defaultdict(lambda: defaultdict(list))
        self.appearances = {row["id"]: row for row in self.tables["appearances"]}
        for table, rows in self.tables.items():
            for row in rows:
                object_keys = OBJECT_COLUMNS & row.keys()
                child_keys = CHILD_LINKS.keys() & row.keys()
                if table == "objects":
                    self.by_object[row["id"]][table].append(row)
                elif object_keys:
                    for key in object_keys:
                        self.by_object[row[key]][table].append(row)
                elif "identity_id" in row:
                    self.by_identity[row["identity_id"]][table].append(row)
                elif child_keys:
                    for key in child_keys:
                        self.children[(CHILD_LINKS[key], row[key])][table].append(row)
                elif table != "appearances":
                    for key in row:
                        if key == "source_id" or key.endswith("_source_id"):
                            self.by_source[row[key]][table].append(row)

    def snapshot(self, members):
        members = tuple(members)
        if members in self.snapshots:
            return self.snapshots[members]
        identity = self.by_members.get(members)
        if identity is None:
            return None
        selected = defaultdict(dict)

        def add(table, rows):
            for row in rows:
                selected[table][_json(row)] = row

        for member in members:
            for table, rows in self.by_object[member].items():
                add(table, rows)
        for table, rows in self.by_identity[identity["identity_id"]].items():
            add(table, rows)
        for link in selected["appearance_object_links"].values():
            appearance = self.appearances.get(link["appearance_id"])
            if appearance:
                add("appearances", [appearance])
        # Children may themselves have children (dedupe evidence and review history).
        for table in list(selected):
            for row in list(selected[table].values()):
                for child_table, rows in self.children[(table, row.get("id"))].items():
                    add(child_table, rows)
        source_ids = {row[key] for rows in selected.values() for row in rows.values()
                      for key in row if key == "source_id" or key.endswith("_source_id")}
        for source_id in source_ids:
            if source_id in self.sources:
                add("sources", [self.sources[source_id]])
            for table, rows in self.by_source[source_id].items():
                add(table, rows)
        payload = {table: sorted(rows.values(), key=_json) for table, rows in selected.items()}
        snapshot = {"fingerprint": _digest({"identity": identity, "evidence": payload}),
                    "identity": identity, "evidence": payload}
        self.snapshots[members] = snapshot
        return snapshot

    def card(self, entry, reader_base):
        snapshot = self.snapshot(entry["members"])
        if snapshot is None:
            return {"item_id": entry["id"], "identity_id": entry["identity_id"],
                    "label": entry["label"], "blocked": "Identity membership or scope changed"}
        identity, rows = snapshot["identity"], snapshot["evidence"]
        facts = []
        preferred = {
            "current_location", "current_or_reported_collection", "dating", "material",
            "dimensions", "script", "inscription_language", "findspot", "provenance",
            "client", "clients", "text_purpose", "condition",
        }
        claims = rows.get("claims", [])
        superseded = {row.get("supersedes_claim_id") for row in claims}
        for claim in claims:
            if claim["field"] not in preferred or claim["id"] in superseded:
                continue
            source = self.sources.get(claim["source_id"], {})
            value = (claim.get("value_text") or claim.get("value_json") or
                     claim.get("normalized_value") or "")[:240]
            if claim["field"] == "dimensions":
                value = format_dimensions(value)
            value = format_fact_value(value)
            facts.append({"claim_id": claim["id"], "field": claim["field"],
                          "value": value,
                          "certainty": claim.get("certainty"),
                          "citation": source.get("citation") or source.get("title"),
                          "source_url": source.get("url"), "locator": claim.get("locator")})
        concerns = []
        for key, label in (("conflict_fields_json", "Conflicting claims"),
                           ("untriaged_conflict_fields_json", "Untriaged differences"),
                           ("stale_conflict_fields_json", "Stale conflict reviews")):
            fields = json.loads(identity[key])
            if fields:
                concerns.append(label + ": " + ", ".join(fields))
        for review in rows.get("dedupe_candidates", []):
            if review["status"] in {"unresolved", "pending"}:
                concerns.append("Identity review pending: " + review["id"])
        unchecked = [text["id"] for text in rows.get("texts", [])
                     if self.text_reviews.get(text["id"], {}).get("status") != "reading_text_checked"]
        if unchecked:
            concerns.append("Text rows without a current complete source check: " + ", ".join(unchecked))
        missing_locators = [claim["id"] for claim in claims if not claim.get("locator")]
        if missing_locators:
            concerns.append("Claims without a recorded locator: " + ", ".join(missing_locators))
        if identity["record_status"] == "candidate":
            concerns.append("Provisional candidate; identity is not confirmed")
        return {
            "item_id": entry["id"], "identity_id": identity["identity_id"],
            "members": entry["members"], "label": identity["display_name"],
            "record_status": identity["record_status"],
            "fingerprint": snapshot["fingerprint"],
            "reader_url": reader_base.rstrip("/") + "/#/explore/" +
                          quote(identity["identity_id"], safe=""),
            "overview": {"collection": identity["display_collection"],
                         "date": identity["display_date"], "language": identity["display_language"],
                         "sources": identity["source_count"], "appearances": identity["appearance_count"],
                         "texts": identity["text_count"], "images": identity["media_count"]},
            "missing": [field for field in CORE_ORDER if not identity["has_" + field]],
            "concerns": concerns, "facts": facts,
            "sources": [{"id": source["id"], "citation": source["citation"] or source["title"],
                         "url": source["url"]} for source in rows.get("sources", [])],
            "appearances": [{"source_id": row["source_id"], "locator": row["locator"]}
                            for row in rows.get("appearances", [])],
        }


def _entry(snapshot, now):
    identity = snapshot["identity"]
    return {"id": _id(), "identity_id": identity["identity_id"],
            "members": json.loads(identity["member_ids_json"]), "label": identity["display_name"],
            "initial_fingerprint": snapshot["fingerprint"], "status": "pending",
            "added_at": _timestamp(now)}


def _require(state):
    if state is None:
        raise ValueError("No personal audit initialized; run audit-init first")


def initialize(path=DEFAULT_LEDGER, database=None, reader_base=DEFAULT_READER,
               now=None, project_root=None):
    now = _now(now)
    parsed = urlparse(reader_base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Use the private localhost reader; remote Mike Access is not commissioned")
    with _locked(path) as previous:
        if previous is not None:
            return status(previous)
        evidence = Evidence(database, project_root)
        roster = [_entry(evidence.snapshot(members), now) for members in evidence.by_members]
        seed = secrets.randbits(128)
        random.Random(seed).shuffle(roster)
        state = {"version": 1, "started_at": _timestamp(now), "timezone": LOCAL_ZONE.key,
                 "batch_size": 5, "shuffle_seed": str(seed), "reader_base": reader_base,
                 "roster": roster, "batches": [], "events": [], "issues": [],
                 "policy": POLICY.copy(), "daily_packets": {}}
        _event(state, "initialized", now, count=len(roster))
        _atomic_write(Path(path), state)
        return status(state)


def _issue(state, now, key, kind, **values):
    old = next((issue for issue in state["issues"] if issue["key"] == key and
                issue["status"] == "open"), None)
    if old:
        return old
    issue = {"id": _id(), "key": key, "kind": kind, "status": "open",
             "created_at": _timestamp(now), **values}
    state["issues"].append(issue)
    _event(state, "issue_opened", now, issue=issue.copy())
    return issue


def _reconcile(state, evidence, now):
    known = {tuple(entry["members"]) for entry in state["roster"] if entry["status"] != "retired"}
    for members in sorted(evidence.by_members):
        if members not in known:
            entry = _entry(evidence.snapshot(members), now)
            state["roster"].append(entry)
            _event(state, "roster_appended", now, item=entry.copy())
    for entry in state["roster"]:
        if entry["status"] == "retired":
            continue
        snapshot = evidence.snapshot(entry["members"])
        if snapshot is None:
            replacements = [row["id"] for row in state["roster"]
                            if row["id"] != entry["id"] and row["status"] != "retired" and
                            set(row["members"]) & set(entry["members"]) and
                            evidence.snapshot(row["members"]) is not None]
            _issue(state, now, entry["id"] + ":membership", "membership_or_scope_changed",
                   item_id=entry["id"], replacements=replacements)
        elif entry["status"] == "completed" and snapshot["fingerprint"] != entry["review_fingerprint"]:
            _issue(state, now, entry["id"] + ":evidence:" + snapshot["fingerprint"],
                   "evidence_changed_after_review", item_id=entry["id"],
                   fingerprint=snapshot["fingerprint"])


def _items(state):
    return {entry["id"]: entry for entry in state["roster"]}


def _active_batch(state):
    items = _items(state)
    return next((batch for batch in reversed(state["batches"])
                 if any(items[item_id]["status"] == "pending" for item_id in batch["item_ids"])), None)


def _number(batch, item_id):
    return batch.get("numbers", {}).get(item_id, batch["item_ids"].index(item_id) + 1)


def _adopt_policy(state, now):
    # Add operational metadata without rewriting the saved roster or past packets.
    if state.get("policy") != POLICY:
        _event(state, "audit_policy_updated", now, previous=state.get("policy"),
               policy=POLICY.copy())
        state["policy"] = POLICY.copy()
    state.setdefault("daily_packets", {})


def _daily_batch(state, today, now):
    """Allocate once per day; unfinished slots keep their numbers when refilled."""
    items = _items(state)
    packets = state["daily_packets"]
    if today in packets:
        return next((b for b in state["batches"] if b["number"] == packets[today]), None)
    active = _active_batch(state)
    carried = [item_id for item_id in (active or {}).get("item_ids", [])
               if items[item_id]["status"] == "pending"]
    waiting = [entry["id"] for entry in state["roster"]
               if entry["status"] == "pending" and entry["id"] not in carried]
    if active and (len(carried) == state["batch_size"] or not waiting):
        batch = active
    elif carried or waiting:
        slots = {_number(active, item_id): item_id for item_id in carried}
        for position in range(1, state["batch_size"] + 1):
            if position not in slots and waiting:
                slots[position] = waiting.pop(0)
        batch = {"number": len(state["batches"]) + 1, "issued_on": today,
                 "issued_at": _timestamp(now),
                 "item_ids": [slots[position] for position in sorted(slots)],
                 "numbers": {item_id: position for position, item_id in slots.items()},
                 "carried_ids": carried, "presentations": []}
        if active:
            active.setdefault("superseded_on", today)
        state["batches"].append(batch)
        _event(state, "batch_issued", now, batch=batch["number"], items=batch["item_ids"],
               carried_ids=carried)
    else:
        batch = None
    packets[today] = batch["number"] if batch else None
    _event(state, "daily_packet_allocated", now, date=today, batch=packets[today])
    return batch


def _complete_batches(state, now):
    items = _items(state)
    review_days = {event["id"]: event["date"] for event in state["events"]
                   if event["type"] == "review_recorded"}
    for batch in state["batches"]:
        if not batch.get("completed_on") and all(
                items[item_id]["status"] != "pending" for item_id in batch["item_ids"]):
            batch["completed_on"] = max(
                items[item_id].get("reviewed_on") or
                review_days.get(items[item_id].get("review_id")) or _day(now)
                for item_id in batch["item_ids"])
            _event(state, "batch_completed", now, batch=batch["number"],
                   completed_on=batch["completed_on"])


def status(state):
    _require(state)
    completed = sum(entry["status"] == "completed" for entry in state["roster"])
    remaining = sum(entry["status"] == "pending" for entry in state["roster"])
    open_issues = [issue for issue in state["issues"] if issue["status"] == "open"]
    return {"reviewed": completed, "remaining": remaining,
            "retired": sum(entry["status"] == "retired" for entry in state["roster"]),
            "total": len(state["roster"]), "outstanding_followups": len(open_issues),
            "issues": open_issues, "queue_complete": remaining == 0,
            "complete": remaining == 0 and not open_issues,
            "active_batch": (_active_batch(state) or {}).get("number"),
            "reader_base": state["reader_base"], "started_at": state["started_at"],
            "reminder": state.get("reminder")}


def read_status(path=DEFAULT_LEDGER):
    with _locked(path) as state:
        return status(state)


def configure_reminder(automation_id, path=DEFAULT_LEDGER, now=None):
    """Retain the app's automation identity so the completion run can stop it."""
    now = _now(now)
    with _locked(path) as state:
        _require(state)
        settings = {"automation_id": automation_id, "time": "09:00", "timezone": LOCAL_ZONE.key}
        if state.get("reminder") != settings:
            state["reminder"] = settings
            _event(state, "reminder_configured", now, settings=settings.copy())
            _atomic_write(Path(path), state)
        return settings


def show(reference, batch_number, path=DEFAULT_LEDGER, database=None, now=None, project_root=None):
    """Present an already-issued bowl again, including a completed bowl's new evidence."""
    now = _now(now)
    with _locked(path) as state:
        _require(state)
        entry, batch = _resolve(state, reference, batch_number)
        if entry["status"] == "retired":
            raise ValueError("Retired item; inspect its replacement instead")
        evidence = Evidence(database, project_root)
        _reconcile(state, evidence, now)
        card = evidence.card(entry, state["reader_base"])
        card["number"] = _number(batch, entry["id"])
        card["changed_since_previous_presentation"] = any(
            previous.get("item_id") == entry["id"] and previous.get("fingerprint") != card.get("fingerprint")
            for presentation in batch["presentations"] for previous in presentation["cards"])
        attempt = _event(state, "manual_presentation", now, item_id=entry["id"], batch=batch_number)
        batch["presentations"].append({"attempt_id": attempt["id"], "at": _timestamp(now), "cards": [card]})
        _atomic_write(Path(path), state)
        return {"date": _day(now), "attempt_id": attempt["id"], "batch": batch_number,
                "carryover": False, "cards": [card], "no_completed_review_recorded": [],
                "progress": status(state)}


def _missed_days(state, today, now):
    recorded_days = {event["date"] for event in state["events"]
                     if event["type"] == "no_completed_review_recorded"}
    reviews = {event["date"] for event in state["events"]
               if event["type"] == "review_recorded" and event["result"] != "not_finished"}
    for batch in state["batches"]:
        first = datetime.fromisoformat(batch["issued_on"]).date()
        last = datetime.fromisoformat(min(batch.get("completed_on") or today,
                                          batch.get("superseded_on") or today)).date()
        day = first
        while day < last:
            value = day.isoformat()
            if value not in reviews and value not in recorded_days:
                _event(state, "no_completed_review_recorded", now, date=value)
                recorded_days.add(value)
            day += timedelta(days=1)
    # A delayed explicit response can establish a review on a previously blank day.
    # Keep earlier events as history, but do not repeat the superseded day claim.
    return sorted(recorded_days - reviews)


def prepare(path=DEFAULT_LEDGER, database=None, now=None, project_root=None):
    """Prepare at most one batch per local day; repeat calls are safe."""
    now = _now(now)
    today = _day(now)
    with _locked(path) as state:
        _require(state)
        attempt = _event(state, "delivery_attempt", now, date=today, outcome="preparing")
        try:
            evidence = Evidence(database, project_root)
            _adopt_policy(state, now)
            _reconcile(state, evidence, now)
            missed = _missed_days(state, today, now)
            batch = _daily_batch(state, today, now)
            cards = []
            if batch:
                items = _items(state)
                for item_id in batch["item_ids"]:
                    if items[item_id]["status"] == "pending":
                        card = evidence.card(items[item_id], state["reader_base"])
                        card["number"] = _number(batch, item_id)
                        card["changed_since_previous_presentation"] = any(
                            old.get("item_id") == item_id and old.get("fingerprint") != card.get("fingerprint")
                            for prior in state["batches"] for presentation in prior["presentations"]
                            for old in presentation["cards"]
                        )
                        cards.append(card)
                batch["presentations"].append({"attempt_id": attempt["id"],
                                              "at": _timestamp(now), "cards": cards})
            attempt["outcome"] = "prepared"
            result = {"date": today, "attempt_id": attempt["id"],
                      "batch": batch["number"] if batch else None,
                      "carryover": bool(batch and (batch["issued_on"] < today or batch.get("carried_ids"))),
                      "no_completed_review_recorded": missed,
                      "cards": cards, "progress": status(state)}
            _atomic_write(Path(path), state)
            return result
        except (OSError, sqlite3.Error, ValueError) as exc:
            # Do not persist a partly reconciled queue when a read or rendering fails.
            original = json.loads(Path(path).read_text(encoding="utf-8"))
            failure = _event(original, "delivery_attempt", now, date=today,
                             outcome="failed", error=str(exc))
            _atomic_write(Path(path), original)
            return {"date": today, "attempt_id": failure["id"], "error": str(exc),
                    "cards": [], "progress": status(original)}


def _resolve(state, reference, batch_number=None):
    batch = next((batch for batch in state["batches"] if batch["number"] == batch_number), None)
    if batch is None:
        raise ValueError("Specify the batch number shown to Mike")
    items = _items(state)
    if str(reference).isdigit():
        position = int(reference)
        matching = [item_id for item_id in batch["item_ids"] if _number(batch, item_id) == position]
        if len(matching) != 1:
            raise ValueError("Bowl number is outside this batch")
        return items[matching[0]], batch
    matches = [items[item_id] for item_id in batch["item_ids"] if reference in
               [item_id, items[item_id]["identity_id"], *items[item_id]["members"]]]
    if len(matches) != 1:
        raise ValueError("Reference must identify exactly one bowl in the specified batch")
    return matches[0], batch


def record(reference, result, fingerprint, batch_number, notes="", path=DEFAULT_LEDGER,
           database=None, now=None, project_root=None, request_id=None, reviewed_on=None):
    """Only call for Mike's explicit personal review; never infer completion."""
    now = _now(now)
    if result not in RESULTS:
        raise ValueError("Unknown personal review result")
    if result == "followup" and not notes.strip():
        raise ValueError("A follow-up needs Mike's notes")
    if not fingerprint:
        raise ValueError("Use the fingerprint from the presentation Mike reviewed")
    review_day = date.fromisoformat(reviewed_on).isoformat() if reviewed_on else _day(now)
    if review_day > _day(now):
        raise ValueError("Review date cannot be in the future")
    with _locked(path) as state:
        _require(state)
        entry, batch = _resolve(state, reference, batch_number)
        payload = {"item_id": entry["id"], "batch": batch_number, "result": result,
                   "fingerprint": fingerprint, "notes": notes, "request_id": request_id}
        if reviewed_on:
            payload["reviewed_on"] = review_day
        # Explicit request IDs distinguish deliberate later reviews from retry delivery.
        old = next((event for event in reversed(state["events"])
                    if event["type"] == "review_recorded" and event.get("payload") == payload), None)
        if old:
            return {"review_id": old["id"], "replayed": True, "progress": status(state)}
        if entry["status"] == "retired":
            raise ValueError("Retired item; review the replacement identity instead")
        presented = [card for presentation in batch["presentations"] for card in presentation["cards"]
                     if card["item_id"] == entry["id"] and card.get("fingerprint") == fingerprint]
        if not presented:
            raise ValueError("This record version has not been presented in the specified batch")
        first_shown = min(_day(datetime.fromisoformat(presentation["at"]))
                          for presentation in batch["presentations"]
                          if any(card.get("fingerprint") == fingerprint and card["item_id"] == entry["id"]
                                 for card in presentation["cards"]))
        if review_day < first_shown:
            raise ValueError("Review date precedes the shown record version")
        evidence = Evidence(database, project_root)
        current = evidence.snapshot(entry["members"])
        _adopt_policy(state, now)
        event = _event(state, "review_recorded", now, date=review_day,
                       result=result, payload=payload, reviewed_by="Mike")
        if result != "not_finished":
            entry["status"] = "completed"
            entry["review_fingerprint"] = fingerprint
            entry["review_id"] = event["id"]
            entry["reviewed_on"] = review_day
            for issue in state["issues"]:
                if issue["status"] == "open" and issue.get("item_id") == entry["id"] and \
                        issue["kind"] == "evidence_changed_after_review" and (
                            issue.get("fingerprint") == fingerprint or
                            (current is not None and current["fingerprint"] == fingerprint)):
                    issue["status"] = "resolved"
                    _event(state, "issue_resolved_by_review", now, issue_id=issue["id"], review_id=event["id"])
            if result == "followup":
                _issue(state, now, "review:" + event["id"], "mike_followup", item_id=entry["id"],
                       review_id=event["id"], notes=notes)
            _reconcile(state, evidence, now)
            _complete_batches(state, now)
        _atomic_write(Path(path), state)
        return {"review_id": event["id"], "replayed": False, "progress": status(state)}


def close_issue(issue_id, notes, path=DEFAULT_LEDGER, database=None, now=None,
                retire=False, project_root=None):
    """Mike's explicit operational resolution; does not decide corpus identity."""
    now = _now(now)
    if not notes.strip():
        raise ValueError("Record Mike's rationale for resolving this issue")
    with _locked(path) as state:
        _require(state)
        issue = next((issue for issue in state["issues"] if issue["id"] == issue_id), None)
        if issue is None or issue["status"] != "open":
            raise ValueError("Issue is not open")
        entry = _items(state).get(issue.get("item_id"))
        if issue["kind"] == "membership_or_scope_changed":
            if not retire:
                raise ValueError("Explicit --retire is required for a replaced or rejected roster item")
            evidence = Evidence(database, project_root)
            if evidence.snapshot(entry["members"]) is not None:
                raise ValueError("Original membership still eligible; do not retire it")
            _reconcile(state, evidence, now)
            entry["status"] = "retired"
            for batch in state["batches"]:
                if entry["id"] in batch["item_ids"] and "completed_on" not in batch and all(
                        _items(state)[item_id]["status"] != "pending" for item_id in batch["item_ids"]):
                    batch["completed_on"] = _day(now)
                    _event(state, "batch_completed", now, batch=batch["number"])
        elif retire:
            raise ValueError("Only changed membership/scope items can be retired")
        issue["status"] = "resolved"
        _event(state, "issue_resolved", now, issue_id=issue_id, notes=notes,
               retired_item=entry["id"] if retire else None, resolved_by="Mike")
        _atomic_write(Path(path), state)
        return status(state)


def delivery(attempt_id, outcome, notes="", path=DEFAULT_LEDGER, now=None):
    if outcome not in {"reported", "failed"}:
        raise ValueError("Delivery outcome must be reported or failed")
    now = _now(now)
    with _locked(path) as state:
        _require(state)
        if not any(event["id"] == attempt_id and event["type"] in {"delivery_attempt", "manual_presentation"}
                   for event in state["events"]):
            raise ValueError("Unknown preparation attempt")
        values = {"attempt_id": attempt_id, "outcome": outcome, "notes": notes}
        if not any(event["type"] == "delivery_result" and
                   all(event.get(key) == value for key, value in values.items()) for event in state["events"]):
            _event(state, "delivery_result", now, **values)
            _atomic_write(Path(path), state)
        return values


def markdown(packet):
    if packet.get("error"):
        return "The daily audit could not be prepared: %s. Your place is saved." % packet["error"]
    progress = packet["progress"]
    lines = ["Daily bowl audit — " + packet["date"],
             "%s reviewed · %s remaining · %s outstanding follow-ups" %
             (progress["reviewed"], progress["remaining"], progress["outstanding_followups"]), ""]
    if not packet["cards"]:
        lines.append("The audit queue is complete." if progress["queue_complete"] else
                     "Today's batch is finished. The next five arrive tomorrow.")
    else:
        lines.append("Batch %s%s" % (packet["batch"], " — carried forward" if packet["carryover"] else ""))
    for card in packet["cards"]:
        lines += ["", "%s. %s — %s" % (card["number"], card["label"], card["identity_id"])]
        if card.get("blocked"):
            lines.append("Needs reconciliation: " + card["blocked"])
            continue
        lines.append("[Full private record](%s)" % card["reader_url"])
        overview = card["overview"]
        lines.append("Status: %s. %s source(s), %s appearance(s), %s text(s), %s image record(s)." %
                     (card["record_status"], overview["sources"], overview["appearances"],
                      overview["texts"], overview["images"]))
        if card["changed_since_previous_presentation"]:
            lines.append("Record changed since an earlier presentation; inspect this version.")
        lines.append("Missing recorded fields: " + (", ".join(card["missing"]) or "none"))
        lines.extend(card["concerns"])
        for fact in card["facts"][:8]:
            lines.append("- %s: %s — %s%s" % (fact["field"], fact["value"], fact["citation"],
                                               "; " + fact["locator"] if fact["locator"] else ""))
        if not card["facts"]:
            for source in card["sources"][:2]:
                locators = [appearance["locator"] for appearance in card["appearances"]
                            if appearance["source_id"] == source["id"] and appearance["locator"]]
                lines.append("Source: %s%s" % (source["citation"],
                                              "; " + ", ".join(locators) if locators else ""))
    missed = packet["no_completed_review_recorded"]
    if missed:
        lines += ["", "No completed review recorded: " + ", ".join(missed[-7:]) +
                  (" (earlier dates retained in the ledger)" if len(missed) > 7 else "")]
    if packet["cards"]:
        lines += ["", "Reply with the batch and bowl numbers: reviewed—no issues noticed; "
                  "reviewed—follow-up needed, with notes; or not finished."]
    return "\n".join(lines)
