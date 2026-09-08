"""Visitor-facing names and concise fact labels for bowls.

These functions change presentation only. Original labels, identifiers and
source-attributed claim values remain untouched and available in the research
record.
"""

import re


_LABEL_NOISE = re.compile(
    r"(?:\s*[-\u2014]\s*)?\b(?:COJS\s+)?(?:exhibition|translation|catalogue|listing|index)"
    r"\s+(?:appearance|entry)\s*$",
    re.I,
)
_LABEL_PREFIX = re.compile(
    r"^(?:Waller\s*2022|Apotropaic\s+index|Context\s+citation)\s*[::]\s*", re.I
)

_COLLECTION_ALIASES = {
    "penn museum": "Penn Museum",
    "the british museum": "British Museum, London",
    "british museum": "British Museum, London",
    "museo delle civiltà": "Museo delle Civiltà, Rome",
}

_LANGUAGE_CODES = {
    "arc": "Aramaic", "heb": "Hebrew", "myz": "Mandaic", "syc": "Syriac",
}


def _identifier_map(identifiers):
    result = {}
    for item in identifiers:
        if isinstance(item, dict):
            scheme, value = item.get("scheme", ""), item.get("value", "")
        else:
            scheme, _, value = str(item).partition(":")
        if str(value).strip():
            result.setdefault(str(scheme).strip().casefold(), []).append(str(value).strip())
    return result


def clean_label(label):
    cleaned = _LABEL_PREFIX.sub("", label or "").strip()
    return _LABEL_NOISE.sub("", cleaned).strip(" -\u2014\u00b7")


def display_name(label, identifiers=()):
    """Return a recognizable catalogue title without inventing an accession."""
    cleaned = clean_label(label)
    ids = _identifier_map(identifiers)

    penn = (ids.get("penn catalogue number") or [None])[0]
    if penn:
        return f"Penn Museum · {penn}"

    isiao = next((value for values in ids.values() for value in values
                  if re.fullmatch(r"IsIAO\s*\S+", value, re.I)), None)
    if isiao and "museo delle civilt" in cleaned.casefold():
        return f"Museo delle Civiltà, Rome · {isiao}"

    british = (ids.get("british museum museum number") or [None])[0]
    if british:
        return f"British Museum, London · {british}"

    publication_key = (ids.get("publication object key") or [None])[0]
    if publication_key and "::" in publication_key:
        publication, number = (part.strip() for part in publication_key.split("::", 1))
        if publication and number:
            return f"{publication} · Bowl {number}"

    if cleaned and not cleaned.casefold().startswith(("untitled", "unknown")):
        return cleaned

    for key in ("accession number", "museum number", "collection designation",
                "publication register identifier", "field number",
                "montgomery 1913 text number", "publication designation"):
        value = (ids.get(key) or [None])[0]
        if value:
            return f"Bowl {value}"
    return "Bowl"


def collection_name(label, identifiers=(), locations=()):
    """A concise collection label, using only recorded collection evidence."""
    title = display_name(label, identifiers)
    if " · " in title:
        prefix = title.split(" · ", 1)[0]
        if prefix not in {"Museum"} and not re.search(r"\b\d{4}$", prefix):
            return prefix
    for location in locations:
        key = str(location).strip().casefold()
        if key in _COLLECTION_ALIASES:
            return _COLLECTION_ALIASES[key]
    return next((str(value).strip() for value in locations if str(value).strip()), "Collection not recorded")


def language_name(claims):
    """Prefer an explicit inscription language to mixed catalogue code fields."""
    precedence = ("inscription_language", "script_or_language", "catalogue_language_codes")
    for field in precedence:
        values = []
        for claim in claims:
            if claim.get("field") != field:
                continue
            value = (claim.get("normalized_value") or claim.get("value_text") or
                     claim.get("value_json") or "").strip()
            if value and value not in values:
                values.append(value)
        if values:
            value = values[0]
            codes = [part.strip().casefold() for part in re.split(r"[;,]", value)]
            if codes and all(code in _LANGUAGE_CODES for code in codes):
                return " / ".join(_LANGUAGE_CODES[code] for code in codes)
            return value
    return "Language not recorded"


def format_date(value):
    """Normalize conventional typography without changing historical precision."""
    original = str(value or "").strip()
    if not original:
        return ""
    text = original.replace("-", "–")
    text = re.sub(r"^(?:circa|ca\.)\s+", "c. ", text, flags=re.I)
    text = re.sub(r"\b(\d+)(st|nd|rd|th)C\s*[–]\s*(\d+)(st|nd|rd|th)C\b",
                  lambda match: (f"{match.group(1)}{match.group(2).lower()}–"
                                 f"{match.group(3)}{match.group(4).lower()} centuries CE"),
                  text, flags=re.I)
    text = re.sub(r"\b(\d+)(st|nd|rd|th)–(\d+)(st|nd|rd|th) century CE\b",
                  r"\1\2–\3\4 centuries CE", text, flags=re.I)
    text = re.sub(r"\b(\d+)(st|nd|rd|th)–(\d+)(st|nd|rd|th) centuries CE\b",
                  r"\1\2–\3\4 centuries CE", text, flags=re.I)
    return text


def display_date(claims):
    """Display explicit dates only; periods and cultures remain separate facts."""
    values = []
    for claim in claims:
        if claim.get("field") != "dating":
            continue
        raw = claim.get("normalized_value") or claim.get("value_text") or claim.get("value_json")
        value = format_date(raw)
        if value and value.casefold() not in {item.casefold() for item in values}:
            values.append(value)
    if not values:
        return "Date not recorded"
    if len(values) == 1:
        return values[0]
    return "Multiple proposed dates"
