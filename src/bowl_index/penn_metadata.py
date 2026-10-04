"""Conservative, catalogue-attributed Penn fields; never infer language from titles."""

import re
from html.parser import HTMLParser


class _DetailTable(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = {}
        self.cells = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.cells = []
        elif tag == "td":
            self.cell = []
        elif tag in ("br", "p") and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, value):
        if self.cell is not None:
            self.cell.append(value)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.cells.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and len(self.cells) == 2:
            key, value = self.cells
            if key and value:
                self.rows.setdefault(key, []).append(value)


def penn_fields(page):
    parser = _DetailTable()
    parser.feed(page)
    return parser.rows


def penn_metadata_claims(fields, description, url):
    """Copy explicit table labels and bounded description clauses, with locators.

    No accession bridges, ancient dating, script classification, or excavated
    findspot inference. 'Hebrew Bowl' is an object title, not language evidence.
    """
    claims = []

    def add(field, value, section, **extra):
        if value:
            claims.append(dict(field=field, value_text=value.strip(), certainty="reported",
                               locator=url + " — " + section, **extra))

    for label, field in (("Inscription Language", "inscription_language"),
                         ("Provenience", "provenance"),
                         ("Materials", "material"), ("Iconography", "iconography")):
        for value in fields.get(label, []):
            add(field, value, label, notes="Penn catalogue label; retained without adjudication.")

    # Keep the catalogue's abbreviated completeness/fragment/line notation intact.
    # Split only explicitly labelled line counts, not arbitrary numbers or dates.
    description = " ".join((description or "").split())
    # A description may append historic register prose or a translated quotation.
    # Those remain in the original description, not in automated form/layout fields.
    description = re.split(r"\b(?:CBS\s+(?:Register|Catalogue)|Aramaic\s+Levy|Levy)\s*:",
                           description, maxsplit=1, flags=re.I)[0].strip()
    extent = re.match(r"^((?:Near\s+Complete|Almost\s+Complete|Incomplete|Complete|Fragmentary)\b[^;.]*)", description, re.I)
    if extent:
        value = extent[1]
        value = value.split("/", 1)[0].rstrip(" /;,")
        add("reported_physical_condition", value, "Description")
    for clause in re.split(r"[;.]+", description):
        if re.search(r"\b(?:internal|external)\b", clause, re.I):
            # Do not turn internal/external counts into a total line count.
            add("inscription_extent", clause.strip(), "Description")
        else:
            for line in re.finditer(r"(?<![\d–-])\b(\d+(?:\s*[–-]\s*\d+)?)\s+Lines?\b", clause, re.I):
                add("line_count", line[1] + " lines (catalogue report)", "Description")
    for clause in re.split(r"[;.]+", description):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:rounded|round|flat)\s+(?:bottom|base)\b", clause, re.I):
            add("reported_bowl_form", clause, "Description")
        if re.search(r"\b(?:wheel[ -]made|hand[ -]made)\b", clause, re.I):
            # Whole clause keeps 'probably', alternatives and other qualifications.
            add("reported_bowl_form", clause, "Description")
        if re.search(r"\btext\b.*\b(?:concentric|spiral|circles)\b", clause, re.I):
            add("text_layout", clause, "Description")
        if re.search(r"\b(?:figures?|demons?)\b", clause, re.I):
            add("iconography_or_caption", clause, "Description")
    return claims
