#!/usr/bin/env python3
"""Build the undeployed Bowlam public educational library release candidate.

The library is a deliberately small derivative of the shared public projection:
only rows with released text content or approved media are grouped into browse
cards. It is written outside ``site/public`` until its exact bytes receive a
separate deployment approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bowl_index.projection import Projection
from bowl_index.state import corpus_fingerprint


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "private" / "ibi.sqlite3"
OUT = ROOT / "site" / "library-build"
SITE_FONTS = ROOT / "site" / "public" / "fonts"
DEFAULT_REVIEW = ROOT / "research" / "reviews" / "public_library_release_candidate_2026-09-20.json"
EXCLUDED_TEXT = "TXT-D39E05041A00"
FORBIDDEN_KEYS = {
    "capture_id", "storage_path", "quotation", "notes", "value_text", "value_json",
    "normalized_value", "public_ok", "private_capture_status", "creator", "rights_holder",
    "reviewed_by", "reviewed_at", "rationale", "followup",
}
BAD_PATTERNS = (
    re.compile(r"/Users/"), re.compile(r"data/private/"), re.compile(r"file://", re.I),
    re.compile(r"\blocalhost\b|127\.0\.0\.1", re.I),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity_map(clusters: list[dict]) -> tuple[dict[str, str], dict[str, dict]]:
    members, by_id = {}, {}
    for cluster in clusters:
        by_id[cluster["identity_id"]] = cluster
        for object_id in json.loads(cluster["member_ids"]):
            members[object_id] = cluster["identity_id"]
    return members, by_id


def library_payload(tables: dict[str, list[dict]]) -> dict:
    texts = [row for row in tables["texts"] if row["content_status"] == "included"]
    media = tables["media"]
    relevant = {row["object_id"] for row in texts + media}
    member_to_identity, clusters = identity_map(tables["identity_clusters"])
    object_rows = {row["id"]: row for row in tables["objects"]}
    identifiers = defaultdict(list)
    for row in tables["identifiers"]:
        if row["object_id"] in relevant:
            identifiers[row["object_id"]].append({
                "scheme": row["scheme"], "value": row["value"],
                "assigning_body": row["assigning_body"],
            })

    groups = {}
    for object_id in sorted(relevant):
        identity_id = member_to_identity.get(object_id, object_id)
        cluster = clusters.get(identity_id)
        obj = object_rows[object_id]
        group = groups.setdefault(identity_id, {
            "id": identity_id,
            "title": (cluster or {}).get("display_name") or obj["label"],
            "date": (cluster or {}).get("display_date"),
            "language": (cluster or {}).get("display_language"),
            "collection": (cluster or {}).get("display_collection"),
            "record_status": (cluster or {}).get("record_status") or obj["record_status"],
            "object_ids": [], "identifiers": [], "texts": [], "media": [],
        })
        group["object_ids"].append(object_id)
        group["identifiers"].extend(identifiers[object_id])

    for row in texts:
        target = groups[member_to_identity.get(row["object_id"], row["object_id"])]
        target["texts"].append({key: row[key] for key in (
            "id", "object_id", "text_type", "language", "script", "editor", "locator",
            "content", "rights_basis", "license_url", "attribution", "rights_locator",
            "editorial_status", "access_citation", "access_url", "access_status",
        )})
    for row in media:
        target = groups[member_to_identity.get(row["object_id"], row["object_id"])]
        target["media"].append({key: row[key] for key in (
            "id", "object_id", "media_type", "url", "attribution", "rights_status",
            "rights_statement", "rights_locator", "license_url",
        )})

    items = sorted(groups.values(), key=lambda row: (row["title"] or "", row["id"]))
    for item in items:
        item["object_ids"].sort()
        item["identifiers"] = sorted(
            {json.dumps(value, sort_keys=True): value for value in item["identifiers"]}.values(),
            key=lambda value: (value["scheme"], value["value"]),
        )
        item["texts"].sort(key=lambda row: (row["text_type"], row["locator"] or "", row["id"]))
        item["media"].sort(key=lambda row: (row["attribution"], row["id"]))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "Public educational library of rights-reviewed incantation-bowl resources",
        "noncommercial_notice": (
            "Some rows carry CC BY-NC or institution-specific educational-use terms. "
            "Terms shown with each item govern those materials."
        ),
        "counts": {"items": len(items), "texts": len(texts), "media": len(media)},
        "items": items,
    }


def audit_candidate(projection: Projection, payload: dict) -> list[dict]:
    checks = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    texts = [row for item in payload["items"] for row in item["texts"]]
    media = [row for item in payload["items"] for row in item["media"]]
    keys = {key for item in payload["items"] for key in item}
    keys.update(key for row in texts + media for key in row)
    record("allowlisted_fields", not (keys & FORBIDDEN_KEYS),
           "no private, raw-evidence or reviewer-only fields")
    record("text_gate", len(texts) == len(projection.approved_texts) and all(
        row["content"] and row["rights_basis"] and row["attribution"]
        and row["rights_locator"] and row["editorial_status"] for row in texts
    ), "%d currently approved text rows" % len(texts))
    record("excluded_text_absent", EXCLUDED_TEXT not in {row["id"] for row in texts},
           "partially reviewed Wohlstein row remains withheld")
    record("media_gate", len(media) == len(projection.approved) and all(
        row["url"] and row["attribution"] and row["rights_statement"]
        and row["rights_locator"] for row in media
    ), "%d currently approved media rows" % len(media))

    by_url = defaultdict(set)
    for row in media:
        by_url[row["url"]].add((row["rights_statement"], row["rights_locator"], row["license_url"]))
    record("shared_media_terms_coherent", all(len(terms) == 1 for terms in by_url.values()),
           "%d distinct media URLs have coherent terms" % len(by_url))

    penn = [row for row in media if "penn.museum//collections/assets/" in row["url"]]
    record("penn_credit", len(penn) == 288 and all(
        row["attribution"].startswith("Object ")
        and row["attribution"].endswith("Courtesy of the Penn Museum.")
        and "penn.museum" in row["rights_locator"] for row in penn
    ), "%d Penn rows carry object credit and policy locator" % len(penn))

    staged = json.dumps(payload, ensure_ascii=False)
    record("local_paths_contacts_and_secrets_absent",
           not any(pattern.search(staged) for pattern in BAD_PATTERNS),
           "no local path, private-directory, localhost, email-address or secret pattern")
    record("private_capture_paths_absent",
           not any(path and path in staged for path in projection.private_storage),
           "%d private storage paths tested" % len(projection.private_storage))
    record("counts_match", payload["counts"] == {
        "items": len(payload["items"]), "texts": len(texts), "media": len(media)},
        "declared library counts match emitted rows")
    record("source_pointers", all(row["access_citation"] and row["locator"] for row in texts),
           "every text carries a source citation and locator")
    return checks


def release_candidate(projection: Projection, payload: dict, checks: list[dict]) -> dict:
    if not all(check["passed"] for check in checks):
        raise ValueError("release audit failed: " + ", ".join(
            check["name"] for check in checks if not check["passed"]
        ))
    files = [
        {"path": str(path.relative_to(OUT)), "sha256": digest(path), "bytes": path.stat().st_size}
        for path in sorted(OUT.rglob("*")) if path.is_file()
    ]
    material = "\n".join(item["path"] + ":" + item["sha256"] for item in files)
    texts = [row for item in payload["items"] for row in item["texts"]]
    media = [row for item in payload["items"] for row in item["media"]]
    text_buckets = Counter((row["rights_basis"], row["license_url"] or "") for row in texts)
    media_buckets = Counter(row["rights_status"] for row in media)
    return {
        "schema_version": 1,
        "artifact": "Bowlam public educational library",
        "candidate_id": hashlib.sha256(material.encode()).hexdigest(),
        "built_at": payload["generated_at"],
        "corpus_state_digest": corpus_fingerprint(projection.conn)["corpus_digest"],
        "approval": {"status": "pending_owner_approval", "approved_by": None,
                     "approved_at": None, "note": None},
        "counts": payload["counts"],
        "licensing": {
            "project_contribution": "CC BY 4.0",
            "texts": [
                {"rights_basis": basis, "license_url": url or None, "rows": count}
                for (basis, url), count in sorted(text_buckets.items())
            ],
            "media": [
                {"recorded_rights_status": status, "rows": count}
                for status, count in sorted(media_buckets.items())
            ],
            "scope_notice": payload["noncommercial_notice"],
        },
        "audit_checks": checks,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--review-manifest", default=str(DEFAULT_REVIEW))
    args = parser.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % args.db, uri=True)
    conn.row_factory = sqlite3.Row
    projection = Projection(conn)
    payload = library_payload(projection.tables())

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    (OUT / "data" / "library.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (OUT / "index.html").write_text(INDEX, encoding="utf-8")
    (OUT / "library.css").write_text(CSS, encoding="utf-8")
    (OUT / "library.js").write_text(JS, encoding="utf-8")
    shutil.copytree(SITE_FONTS, OUT / "fonts")

    checks = audit_candidate(projection, payload)
    candidate = release_candidate(projection, payload, checks)
    candidate_text = json.dumps(candidate, ensure_ascii=False, indent=2) + "\n"
    (OUT / "release-candidate.json").write_text(candidate_text, encoding="utf-8")
    review = Path(args.review_manifest)
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(candidate_text, encoding="utf-8")
    print(json.dumps({
        **payload["counts"], "candidate_id": candidate["candidate_id"],
        "audit_checks": "%d/%d" % (sum(c["passed"] for c in checks), len(checks)),
        "deployed": False,
    }, indent=2))


INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Rights-reviewed translations, texts and images of Aramaic incantation bowls.">
<title>Bowlam Library</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='14' fill='%2317130f' stroke='%23d9954f' stroke-width='2'/%3E%3Cpath d='M7 13c3 9 15 9 18 0M10 12c2 5 10 5 12 0' fill='none' stroke='%23ece3d4' stroke-width='1.5'/%3E%3C/svg%3E">
<link rel="stylesheet" href="library.css">
</head>
<body>
<a class="skip" href="#results">Skip to results</a>
<header class="topbar">
  <a class="brand" href="/"><span aria-hidden="true">𐡀</span><strong>Bowlam</strong></a>
  <nav aria-label="Site"><a href="/">About the index</a><span>Library</span></nav>
</header>
<main>
  <section class="workbench" aria-labelledby="library-title">
    <div class="intro">
      <p class="eyebrow">Rights-reviewed collection</p>
      <h1 id="library-title">The bowl library</h1>
      <p>Read available texts and examine collection images. Each item carries its source and reuse terms; material without a recorded basis stays out.</p>
    </div>
    <form class="controls" role="search" onsubmit="return false">
      <label for="query">Search bowls, collections, editors and text</label>
      <input id="query" type="search" placeholder="Try Nippur, Montgomery, B16091…" autocomplete="off">
      <fieldset>
        <legend>Show</legend>
        <button type="button" data-filter="all" aria-pressed="true">Everything</button>
        <button type="button" data-filter="images" aria-pressed="false">Images</button>
        <button type="button" data-filter="translations" aria-pressed="false">Translations</button>
        <button type="button" data-filter="texts" aria-pressed="false">All texts</button>
      </fieldset>
    </form>
    <div class="summary" id="summary" role="status" aria-live="polite">Loading the library…</div>
  </section>
  <section id="results" class="results" aria-label="Library results"></section>
  <div class="more-wrap"><button id="more" class="more" type="button" hidden>Show more</button></div>
</main>
<footer>
  <p>Bowlam’s database contribution is CC BY 4.0. Public-domain works, CC BY-NC texts and institution-specific images retain their own terms.</p>
  <p><a href="release-candidate.json">Release inventory and privacy checks</a></p>
</footer>
<template id="empty"><div class="empty"><h2>No matching bowls</h2><p>Try a broader word or another material filter.</p></div></template>
<script src="library.js" defer></script>
</body>
</html>
"""


CSS = r"""@font-face{font-family:Frank;src:url('fonts/frank-ruhl-libre-latin.woff2') format('woff2');font-display:swap;font-weight:300 900}
:root{color-scheme:dark;--paper:#17130f;--raised:#211b16;--ink:#eee5d8;--muted:#b5aa9c;--line:#493b30;--clay:#dc9a55;--blue:#8bbac0;--serif:Frank,Georgia,serif;--sans:"Avenir Next",Avenir,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:1rem/1.55 var(--sans)}a{color:inherit}button,input{font:inherit}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;z-index:9;background:var(--clay);color:#17130f;padding:.7rem 1rem}.topbar{height:68px;padding:0 clamp(1rem,4vw,4rem);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);background:#100d0af2;position:sticky;top:0;z-index:5;backdrop-filter:blur(12px)}.brand{display:flex;align-items:center;gap:.65rem;text-decoration:none;font-family:var(--serif);font-size:1.15rem}.brand span{display:grid;place-items:center;width:32px;height:32px;border:1px solid #745e4b;border-radius:50%;color:var(--clay)}nav{display:flex;gap:1.2rem;color:var(--muted);font-size:.9rem}nav a{text-decoration:none}nav span{color:var(--ink)}main{min-height:70vh}.workbench{padding:clamp(2.5rem,6vw,5rem) clamp(1rem,5vw,5rem) 2rem;border-bottom:1px solid var(--line);background:radial-gradient(circle at 82% 0,#3a291a 0,transparent 33%)}.intro{max-width:780px}.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;color:var(--clay);font-weight:700}.intro h1{font:400 clamp(2.8rem,7vw,5.5rem)/.96 var(--serif);letter-spacing:-.04em;margin:.4rem 0 1rem}.intro>p:last-child{max-width:650px;color:var(--muted);font-size:1.05rem}.controls{display:grid;grid-template-columns:minmax(250px,1fr) auto;gap:.7rem 1.25rem;align-items:end;margin-top:2.25rem;max-width:1080px}.controls>label{grid-column:1/-1;font-size:.82rem;font-weight:700}.controls input{min-height:50px;padding:.75rem 1rem;background:#0f0d0b;border:1px solid #665140;color:var(--ink);border-radius:4px;font-size:1rem}.controls fieldset{display:flex;gap:.45rem;border:0;padding:0;margin:0}.controls legend{position:absolute;left:-9999px}.controls button,.more{min-height:46px;padding:.65rem .95rem;border:1px solid var(--line);border-radius:999px;background:var(--raised);color:var(--muted);cursor:pointer}.controls button[aria-pressed=true]{background:var(--clay);border-color:var(--clay);color:#17130f}.summary{margin-top:1rem;color:var(--muted);font-size:.9rem}.results{padding:clamp(1rem,4vw,4rem);display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,360px),1fr));gap:1rem;align-items:start}.card{border:1px solid var(--line);background:var(--raised);border-radius:7px;overflow:hidden}.card-head{padding:1.15rem 1.2rem;border-bottom:1px solid var(--line)}.card h2{font:500 1.42rem/1.15 var(--serif);margin:0}.meta{margin:.45rem 0 0;color:var(--muted);font-size:.8rem}.image{margin:0;border-bottom:1px solid var(--line);background:#0c0a08}.image img{display:block;width:100%;height:270px;object-fit:contain}.image figcaption{padding:.7rem 1rem;color:var(--muted);font-size:.75rem}.image a{color:var(--blue)}.resource{padding:1rem 1.2rem;border-bottom:1px solid var(--line)}.resource:last-child{border-bottom:0}.resource h3{margin:0 0 .65rem;font:600 1rem var(--serif)}.text{white-space:pre-wrap;overflow-wrap:anywhere;font-family:var(--serif);font-size:1.04rem;line-height:1.65}.terms{margin:.8rem 0 0;padding-top:.7rem;border-top:1px dotted #5b4b3f;color:var(--muted);font-size:.75rem}.terms a{color:var(--blue)}.badge{display:inline-block;margin-right:.4rem;color:var(--clay);font-family:var(--sans);font-size:.7rem;letter-spacing:.08em;text-transform:uppercase}.empty{grid-column:1/-1;padding:4rem 1rem;text-align:center;color:var(--muted)}.empty h2{color:var(--ink);font:2rem var(--serif);margin:0}.more-wrap{text-align:center;padding:0 1rem 3rem}.more{color:var(--ink)}footer{padding:2rem clamp(1rem,5vw,5rem) 4rem;border-top:1px solid var(--line);color:var(--muted);font-size:.82rem}footer p{max-width:760px}@media(max-width:720px){.topbar nav a{display:none}.controls{grid-template-columns:1fr}.controls fieldset{overflow-x:auto;padding-bottom:.25rem}.controls button{white-space:nowrap}.image img{height:230px}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}"""


JS = r"""(function(){"use strict";var data=[],filtered=[],shown=0,filter="all",step=36;
var results=document.getElementById("results"),summary=document.getElementById("summary"),query=document.getElementById("query"),more=document.getElementById("more");
function esc(v){return String(v==null?"":v).replace(/[&<>\"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function firstUrl(v){var m=String(v||"").match(/^https?:\/\/[^;\s]+/);return m?m[0]:null}
function terms(r,kind){var link=r.license_url||(kind==="media"?firstUrl(r.rights_locator):r.access_url);var label=r.license_url?"Licence":kind==="media"?"Use terms":"Source";var note=kind==="media"?r.rights_statement:(r.attribution||r.access_citation);return '<p class="terms">'+esc(note||"")+(link?' · <a href="'+esc(link)+'" rel="external noreferrer">'+label+'</a>':"")+(r.locator?' · '+esc(r.locator):"")+'</p>'}
function card(item){var ids=item.identifiers.slice(0,3).map(function(x){return x.value}).join(" · ");var meta=[item.collection,item.language,item.date,ids].filter(Boolean).join(" · ");var media=item.media.map(function(r){return '<figure class="image"><a href="'+esc(r.url)+'" rel="external noreferrer"><img src="'+esc(r.url)+'" alt="'+esc(item.title+" — "+r.attribution)+'" loading="lazy" decoding="async"></a><figcaption>'+esc(r.attribution)+terms(r,"media")+'</figcaption></figure>'}).join("");var texts=item.texts.map(function(r){return '<article class="resource"><h3><span class="badge">'+esc(r.text_type)+'</span>'+esc(r.editor||"Text")+'</h3><div class="text" dir="auto">'+esc(r.content)+'</div>'+terms(r,"text")+'</article>'}).join("");return '<article class="card"><header class="card-head"><h2>'+esc(item.title)+'</h2><p class="meta">'+esc(meta||"Catalogue record")+'</p></header>'+media+texts+'</article>'}
function matches(i,q){var has=filter==="all"||(filter==="images"&&i.media.length)||(filter==="texts"&&i.texts.length)||(filter==="translations"&&i.texts.some(function(t){return t.text_type==="translation"}));if(!has)return false;if(!q)return true;return JSON.stringify(i).toLocaleLowerCase().indexOf(q)>=0}
function render(reset){if(reset){shown=step;results.innerHTML=""}else shown+=step;var q=query.value.trim().toLocaleLowerCase();filtered=data.filter(function(i){return matches(i,q)});if(!filtered.length){results.innerHTML=document.getElementById("empty").innerHTML;more.hidden=true}else{results.innerHTML=filtered.slice(0,shown).map(card).join("");more.hidden=shown>=filtered.length}var t=filtered.reduce(function(n,i){return n+i.texts.length},0),m=filtered.reduce(function(n,i){return n+i.media.length},0);summary.textContent=filtered.length.toLocaleString()+" bowls · "+t.toLocaleString()+" texts · "+m.toLocaleString()+" images"}
document.querySelectorAll("[data-filter]").forEach(function(b){b.onclick=function(){filter=b.dataset.filter;document.querySelectorAll("[data-filter]").forEach(function(x){x.setAttribute("aria-pressed",String(x===b))});render(true)}});query.addEventListener("input",function(){render(true)});more.onclick=function(){render(false)};
fetch("data/library.json").then(function(r){if(!r.ok)throw Error(r.status);return r.json()}).then(function(p){data=p.items;render(true)}).catch(function(){summary.textContent="The library could not be loaded.";results.innerHTML='<div class="empty"><h2>Library unavailable</h2><p>Please try again later.</p></div>'});})();"""


if __name__ == "__main__":
    main()
