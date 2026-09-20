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

# These labels belong to this project. They are deliberately kept separate from
# the source-attributed wording in ``claims``: the visitor gets a stable browse
# vocabulary while the object page can still show exactly what each source said.
_COLLECTION_PATTERNS = (
    (r"penn museum|university of pennsylvania", "Penn Museum"),
    (r"british museum", "British Museum, London"),
    (r"vorderasiatisches museum", "Vorderasiatisches Museum, Berlin"),
    (r"sch.yen collection", "Schøyen Collection"),
    (r"hilprecht collection", "Hilprecht Collection, Jena"),
    (r"moussaieff collection", "Moussaieff Collection"),
    (r"national library of israel", "National Library of Israel, Jerusalem"),
    (r"iraq museum", "Iraq Museum, Baghdad"),
    (r"israel museum", "Israel Museum, Jerusalem"),
    (r"kelsey museum", "Kelsey Museum of Archaeology, Ann Arbor"),
    (r"metropolitan museum", "Metropolitan Museum of Art, New York"),
    (r"institute for the study of ancient cultures|isac museum", "ISAC Museum, Chicago"),
    (r"museo sefard", "Museo Sefardí, Toledo"),
    (r"mus.e du louvre", "Musée du Louvre, Paris"),
    (r"state hermitage", "State Hermitage Museum, St. Petersburg"),
    (r".bg.ne museum", "Ābgīne Museum, Tehran"),
    (r"loyola marymount", "Loyola Marymount University Archaeology Museum"),
    (r"yale babylonian", "Yale Babylonian Collection"),
    (r"royal ontario", "Royal Ontario Museum, Toronto"),
    (r"smithsonian", "Smithsonian National Museum of Natural History"),
    (r"jewish historical museum", "Jewish Historical Museum, Belgrade"),
    (r"mus.e champollion", "Musée Champollion"),
    (r"cincinnati skirball", "Cincinnati Skirball Museum"),
    (r"allard pierson", "Allard Pierson Museum, Amsterdam"),
    (r"johns hopkins", "Johns Hopkins Archaeological Museum"),
    (r"hebrew university institute", "Hebrew University Institute of Archaeology"),
    (r"davidovitz collection", "Davidovitz Collection"),
    (r"di castro collection", "Di Castro Collection, Rome"),
    (r"magnes collection", "Magnes Collection"),
    (r"barakat gallery|barakat collection", "Barakat Collection"),
    (r"erbil civilization", "Erbil Civilization Museum"),
    (r"jewish museum of switzerland", "Jewish Museum of Switzerland, Basel"),
    (r"matenadaran", "Matenadaran, Yerevan"),
    (r"bodmer", "Fondation Martin Bodmer, Geneva"),
    (r"museo delle civilt", "Museo delle Civiltà, Rome"),
    (r"miami university", "Miami University Art Museum"),
    (r"hetjens", "Hetjens-Museum, Düsseldorf"),
    (r"museu da farm.cia", "Museu da Farmácia, Lisbon"),
    (r"museum f.r vor", "Museum für Vor- und Frühgeschichte, Berlin"),
    (r"menil collection", "The Menil Collection, Houston"),
    (r"national museum of finland", "National Museum of Finland, Helsinki"),
    (r"bible lands museum", "Bible Lands Museum Jerusalem"),
    (r"wolf collection", "Wolf Collection"),
    (r"klagsbald collection", "Klagsbald Collection"),
    (r"akram sawalha", "Akram Sawalha Collection"),
    (r"small collection at st albans", "Private collection, St Albans"),
    (r"private collection", "Private collection"),
)

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

    # A descriptive nickname is not a catalogue title. Where the label carries no
    # number at all but the collection has given the bowl one, and that
    # designation is built on a name the label already uses, prefer the
    # designation: "Davidovitz popularity-and-success bowl" is how an editor
    # referred to it in prose, "Davidovitz 41" is what the collection calls it.
    # Both conditions are load-bearing. Preferring a designation generally
    # rewrites 614 names and makes many worse ("Penn B2958: Hebrew Bowl" would
    # become "B2958"); requiring a digit-free label alone still catches
    # "De Menil", whose designation "X 831" says less than the label does.
    designation = (ids.get("collection designation") or [None])[0]
    if cleaned and designation and not re.search(r"\d", cleaned):
        stem = re.sub(r"[\d\s]+$", "", designation).strip()
        if stem and re.search(r"\d", designation) and stem.casefold() in cleaned.casefold():
            return designation

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
        labels = collection_facet(location)
        if labels:
            return labels[0]
    return next((str(value).strip() for value in locations if str(value).strip()), "Collection not recorded")


def collection_facet(value):
    """Normalize a recorded repository for browsing, without changing the claim."""
    raw = str(value or "").strip()
    folded = raw.casefold()
    if not raw:
        return []
    if any(token in folded for token in (
        "unknown", "unlocated", "not exposed in accessible bibliographic metadata"
    )):
        return ["Location unknown / unlocated"]
    for pattern, label in _COLLECTION_PATTERNS:
        if re.search(pattern, folded):
            return [label]
    # An unmatched institution is already a concise factual name. Remove only
    # common report-date tails; do not guess at an institution or city.
    cleaned = re.sub(r",?\s+(?:in|as reported in)\s+\d{4}$", "", raw, flags=re.I)
    return [cleaned]


def language_facets(value):
    """Return broad, project-authored language categories for one source claim."""
    raw = re.sub(r"[\x00-\x1f\u200b]", "", str(value or "")).strip()
    folded = raw.casefold()
    if not raw:
        return []
    pseudo = "pseudo" in folded or "meaningless" in folded or "aramaic-like" in folded
    if "meaningless" in folded or ("probably" in folded and "pseudo" in folded):
        return ["Pseudo-script / non-lexical"]
    labels = ["Pseudo-script / non-lexical"] if pseudo else []
    if re.search(r"jewish babylonian|talmudic aramaic|judeo-aramaic|jewish aramaic|\bjba\b", folded):
        labels.append("Jewish Babylonian Aramaic")
    elif "aramaic" in folded or "aramean" in folded or folded == "arc":
        labels.append("Aramaic (unspecified)")
    if "syriac" in folded or folded == "syc":
        labels.append("Syriac")
    if "mandaic" in folded or folded == "myz":
        labels.append("Mandaic")
    if "hebrew" in folded or folded == "heb":
        labels.append("Hebrew")
    if "middle persian" in folded or "pahlavi" in folded or "persian language" in folded:
        labels.append("Middle Persian / Pahlavi")
    if "arabic" in folded:
        labels.append("Arabic")
    # Catalogue code lists are intentionally allowed to yield several labels.
    if not labels and ";" in folded:
        for code in (part.strip() for part in folded.split(";")):
            label = _LANGUAGE_CODES.get(code)
            if label and label not in labels:
                labels.append(label if label != "Aramaic" else "Aramaic (unspecified)")
    if labels:
        return labels
    if folded in {"?", "n/a", "n/a.", "n/​a."} or "not adjudicated" in folded:
        return ["Classification unresolved"]
    return [raw.rstrip(".")]


_ORIGIN_PATTERNS = (
    (r"\bnippur\b", "Nippur"),
    (r"khouabir", "Khouabir"),
    (r"tell ibrahim|\bkutha\b", "Kutha (Tell Ibrahim)"),
    (r"ibrahim al-khalil|birs-nimrud|\bborsippa\b", "Borsippa"),
    (r"\bbabylon\b|\bamran\b", "Babylon"),
    (r"khorsabad", "Khorsabad"),
    (r"seleucia", "Seleucia on the Tigris"),
    (r"susiana|\bsusa\b", "Susa / Susiana"),
    (r"abu habba|\bsippar\b", "Sippar (Abu Habba)"),
    (r"\bnimrud\b", "Nimrud"),
    (r"kouyunjik", "Nineveh (Kouyunjik)"),
    (r"\bwarka\b", "Uruk (Warka)"),
    (r"\bashur\b", "Ashur"),
    (r"tell baruda|\bchoche\b", "Tell Baruda (Choche)"),
    (r"tell khafaje", "Tell Khafaje"),
    (r"tell al-duwayhi", "Tell al-Duwayhi"),
    (r"kermanshah", "Kermanshah"),
    (r"\barban\b", "Arban"),
    (r"kiamiaz", "Kiamiaz"),
    (r"velyki kuchugury", "Velyki Kuchugury"),
    (r"karbal", "Karbala"),
    (r"\bbaghdad\b", "Baghdad"),
    (r"\bhillah\b|al-hillah", "Hillah / Babylon region"),
)


def origin_facets(field, value):
    """Normalize geography only; ownership narratives are not origins."""
    if field not in {
        "findspot", "findspot_or_origin", "origin", "production_place", "geography",
        "geographic_association", "excavation_context",
    }:
        return []
    folded = str(value or "").casefold()
    labels = [label for pattern, label in _ORIGIN_PATTERNS if re.search(pattern, folded)]
    # Prefer named sites to broad regions, but preserve a genuinely composite
    # site claim such as “Babylon | Borsippa”.
    if labels:
        return list(dict.fromkeys(labels))
    if "southern iraq" in folded or "iraq, south" in folded:
        return ["Southern Iraq"]
    if "iraq" in folded:
        return ["Iraq (unspecified)"]
    if "mesopotamia" in folded:
        return ["Mesopotamia (unspecified)"]
    if "iran" in folded or "persia" in folded:
        return ["Iran / Persia"]
    if "syria" in folded:
        return ["Syria"]
    if "near east" in folded:
        return ["Near East (unspecified)"]
    return []


def purpose_facets(field, value):
    """Classify ritual function; names and installation notes are not purposes."""
    if field not in {"text_purpose", "text_function", "formula_genre", "text_tradition"}:
        return []
    folded = str(value or "").casefold()
    labels = []
    rules = (
        (r"heal|illness|fever|health|ill health", "Healing"),
        (r"pregnan|childbirth|delivery|fertil|unborn|womb|abortion|barren", "Childbirth & fertility"),
        (r"love|enamour|desire", "Love & attraction"),
        (r"prosper|business|popularity|economic success|social influence|favor|favour|grace", "Favor & prosperity"),
        (r"aggressive|curse magic|hate magic|adversarial|subjugat|discord|hostile mouths", "Aggressive / curse magic"),
        (r"divorce|ban-writ|writ of dismissal", "Divorce / dismissal"),
        (r"expuls|banish|driving out|drive out|exorcis", "Exorcism / expulsion"),
        (r"bind|seal|pressing down|counter-spell|charming", "Binding & sealing"),
        (r"historiola", "Historiola"),
        (r"protect|guard|safety|salvation|repulsion|amulet against|suppress|armament", "Protection"),
    )
    for pattern, label in rules:
        if re.search(pattern, folded):
            labels.append(label)
    if labels:
        return list(dict.fromkeys(labels))
    if field == "formula_genre" and "general charm" in folded:
        return ["General charm"]
    # “Mesopotamian” and “Talmudic” are traditions, not functions. Keep them in
    # raw facts but do not force them into the visitor's “What they do” facet.
    return []


def public_facets(field, field_group, value):
    """Route one source claim into zero or more controlled browse labels."""
    if field_group == "location":
        return collection_facet(value)
    if field_group == "language":
        return language_facets(value)
    if field_group == "provenance":
        return origin_facets(field, value)
    if field_group == "ritual":
        return purpose_facets(field, value)
    return []


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
