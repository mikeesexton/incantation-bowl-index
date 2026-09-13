const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

// The presentation helpers sit above loadIdentities; the review renderers sit well
// below it, so the two regions are stitched together rather than sliced once.
const source = fs.readFileSync("web/app.js", "utf8");
const helpers = source.slice(0, source.indexOf("async function loadIdentities"));
const renderers = source.slice(
  source.indexOf("function reviewListItem"),
  source.indexOf("function reviewDetailMarkup"),
);
const context = vm.createContext({URL, URLSearchParams, FormData});
vm.runInContext(helpers + "\n" + renderers, context);

function panel(evidence) {
  context.fixture = evidence;
  return vm.runInContext("pairEvidencePanel(fixture)", context);
}

test("agreeing and conflicting facets are both named, not just coloured", () => {
  const html = panel({
    band: "conflict",
    agreeing_groups: ["location"],
    conflicting_groups: ["language"],
    differing_non_discriminating_groups: [],
    groups_on_one_side_only: ["material"],
  });
  assert.match(html, /Agree/);
  assert.match(html, /Disagree/);
  assert.match(html, /Location/);
  assert.match(html, /Language/);
  assert.match(html, /claims disagree/);
});

test("no_overlap reads as silence, not as disagreement", () => {
  const html = panel({
    band: "no_overlap", agreeing_groups: [], conflicting_groups: [],
    differing_non_discriminating_groups: [], groups_on_one_side_only: ["dimensions"],
  });
  assert.match(html, /nothing compared/);
  assert.match(html, /silence, not disagreement/);
  assert.doesNotMatch(html, /Disagree/);
});

test("a differing publication is shown as not being about the object", () => {
  const html = panel({
    band: "corroborated", agreeing_groups: ["location"], conflicting_groups: [],
    differing_non_discriminating_groups: ["publication"], groups_on_one_side_only: [],
  });
  assert.match(html, /Differ, but not about the object/);
  assert.match(html, /different publications is expected/);
});

test("the panel states its limits and never proposes a decision", () => {
  const html = panel({
    band: "corroborated", agreeing_groups: ["location"], conflicting_groups: [],
    differing_non_discriminating_groups: [], groups_on_one_side_only: [],
  });
  assert.match(html, /stored claims only/);
  assert.match(html, /not a recommendation/);
  // Phrases that would propose an outcome. "not a recommendation" is the
  // disclaimer and must survive, so the check is for proposing language, not for
  // the substring "recommend".
  for (const phrase of [
    "should be merged", "recommend merging", "likely the same",
    "probably the same", "safe to merge", "we recommend",
  ]) {
    assert.ok(!html.toLowerCase().includes(phrase), `panel must not say "${phrase}"`);
  }
  assert.match(html, /not a recommendation/);
});

test("a missing or empty payload renders nothing rather than breaking the page", () => {
  assert.equal(panel(null), "");
  const empty = panel({
    band: "no_overlap", agreeing_groups: [], conflicting_groups: [],
    differing_non_discriminating_groups: [], groups_on_one_side_only: [],
  });
  assert.match(empty, /Neither record carries a comparable claim/);
});

test("an unknown band from a newer server does not blank the panel", () => {
  const html = panel({band: "speculative", agreeing_groups: ["location"]});
  assert.match(html, /Speculative/);
  assert.match(html, /Location/);
});

test("queue rows show the band, and survive a row that lacks one", () => {
  context.row = {
    id: "DED-1", status: "pending", object_a_label: "A", object_b_label: "B",
    method: "exact_identifier", score: 0.99, pair_band: "conflict",
  };
  const withBand = vm.runInContext("reviewListItem(row)", context);
  assert.match(withBand, /claims disagree/);
  context.row2 = {
    id: "DED-2", status: "pending", object_a_label: "A", object_b_label: "B",
    method: "label_similarity", score: 0.4,
  };
  const without = vm.runInContext("reviewListItem(row2)", context);
  assert.match(without, /label_similarity/);
  assert.doesNotMatch(without, /pair-band/);
});
