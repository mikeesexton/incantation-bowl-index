const assert = require("node:assert");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("web/reading.js", "utf8");
const body = source.slice(source.indexOf("const TABLES"), source.indexOf("function renderBrowse"));
const context = vm.createContext({window: {}});
vm.runInContext(body + "\nglobalThis.T = {facetCounts, data, BROWSE};", context);
const {facetCounts, data, BROWSE} = context.T;

data.identity_clusters = [{identity_id: "IDENT-1", members: ["IBI-1"]}];
data.clusterById = {"IDENT-1": data.identity_clusters[0]};
data.facts = [
  {object_id: "IBI-1", field_group: "ritual", value: "Halbas-Lilit"},
  {object_id: "IBI-1", field_group: "client", value: "Ada; Mara"},
];
data.facets = [
  {object_id: "IBI-1", facet_group: "ritual", facet_label: "Protection"},
  {object_id: "IBI-1", facet_group: "biblical_intertexts", facet_label: "Zech 3:2"},
  {object_id: "IBI-1", facet_group: "biblical_intertexts", facet_label: "Deut 6:4"},
];

test("browse categories follow the meaning-first order", () => {
  assert.deepStrictEqual(JSON.parse(JSON.stringify(BROWSE.map(row => row[1]))), [
    "What they do", "People named", "What is drawn", "Scripture quoted", "Language",
    "Where they come from", "Where they are", "Hands and scribes",
  ]);
});

test("controlled groups browse project labels rather than raw source wording", () => {
  assert.deepStrictEqual(JSON.parse(JSON.stringify(facetCounts("ritual"))), [
    {value: "Protection", count: 1, ids: ["IDENT-1"]},
  ]);
});

test("other browse groups retain their concise source values", () => {
  assert.deepStrictEqual(JSON.parse(JSON.stringify(facetCounts("client"))), [
    {value: "Ada", count: 1, ids: ["IDENT-1"]},
    {value: "Mara", count: 1, ids: ["IDENT-1"]},
  ]);
});

test("scripture uses canonical book order rather than frequency or alphabet", () => {
  assert.deepStrictEqual(JSON.parse(JSON.stringify(facetCounts("biblical_intertexts").map(row => row.value))), [
    "Deut 6:4", "Zech 3:2",
  ]);
});
