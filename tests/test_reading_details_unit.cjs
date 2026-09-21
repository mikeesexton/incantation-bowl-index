const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("web/reading.js", "utf8");
const grouping = source.slice(source.indexOf("const tidy"), source.indexOf("function journeySection"));
const identifiers = source.slice(source.indexOf("function identifierRank"), source.indexOf("function renderObject"));
const context = vm.createContext({});
vm.runInContext(`
  const data = {factsBy: {}, sourceById: {SRC: {authors: "Scholar", issued_year: 2003}}};
  const factsOf = (id, group) => (data.factsBy[id] || []).filter(row => row.field_group === group);
  const esc = value => String(value ?? "");
  ${grouping}
  ${identifiers}
  globalThis.T = {data, groupedFacts, citationsFor, groupedEditions, groupedIdentifiers, identifiersSection};
`, context);
const {data, groupedFacts, citationsFor, groupedEditions, groupedIdentifiers, identifiersSection} = context.T;

test("equivalent date and measurement wording becomes one display value", () => {
  data.factsBy.ID = [
    {field_group: "dating", value: "c. 6th century CE", recorded_value: "About the 6th century CE",
      source_id: "SRC", locator: "pp. 323–336, bowl AC-MSEF"},
    {field_group: "dating", value: "c. 6th century CE", recorded_value: "c. 6th century CE",
      source_id: "SRC", locator: "pp. 323–336; AC-MSEF"},
    {field_group: "dimensions", value: "Opening diameter 15 cm; depth 5.6 cm",
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

test("genuinely different dates remain separate", () => {
  data.factsBy.ID = [
    {field_group: "dating", value: "5th–6th centuries CE", source_id: "SRC", locator: "lot 1"},
    {field_group: "dating", value: "600–800 CE", source_id: "SRC", locator: "lot 1"},
  ];
  assert.equal(groupedFacts("ID", "dating").length, 2);
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
