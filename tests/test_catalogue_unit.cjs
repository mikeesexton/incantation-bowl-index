const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync("web/app.js", "utf8");
const presentationOnly = source.slice(0, source.indexOf("async function loadIdentities"));
const context = vm.createContext({URL, URLSearchParams, FormData});
vm.runInContext(presentationOnly, context);

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
