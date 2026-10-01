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
  globalThis.T = {data, groupedFacts, citationsFor, groupedEditions, groupedIdentifiers, identifiersSection, sourcesSection, journeySection, datingEvidence, factItems};
`, context);
const {data, groupedFacts, citationsFor, groupedEditions, groupedIdentifiers, identifiersSection, sourcesSection, journeySection, datingEvidence, factItems} = context.T;

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
