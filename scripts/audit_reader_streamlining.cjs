/* Render every private bowl page without a browser. Store only IDs and counts;
 * flags are an editorial review queue, not evidence decisions or permission to
 * truncate inscriptions. Run after scripts/build_mike_access.py. */
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const out = process.argv[2] || path.join(root, "research/audits/reader_streamlining_2026-10-01.json");
const built = path.join(root, "site/mike-build/data");
const code = fs.readFileSync(path.join(root, "web/reading.js"), "utf8")
  .replace("window.ReadingRoom = {render, invalidate};", "window.audit = {data, load, renderObject};");
const context = vm.createContext({
  window: {},
  fetch: async url => ({ok: true, json: async () => JSON.parse(fs.readFileSync(
    path.join(built, url.split("/").pop().replace(/\.json$/, "") + ".json"), "utf8"))}),
});
vm.runInContext(code, context);

(async () => {
  const {data, load, renderObject} = context.window.audit;
  await load();
  const queue = [], failures = [];
  const totals = {};
  for (const bowl of data.identity_clusters) {
    const view = {};
    renderObject(view, bowl.identity_id);
    const html = view.innerHTML;
    const main = html.split('<h2>Sources</h2>')[0].split('<details class="entry-apparatus">')[0]
      .replace(/<blockquote[\s\S]*?<\/blockquote>/g, "");
    const problems = [];
    if (/Consult the sources|No (?:original|translation).*available/i.test(main)) problems.push("empty_reading_boilerplate");
    if (/Related objects:|MMS \d{10,}|web-visible catalogue checked|Details: Description/.test(main)) problems.push("source_metadata_among_facts");
    if (/<cite>/.test(main)) problems.push("inline_citation_column");
    if (/Summary and commentary|not an independent translation|Private research copy/.test(main)) problems.push("repeated_editorial_boilerplate");
    if (problems.length) failures.push({identity_id: bowl.identity_id, problems});

    const flags = [];
    const facts = data.factsBy[bowl.identity_id] || [];
    const texts = data.textsBy[bowl.identity_id] || [];
    if (facts.some(row => row.value.length > 140)) flags.push("long_fact_wording");
    const groups = new Map();
    for (const row of facts) {
      const key = row.value.trim().toLowerCase();
      if (key.length < 24) continue;
      if (!groups.has(key)) groups.set(key, new Set());
      groups.get(key).add(row.field_group);
    }
    if ([...groups.values()].some(group => group.size > 1)) flags.push("same_fact_in_multiple_sections");
    const standfirst = texts.find(row => row.editor === "Incantation Bowl Index card line")?.content?.toLowerCase() || "";
    if (facts.some(row => row.value.length > 18 && standfirst.includes(row.value.toLowerCase()))) flags.push("overview_repeats_fact");
    if (texts.some(row => row.text_type === "summary" && row.editor !== "Incantation Bowl Index card line"
      && row.editor !== "Incantation Bowl Index source commentary" && (row.content || "").length > 240)) flags.push("long_commentary");
    if (/class="entry-credit">[^<]{180}/.test(main)) flags.push("long_credit");
    for (const flag of flags) totals[flag] = (totals[flag] || 0) + 1;
    queue.push({identity_id: bowl.identity_id, flags, status: "pending_editorial_review"});
  }
  queue.sort((a, b) => b.flags.length - a.flags.length || a.identity_id.localeCompare(b.identity_id));
  const report = {
    schema_version: 1, checked_identities: queue.length,
    corpus_digest: JSON.parse(fs.readFileSync(path.join(root, "data/db-state.json"), "utf8")).corpus_digest,
    generated_at: new Date().toISOString(),
    contract_failures: failures,
    flagged_identities: queue.filter(row => row.flags.length).length,
    flag_counts: totals,
    policy: "Content-free whole-corpus editorial queue. Flags identify possible clutter; they do not authorize shortening inscription texts, erasing source data, or resolving conflicting claims. Every identity remains pending human editorial inspection.",
    queue,
  };
  fs.writeFileSync(out, JSON.stringify(report, null, 2) + "\n");
  process.stdout.write(JSON.stringify({checked: queue.length, contract_failures: failures.length,
    flagged: report.flagged_identities, flag_counts: totals}) + "\n");
  if (failures.length) process.exitCode = 1;
})().catch(error => { process.stderr.write(error.stack + "\n"); process.exitCode = 1; });
