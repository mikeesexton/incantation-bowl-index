const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync("web/app.js", "utf8");
const presentationOnly = source.slice(0, source.indexOf("async function loadIdentities"));
const context = vm.createContext({URL, URLSearchParams, FormData});
vm.runInContext(presentationOnly, context);

test("search controls follow the approved reader-first order", () => {
  const html = fs.readFileSync("web/index.html", "utf8");
  const ids = ["ritual-filter", "language-filter", "provenance-filter", "collection-filter",
    'name="available"', "type-filter"];
  const positions = ids.map(value => html.indexOf(value));
  assert.ok(positions.every(position => position >= 0));
  assert.deepEqual([...positions].sort((a, b) => a - b), positions);
  assert.match(html, /Most content available/);
});

function render(item) {
  context.fixture = item;
  return vm.runInContext("identityRow(fixture)", context);
}

test("a sparse or stale API row cannot blank the catalogue", () => {
  const html = render({
    identity_id: "IDENT-123456789ABC",
    label: "Sparse bowl",
    languages: [],
    dating: [],
    identifiers: [],
    authenticity: "unassessed",
  });
  assert.match(html, /Sparse bowl/);
  assert.match(html, /Language not recorded/);
  assert.match(html, /Date not recorded/);
  assert.match(html, /0 sources/);
});

test("script is optional and shown separately from language", () => {
  const html = render({
    identity_id: "IDENT-123456789ABC",
    display_name: "Test Museum · 1",
    display_language: "Aramaic",
    display_date: "6th century CE",
    scripts: ["Square script"],
    source_count: 1,
    authenticity: "accepted",
  });
  assert.match(html, /Aramaic/);
  assert.match(html, /Script: Square script/);
  assert.match(html, /1 source</);
});
