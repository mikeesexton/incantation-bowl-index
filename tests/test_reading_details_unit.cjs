const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("web/reading.js", "utf8");
const grouping = source.slice(source.indexOf("const tidy"), source.indexOf("function sourcesSection"));
const identifiers = source.slice(source.indexOf("function identifierRank"), source.indexOf("function renderObject"));
const context = vm.createContext({});
vm.runInContext(`
  const data = {factsBy: {}, textsBy: {}, editionsBy: {}, mediaBy: {}, sourceById: {SRC: {authors: "Scholar", issued_year: 2003}}};
  const factsOf = (id, group) => (data.factsBy[id] || []).filter(row => row.field_group === group);
  const esc = value => String(value ?? "");
  ${grouping}
  ${identifiers}
  ${source.slice(source.indexOf("function sourcesSection"), source.indexOf("function identifierRank"))}
  globalThis.T = {data, groupedFacts, citationsFor, groupedEditions, groupedIdentifiers, identifierDetails, identifiersSection, sourcesSection, journeySection, datingEvidence, factItems, bowlAppearance, recordedFormsSection};
`, context);
const {data, groupedFacts, citationsFor, groupedEditions, groupedIdentifiers, identifierDetails, identifiersSection, sourcesSection, journeySection, datingEvidence, factItems, bowlAppearance, recordedFormsSection} = context.T;

test("form is compact and same-witness fading accompanies writing legibility", () => {
  const report = (field, field_group, value) => ({field, field_group, value, source_id: "SRC", locator: "entry 39"});
  data.factsBy.ID = [report("reported_bowl_form", "vessel_form", "Round base."),
    report("reported_fragment_type", "vessel_form", "Full profile."),
    report("reported_physical_condition", "condition", "Two large fragments, each constitutes approximately one quarter of the bowl. Broken. Faded."),
    report("reported_writing_condition", "condition", "Partly legible.")];
  const html = bowlAppearance("ID");
  assert.match(html, /Round base; full profile\./);
  assert.doesNotMatch(html, /Fragment:|Broken/);
  assert.match(html, /<small>Writing<\/small>Faded; partly legible\./);
  assert.match(html, /approximately one quarter/);
  assert.match(recordedFormsSection("ID"), /Broken\. Faded/);
});

test("condition grouping preserves uncertainty, conflicts, and non-writing fading", () => {
  data.factsBy.ID = [
    {field: "reported_physical_condition", field_group: "condition", value: "Complete. Broken. Faded glaze.", source_id: "SRC", locator: "entry 1"},
    {field: "reported_writing_condition", field_group: "condition", value: "Probably legible.", source_id: "SRC", locator: "entry 1"},
    {field: "reported_writing_condition", field_group: "condition", value: "Illegible.", source_id: "OTHER", locator: "entry 1"},
    {field: "condition", field_group: "condition", value: "Faded.", source_id: "OTHER"},
  ];
  const html = bowlAppearance("ID");
  assert.match(html, /Complete\. Broken\. Faded glaze/);
  assert.match(html, /Probably legible; illegible/);
  assert.match(html, /Other condition reports/);
  assert.doesNotMatch(html, /<small>Writing<\/small>Faded/);
});

test("a different source or locator cannot move an unpaired fading clause", () => {
  data.factsBy.ID = [
    {field: "reported_physical_condition", field_group: "condition", value: "Incomplete. Faded.", source_id: "SRC", locator: "entry 1"},
    {field: "reported_writing_condition", field_group: "condition", value: "Legible.", source_id: "OTHER", locator: "entry 1"},
  ];
  assert.match(bowlAppearance("ID"), /<small>Vessel<\/small>Incomplete\. Faded\./);
  data.factsBy.ID[1].source_id = "SRC"; data.factsBy.ID[1].locator = "entry 2";
  assert.match(bowlAppearance("ID"), /<small>Vessel<\/small>Incomplete\. Faded\./);
});

test("Penn source fields share one catalogue locator without losing named sections", () => {
  data.factsBy.ID = ["", " — Description", " — Inscription Language", " — Provenience"].map(suffix =>
    ({source_id: "SRC", locator: "https://collections.penn.museum/collections/object/15709" + suffix}));
  data.textsBy.ID = []; data.editionsBy.ID = []; data.mediaBy.ID = [];
  const html = sourcesSection("ID");
  assert.equal((html.match(/Penn web object 15709/g) || []).length, 1);
  assert.match(html, /Description; Inscription Language; Provenience/);
});

test("Penn fragment abbreviations expand without changing the completeness report", () => {
  data.factsBy.ID = [{field:"reported_physical_condition",field_group:"condition",value:"Incomplete-12 Frag"}];
  assert.match(bowlAppearance("ID"), /Incomplete; 12 fragments/);
  assert.match(recordedFormsSection("ID"), /Incomplete-12 Frag/);
  data.factsBy.ID[0].value = "Complete-1 Frag";
  assert.match(bowlAppearance("ID"), /Complete; 1 fragment/);
});

test("Berlin designation spelling variants display once with all assigning bodies", () => {
  const rows = [{scheme: "collection designation", value: "VA.2422"},
    {scheme: "collection designation", value: "VA 2422", assigning_body: "Old museum"},
    {scheme: "collection designation", value: "VA 2422", assigning_body: "Another source"},
    {scheme: "collection designation", value: "VA.Bab.2422"}];
  const html = identifierDetails(rows);
  assert.equal((html.match(/collection designation/g) || []).length, 2);
  assert.match(html, /Old museum; Another source/);
  assert.match(html, /VA\.Bab\.2422/);
  const publications = identifierDetails([
    {scheme: "publication object key", value: "Edition A::6"},
    {scheme: "publication object key", value: "Edition B::6"}]);
  assert.match(publications, /Edition A/);
  assert.match(publications, /Edition B/);
});

test("identical source pages appear once while witness types and different ranges survive", () => {
  data.factsBy.ID = []; data.mediaBy.ID = []; data.editionsBy.ID = [];
  data.textsBy.ID = [
    {source_id: "SRC", access_locator: "Text K — transcription; printed p. 92; PDF p. 10"},
    {source_id: "SRC", access_locator: "Text K — translation; printed p. 92; PDF p. 10"},
    {source_id: "SRC", access_locator: "Text K — source extract; printed pp. 92–93; PDF pp. 10–11"},
    {source_id: "SRC", access_locator: "Text K — commentary; printed pp. 92–93; PDF pp. 10–11"},
    {source_id: "OTHER", access_locator: "Text K — translation; printed p. 92; PDF p. 10"},
  ];
  const html = sourcesSection("ID");
  assert.equal((html.match(/printed p\. 92/g) || []).length, 2);
  assert.equal((html.match(/printed pp\. 92–93/g) || []).length, 1);
  assert.match(html, /transcription; translation/);
  assert.match(html, /source extract; commentary/);
});

test("writing condition stays distinguishable and placeholder forms disappear", () => {
  data.factsBy.ID = [
    {field_group: "condition", field: "reported_physical_condition", value: "Small fragment."},
    {field_group: "condition", field: "reported_writing_condition", value: "Legible."},
    {field_group: "vessel_form", field: "reported_fragment_type", value: "n/ a."},
  ];
  assert.match(factItems("ID", "condition"), /Writing: Legible/);
  assert.match(factItems("ID", "condition"), /Small fragment/);
  assert.equal(groupedFacts("ID", "vessel_form").length, 0);
});

test("equivalent date and measurement wording becomes one display value", () => {
  data.factsBy.ID = [
    {field_group: "dating", value: "c. 6th century CE", recorded_value: "About the 6th century CE",
      source_id: "SRC", locator: "pp. 323–336, bowl AC-MSEF"},
    {field_group: "dating", value: "c. 6th century CE", recorded_value: "c. 6th century CE",
      source_id: "SRC", locator: "pp. 323–336; AC-MSEF"},
    {field_group: "dimensions", value: "Diameter 150 mm; depth 56 mm",
      source_id: "SRC", locator: "p. 323"},
    {field_group: "dimensions", value: "15 cm diameter × 5.6 cm depth",
      source_id: "SRC", locator: "p. 323"},
  ];
  const dates = groupedFacts("ID", "dating");
  assert.equal(dates.length, 1);
  assert.equal(dates[0].display, "c. 6th century CE");
  assert.deepEqual([...dates[0].variants], ["About the 6th century CE", "c. 6th century CE"]);
  assert.equal(citationsFor(dates[0].reports).length, 1);
  const dimensions = groupedFacts("ID", "dimensions");
  assert.equal(dimensions.length, 1);
  assert.equal(dimensions[0].display, "Diameter 15 cm · Depth 5.6 cm");
});

test("measurement conventions and unparsed qualifications cannot collapse", () => {
  data.factsBy.ID = [
    "Diameter 15 cm; height 5 cm", "Outside diameter 150 mm; height 50 mm",
    "Opening diameter 15 cm; height 5 cm", "Approximately diameter 15 cm; height 5 cm",
    "Diameter 15 cm; height 5 cm; base 8 cm", "Diameter 15–16 cm; height 5 cm",
  ].map(value => ({field_group: "dimensions", value}));
  const values = groupedFacts("ID", "dimensions");
  assert.equal(values.length, 6);
  assert.match(values[1].display, /^Outside diameter 15 cm/);
  assert.match(values[2].display, /^Opening diameter 15 cm/);
  assert.match(values[3].display, /Approximately/);
  assert.match(values[4].display, /base 8 cm/);
  assert.match(values[5].display, /15–16/);
});

test("repeated place reports show one place while retaining both roles and all sources", () => {
  data.factsBy.ID = [
    {field_group: "provenance", field: "findspot", value: "Found/Acquired: Iraq, South",
      source_id: "SRC", locator: "Related objects: 1980-0415-19", certainty: "reported"},
    {field_group: "provenance", field: "production_place", value: "Made in: Iraq, South",
      source_id: "SRC", locator: "Related objects: 1980-0415-19", certainty: "reported"},
    {field_group: "provenance", field: "production_place", value: "Iraq, South",
      source_id: "OTHER", locator: "p. 4", certainty: "reported"},
  ];
  const html = journeySection("ID");
  assert.equal((html.match(/Iraq, South/g) || []).length, 1);
  assert.match(html, /Find or acquisition place · Reported production place/);
  assert.doesNotMatch(html, /Related objects|p\. 4|<cite/);
  assert.match(sourcesSection("ID"), /Related objects: 1980-0415-19/);
  assert.match(sourcesSection("ID"), /p\. 4/);
  data.factsBy.ID.push({field_group: "provenance", field: "findspot", value: "Iraq, South", certainty: "uncertain"});
  assert.equal((journeySection("ID").match(/Iraq, South/g) || []).length, 2);
});

test("genuinely different dates remain separate", () => {
  data.factsBy.ID = [
    {field_group: "dating", value: "5th–6th centuries CE", source_id: "SRC", locator: "lot 1"},
    {field_group: "dating", value: "600–800 CE", source_id: "SRC", locator: "lot 1"},
  ];
  assert.equal(groupedFacts("ID", "dating").length, 2);
});

test("museum catalogue witnesses share one heading with all evidence and republication credits", () => {
  data.factsBy.BM = [
    {source_id: "BM1", locator: "Related objects: 1881-0714-6"},
    {source_id: "BM2", locator: "Google asset fQEubwbd_KepFw"},
    {source_id: "SEGAL", locator: "bowl 1"},
  ];
  data.sourceById.BM1 = {source_type: "museum_record", authors: "The British Museum",
    title: "Museum catalogue", publisher: "The British Museum", url: "https://museum.example/1", citation: "First witness"};
  data.sourceById.BM2 = {source_type: "museum_record", authors: "British Museum",
    title: "Ceramic bowl", publisher: "Google Arts & Culture", url: "https://google.example/1", citation: "Second witness"};
  data.sourceById.SEGAL = {source_type: "catalogue", authors: "J. B. Segal",
    publisher: "British Museum", issued_year: 2000, citation: "Scholarly edition"};
  const html = sourcesSection("BM");
  assert.equal((html.match(/<span>British Museum<\/span>/g) || []).length, 1);
  assert.match(html, /https:\/\/museum.example\/1/);
  assert.match(html, /https:\/\/google.example\/1/);
  assert.match(html, /via Google Arts & Culture/);
  assert.match(html, /First witness/); assert.match(html, /Second witness/);
  assert.match(html, /Related objects: 1881-0714-6/); assert.match(html, /Google asset/);
  assert.match(html, /J\. B\. Segal · 2000/);
});

test("exact site aliases group across records without losing qualifiers or original forms", () => {
  const place = (value, certainty = "reported") => ({field_group: "provenance", field: "findspot", value, certainty});
  data.factsBy.PLACES = [place("Excavated/Findspot: Tell Ibrahim (Kutha)"), place("Tell Ibrahim, Iraq")];
  assert.equal((journeySection("PLACES").match(/Kutha \(Tell Ibrahim\)/g) || []).length, 1);
  assert.match(recordedFormsSection("PLACES"), /Excavated\/Findspot: Tell Ibrahim \(Kutha\)/);
  assert.match(recordedFormsSection("PLACES"), /Tell Ibrahim, Iraq/);
  data.factsBy.PLACES.push(place("Tell Ibrahim, Iraq", "uncertain"), place("Probably Tell Ibrahim"),
    place("Tell Ibrahim, Iran"), place("Tell Ibrahim, Area A"), place("Tell Ibrahim | Nippur"));
  assert.equal((journeySection("PLACES").match(/<small>Reported findspot<\/small>/g) || []).length, 6);
  assert.match(journeySection("PLACES"), /Probably Tell Ibrahim/);
  assert.match(journeySection("PLACES"), /Tell Ibrahim, Iran/);
  assert.match(journeySection("PLACES"), /Tell Ibrahim, Area A/);
  data.factsBy.PLACES = [place("Nuffar"), place("Nippur, Iraq"), place("Nippur, locus 14")];
  assert.equal((journeySection("PLACES").match(/<small>Reported findspot<\/small>/g) || []).length, 2);
  assert.match(journeySection("PLACES"), /Nippur, locus 14/);
});

test("a date and its period share one statement and citation without merging differing dates", () => {
  data.factsBy.ID = [
    {field_group: "dating", value: "6th–8th centuries CE", source_id: "SRC", locator: "Details"},
    {field_group: "dating", value: "Late–Post Sasanian", source_id: "SRC", locator: "Details"},
  ];
  const html = datingEvidence("ID");
  assert.match(html, /6th–8th centuries CE · Late–Post Sasanian/);
  assert.equal((html.match(/<li>/g) || []).length, 1);
  assert.doesNotMatch(html, /Scholar 2003|Details|<cite/);
  assert.match(sourcesSection("ID"), /Source details/);
  data.factsBy.ID[1].source_id = "OTHER";
  assert.equal((datingEvidence("ID").match(/<li>/g) || []).length, 2);
  data.factsBy.ID.push({field_group: "dating", value: "5th century CE", source_id: "SRC", locator: "Details"});
  assert.match(datingEvidence("ID"), /Proposed dates/);
  assert.match(datingEvidence("ID"), /5th century CE/);
});

test("same-source publication rows collapse while distinct sources remain", () => {
  const rows = [
    {source_id: "SRC", citation: "Edition", locator: "pp. 323–336, bowl AC-MSEF",
      access_url: "https://example.test/edition"},
    {source_id: "SRC", citation: "Edition", locator: "pp. 323–336; AC-MSEF",
      access_url: "https://example.test/edition"},
    {source_id: "FORD", citation: "Ford 2014", locator: "p. 256; figures 25–26",
      access_url: "https://example.test/ford"},
  ];
  const grouped = groupedEditions(rows);
  assert.equal(grouped.length, 2);
  assert.equal(grouped[0].locators.length, 1);
  assert.equal(grouped[1].citation, "Ford 2014");
});

test("identity-wide identifier duplicates collapse and publication keys remain readable", () => {
  const rows = [
    {scheme: "publication designation", value: "AC-MSEF", assigning_body: "Martínez Borobio"},
    {scheme: "publication designation", value: "AC-MSEF", assigning_body: null},
    {scheme: "collection designation", value: "AC-MSEF", assigning_body: "Museo Sefardí"},
    {scheme: "publication object key", value: "Martínez Borobio 2003::AC-MSEF", assigning_body: "Martínez Borobio"},
    {scheme: "collection designation", value: "Museo Sefardí 1073", assigning_body: null},
    {scheme: "publication object key", value: "Ford 2014::Museo Sefardí 1073", assigning_body: "IBI"},
  ];
  assert.equal(groupedIdentifiers(rows).length, 2);
  const html = identifiersSection(["Museo Sefardí de Toledo AC-MSEF"], rows,
    "Museo Sefardí, Toledo · 1073");
  assert.equal((html.match(/AC-MSEF/g) || []).length, 1);
  assert.match(html, /published in Martínez Borobio 2003/);
  assert.match(html, /Museo Sefardí 1073/);
});

test("AIT27 duplicate page and item citations use the richer locator only", () => {
  const rows = [
    {source_id: "SRC", locator: "p. 325, item 27"},
    {source_id: "SRC", locator: "Catalogue, text 27, printed p. 325; PDF p. 331; size column (height by diameter)"},
  ];
  assert.equal(citationsFor(rows).length, 1);
  assert.match(citationsFor(rows)[0], /PDF p. 331/);
  assert.equal(citationsFor([...rows, {source_id: "SRC", locator: "p. 325, item 28"}]).length, 2);
  assert.equal(citationsFor([...rows, {source_id: "SRC", locator: "p. 326, item 27"}]).length, 2);
  assert.equal(citationsFor([...rows, {source_id: "OTHER", locator: "p. 325, item 27"}]).length, 2);
  assert.equal(citationsFor([...rows, {source_id: "SRC", locator: "p. 325, item 27; lines 1–3"}]).length, 2);
  assert.equal(citationsFor([{source_id: "SRC", locator: "PDF p. 325, item 27"}, rows[0]]).length, 2);
});


test("bibliography prefers a museum record over its photograph and preserves private editions", () => {
  data.sourceById.SRC.url = "https://museum.test/object/79917";
  data.factsBy.ID = [{source_id: "SRC", locator: "Details"}];
  data.textsBy = {};
  data.editionsBy = {};
  data.mediaBy = {ID: [{source_id: "SRC", url: "https://museum.test/photo.jpg"}]};
  const museum = sourcesSection("ID");
  assert.match(museum, /href="https:\/\/museum.test\/object\/79917"/);
  assert.doesNotMatch(museum, /photo.jpg/);
  // The projection keeps museum URLs in citation locators, rather than a URL
  // column on its bounded source metadata table.
  delete data.sourceById.SRC.url;
  data.factsBy.ID[0].locator = "https://museum.test/object/79917";
  assert.match(sourcesSection("ID"), /href="https:\/\/museum.test\/object\/79917"/);
  data.editionsBy.ID = [{source_id: "SRC", access_url: "/api/private-captures/CAP-TEST", locator: "p. 1"}];
  assert.match(sourcesSection("ID"), /href="\/api\/private-captures\/CAP-TEST"/);
});


test("machine locators occur only under Sources, including NLI and Penn facts", () => {
  data.factsBy.ID = [
    {field_group: "dimensions", value: "Height 7.2 cm · Circumference 16.4 cm", source_id: "SRC", locator: "MMS 997008712546905171"},
    {field_group: "condition", value: "Incomplete; 11 fragments", source_id: "SRC", locator: "Penn object 151160; Details: Description; checked 2026-10-01"},
  ];
  const main = factItems("ID", "dimensions") + factItems("ID", "condition");
  assert.doesNotMatch(main, /MMS|Penn object|checked|<cite/);
  const sources = sourcesSection("ID");
  assert.match(sources, /MMS 997008712546905171/);
  assert.match(sources, /Penn object 151160/);
  assert.match(sources, /Source details/);
});
