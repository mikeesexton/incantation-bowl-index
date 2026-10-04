"""Prepare an append-only private manifest from existing Penn appearances.

Reads the corpus; never ingests, changes identities, or follows accession links.
Retains HTML and HTTP/robots receipts under the private output directory. Resume
uses those saved bytes, rather than replacing evidence beneath a manifest.
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bowl_index.archive import USER_AGENT, _open
from bowl_index.db import connect
from bowl_index.penn_metadata import penn_fields, penn_metadata_claims
from bowl_index.robots import can_fetch


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha(body):
    return hashlib.sha256(body).hexdigest()


def prepare(conn, output, delay=0.3):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    policies = {}

    def policy(url):
        host = urlsplit(url)
        if host.scheme != "https" or host.netloc != "collections.penn.museum":
            raise ValueError("Unexpected catalogue host: " + url)
        if host.netloc not in policies:
            target = "https://" + host.netloc + "/robots.txt"
            request = urllib.request.Request(target, headers={"User-Agent": USER_AGENT})
            try:
                response = urllib.request.urlopen(request, timeout=30)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                body = response.read()
                status = response.code
            receipt = dict(url=target, status_code=status, body_sha256=sha(body), retrieved_at=now())
            (output / "robots.body").write_bytes(body)
            (output / "robots.json").write_text(json.dumps(receipt, indent=2))
            policies[host.netloc] = status, body
        status, body = policies[host.netloc]
        if status == 200:
            allowed = can_fetch(body.decode("utf-8", "replace"), USER_AGENT, url)
        else:
            allowed = 400 <= status < 500 and status not in (401, 403)
        if not allowed:
            raise PermissionError("Robots denied or unverifiable: " + url)

    records, inventory, failures = [], [], []
    rows = conn.execute("SELECT a.*,s.url AS source_url FROM appearances a JOIN sources s "
                        "ON s.id=a.source_id WHERE s.publisher='Penn Museum' "
                        "AND s.url LIKE 'https://collections.penn.museum/collections/object/%' "
                        "AND EXISTS (SELECT 1 FROM appearance_object_links l JOIN objects o "
                        "ON o.id=l.object_id WHERE l.appearance_id=a.id "
                        "AND l.relation_type<>'rejected' AND o.record_status<>'rejected') "
                        "ORDER BY a.id").fetchall()
    for index, row in enumerate(rows, 1):
        url = row["source_url"]
        key = url.rsplit("/", 1)[-1]
        body_path = output / (key + ".html")
        receipt_path = output / (key + ".json")
        try:
            links = conn.execute("SELECT object_id FROM appearance_object_links "
                                 "WHERE appearance_id=? AND relation_type<>'rejected'",
                                 (row["id"],)).fetchall()
            if len(links) != 1:
                raise ValueError("Appearance has ambiguous object membership; needs review")
            if body_path.exists() and receipt_path.exists():
                body = body_path.read_bytes()
                receipt = json.loads(receipt_path.read_text())
                if receipt["sha256"] != sha(body) or receipt["url"] != url:
                    raise ValueError("Saved evidence does not match receipt")
            else:
                target = url
                for _ in range(6):
                    policy(target)
                    try:
                        with _open(target) as response:
                            body = response.read()
                            receipt = dict(url=url, final_url=target, status_code=response.status,
                                           sha256=sha(body), retrieved_at=now(),
                                           headers=dict(response.headers.items()))
                        break
                    except urllib.error.HTTPError as exc:
                        location = exc.headers.get("Location") if 300 <= exc.code < 400 else None
                        if not location:
                            raise
                        target = urljoin(target, location)
                else:
                    raise ValueError("Too many redirects")
                body_path.write_bytes(body)
                receipt_path.write_text(json.dumps(receipt, indent=2))
            fields = penn_fields(body.decode("utf-8", "replace"))
            designation = fields.get("Object Number", [])
            expected = [r[0] for r in conn.execute(
                "SELECT i.value FROM identifiers i JOIN appearance_object_links l "
                "ON l.object_id=i.object_id WHERE l.appearance_id=? AND i.source_id=? "
                "AND i.scheme='collection designation'", (row["id"], row["source_id"]))]
            if not designation or not any(d.strip().casefold() == e.strip().casefold()
                                          for d in designation for e in expected):
                raise ValueError("Object number does not match retained appearance")
            description = " ".join(fields.get("Description", []))
            claims = penn_metadata_claims(fields, description, url)
            def comparable(field, value):
                if field == "material":
                    value = value.translate(str.maketrans({"|": " ", ";": " ", ",": " "}))
                return field, " ".join(value.split()).casefold()

            existing = {comparable(r[0], r[1]) for r in conn.execute(
                "SELECT field,value_text FROM claims WHERE appearance_id=? AND value_text IS NOT NULL",
                (row["id"],))}
            claims = [c for c in claims if comparable(c["field"], c["value_text"]) not in existing]
            for claim in claims:
                claim["notes"] = (claim.get("notes", "") + " Source HTML SHA-256 " + sha(body)
                                  + "; retrieved " + receipt["retrieved_at"] + ". Original description retained.")
            if claims:
                records.append(dict(source_id=row["source_id"],
                                    appearance=dict(locator=row["locator"]), claims=claims))
            inventory.append(dict(appearance_id=row["id"], source_id=row["source_id"],
                                  web_id=key, sha256=sha(body), added_fields=[c["field"] for c in claims]))
        except Exception as exc:
            failures.append(dict(appearance_id=row["id"], url=url, error=str(exc)))
        if index % 25 == 0:
            print(json.dumps(dict(processed=index, total=len(rows), failures=len(failures))), flush=True)
        time.sleep(delay)
    manifest = output / "candidates.jsonl"
    manifest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    result = dict(prepared_at=now(), eligible_appearances=len(rows), fetched=len(inventory),
                  records=len(records), claims=sum(len(r["claims"]) for r in records),
                  manifest_sha256=sha(manifest.read_bytes()), inventory=inventory, failures=failures)
    (output / "inventory.json").write_text(json.dumps(result, indent=2))
    return {k: v for k, v in result.items() if k not in ("inventory", "failures")} | {"failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()
    # SQLite query-only also protects against incidental writes in a helper.
    conn = connect()
    conn.execute("PRAGMA query_only=ON")
    try:
        print(json.dumps(prepare(conn, args.output, args.delay), indent=2))
    finally:
        conn.close()
