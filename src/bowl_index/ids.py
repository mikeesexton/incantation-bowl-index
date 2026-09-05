import uuid


PREFIXES = {
    "source": "SRC",
    "capture": "CAP",
    "search_run": "RUN",
    "search_query": "QRY",
    "coverage": "COV",
    "object": "IBI",
    "appearance": "APP",
    "identifier": "IDN",
    "claim": "CLM",
    "text": "TXT",
    "event": "EVT",
    "media": "MED",
    "lead": "LED",
    "dedupe": "DED",
    "dedupe_evidence": "DEV",
    "claim_conflict_review": "CFR",
    "merge": "MRG",
}


def new_id(kind):
    """Return a stable, opaque identifier suitable for citations and exports."""
    return "%s-%s" % (PREFIXES[kind], uuid.uuid4().hex[:12].upper())
