/* The reading room.
 *
 * Reads only /api/reader/*, which serves the same gated projection the file
 * export writes. Everything here would work unchanged against static JSON, so
 * a published version is the same code and cannot see more than this one does.
 */
(function () {
  "use strict";
  const TABLES = ["identity_clusters", "objects", "facts", "texts", "editions", "sources", "media",
    "works", "contributors", "scholarship_decades"];
  const data = {loaded: false};
  const esc = value => String(value === null || value === undefined ? "" : value)
    .replace(/[&<>"']/g, ch => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch]));

  async function load() {
    if (data.loaded) return data;
    const manifest = await fetch("/api/reader/manifest").then(r => r.json());
    const fetched = await Promise.all(TABLES.map(name =>
      fetch(`/api/reader/${name}`).then(r => r.json()).then(payload => [name, payload.rows])));
    fetched.forEach(([name, rows]) => { data[name] = rows; });
    data.manifest = manifest;

    // Index by object, then roll up to the identity that owns the object.
    const owner = {};
    data.identity_clusters.forEach(cluster => {
      cluster.members = JSON.parse(cluster.member_ids || "[]");
      cluster.members.forEach(id => { owner[id] = cluster.identity_id; });
    });
    const bucket = key => {
      const index = {};
      (data[key] || []).forEach(row => {
        const id = owner[row.object_id];
        if (!id) return;
        (index[id] = index[id] || []).push(row);
      });
      return index;
    };
    data.factsBy = bucket("facts");
    data.textsBy = bucket("texts");
    data.editionsBy = bucket("editions");
    data.mediaBy = bucket("media");
    data.sourceById = Object.fromEntries(data.sources.map(s => [s.id, s]));
    data.objectById = Object.fromEntries(data.objects.map(o => [o.id, o]));
    data.clusterById = Object.fromEntries(data.identity_clusters.map(c => [c.identity_id, c]));
    data.loaded = true;
    return data;
  }

  const factsOf = (id, group) => (data.factsBy[id] || []).filter(f => f.field_group === group);
  const values = (id, group) => [...new Set(factsOf(id, group).map(f => f.value))];
  const first = (id, group) => values(id, group)[0] || "";

  /* A bowl's text spirals from the base to the rim. Draw that from the object's
   * own recorded line count, so the mark is a diagram rather than an ornament. */
  function spiral(cluster) {
    const recorded = first(cluster.identity_id, "text_form");
    const digits = (recorded.match(/\d+/) || [])[0];
    const words = {one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8,
      nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15};
    const named = Object.keys(words).find(w => recorded.toLowerCase().includes(w));
    const turns = Math.min(14, Math.max(3, digits ? Number(digits) : (named ? words[named] : 7)));
    const known = Boolean(digits || named);
    const points = [];
    const steps = turns * 36;
    for (let i = 0; i <= steps; i += 1) {
      const t = i / steps;
      const angle = t * turns * 2 * Math.PI;
      const radius = 4 + t * 40;
      points.push(`${(48 + radius * Math.cos(angle)).toFixed(1)},${(48 + radius * Math.sin(angle)).toFixed(1)}`);
    }
    return `<svg class="spiral${known ? "" : " is-estimated"}" viewBox="0 0 96 96" role="img"
      aria-label="${known ? esc(recorded) : "Line count not recorded"}"><circle class="spiral-rim" cx="48" cy="48" r="45"/>
      <polyline class="spiral-line" points="${points.join(" ")}"/></svg>`;
  }

  const clip = (value, limit) => value.length > limit
    ? value.slice(0, value.lastIndexOf(" ", limit) > 0 ? value.lastIndexOf(" ", limit) : limit) + "…"
    : value;

  function summarise(cluster, limit) {
    const id = cluster.identity_id;
    // Prefer the shortest ritual statement: a purpose reads better than an
    // installation instruction, and the short ones are almost always purposes.
    const purpose = values(id, "ritual").sort((a, b) => a.length - b.length)[0] || "";
    const client = values(id, "client")[0];
    let line = "";
    if (purpose && client) line = `${purpose} — for ${client}`;
    else if (purpose) line = purpose;
    else if (client) line = `Named for ${client}`;
    else {
      const verses = values(id, "biblical_intertexts");
      if (verses.length) line = `Quotes ${verses.slice(0, 3).join(", ").replace(/[[\]"]/g, "")}`;
    }
    return limit ? clip(line, limit) : line;
  }

  function card(cluster) {
    const id = cluster.identity_id;
    const text = (data.textsBy[id] || []).find(t => t.content_status === "included");
    const line = summarise(cluster, 96);
    const place = first(id, "location");
    const tongue = first(id, "language");
    const when = first(id, "dating");
    return `<article class="bowl-card"><a href="#/reading/${encodeURIComponent(id)}">
      <div class="bowl-card-mark">${spiral(cluster)}</div>
      <div class="bowl-card-body">
        <h3>${esc(cluster.display_name)}</h3>
        ${line ? `<p class="bowl-card-line">${esc(line)}</p>` : ""}
        <p class="bowl-card-meta">${[place, tongue, when].filter(Boolean).map(esc).join(" · ")}</p>
        ${text ? `<p class="bowl-card-flag">Text you can read</p>` : ""}
      </div></a></article>`;
  }

  function renderIndex(view) {
    const readable = data.identity_clusters
      .filter(c => c.reading_score >= 4)
      .sort((a, b) => b.reading_score - a.reading_score ||
        a.display_name.localeCompare(b.display_name));
    const thin = data.identity_clusters.length - readable.length;
    const m = data.manifest;
    view.innerHTML = `<div class="reading-head">
        <span class="eyebrow">Late antique Mesopotamia, roughly 500–700 CE</span>
        <h1 id="reading-title">Bowls worth reading</h1>
        <p class="standfirst">Ordinary clay vessels, inscribed in a spiral and buried upside
          down beneath the floors of houses in Sasanian Mesopotamia to keep something out.
          This index holds <strong>${data.identity_clusters.length.toLocaleString()}</strong>
          records of them. Measured against the field's own control list of published Jewish
          Babylonian Aramaic bowls, it cites <strong>115 of 115</strong> publications and has
          attached objects to almost none of them, so treat coverage as a reading list rather
          than a corpus.</p>
        <p class="standfirst-note">${m.texts_included_rows} bowls have a text you can read here.
          ${m.texts_withheld_rows} more name the edition that prints theirs.
          No image is cleared for reuse yet, so every mark below is drawn from the object's own
          recorded line count.</p>
      </div>
      <div class="bowl-grid">${readable.map(card).join("")}</div>
      <p class="thin-note"><a href="#/explore">${thin.toLocaleString()} further records</a>
        hold little beyond an identifier and a source. They are in the research explorer.</p>`;
  }

  function factList(id, group, heading) {
    const rows = factsOf(id, group);
    if (!rows.length) return "";
    const seen = new Set();
    const items = rows.filter(r => !seen.has(r.value) && seen.add(r.value)).map(r => {
      const source = data.sourceById[r.source_id];
      const cite = source ? `${source.authors || source.title || ""} ${source.issued_year || ""}`.trim() : "";
      return `<li><span>${esc(r.value.replace(/^\["|"\]$/g, "").replace(/","/g, ", "))}</span>
        ${cite ? `<cite title="${esc(r.locator || "")}">${esc(cite)}</cite>` : ""}</li>`;
    });
    return `<section class="entry-block"><h2>${esc(heading)}</h2><ul class="fact-list">${items.join("")}</ul></section>`;
  }

  /* The citation usually opens with the editor's name; do not say it twice. */
  function credit(text) {
    const citation = (text.access_citation || "").trim();
    const editor = (text.editor || "").trim();
    const surname = editor.split(/\s+/).pop();
    const lead = editor && surname && !citation.toLowerCase().startsWith(surname.toLowerCase())
      ? editor + ", " : "";
    return [lead + citation, text.access_locator].filter(Boolean).join(" · ");
  }

  function renderObject(view, identityId) {
    const cluster = data.clusterById[identityId];
    if (!cluster) { view.innerHTML = `<p class="dossier-loading">No such record.</p>`; return; }
    const id = cluster.identity_id;
    const texts = data.textsBy[id] || [];
    const readable = texts.filter(t => t.content_status === "included");
    const withheld = texts.filter(t => t.content_status !== "included");
    const editions = data.editionsBy[id] || [];
    const rawLabels = cluster.members.map(m => (data.objectById[m] || {}).label).filter(Boolean);

    view.innerHTML = `<article class="entry">
      <a class="entry-back" href="#/reading">← Bowls worth reading</a>
      <header class="entry-head">
        <div class="entry-mark">${spiral(cluster)}</div>
        <div>
          <h1 id="reading-title">${esc(cluster.display_name)}</h1>
          <p class="entry-standfirst">${esc(summarise(cluster) || "No description recorded.")}</p>
          <p class="entry-meta">${[first(id, "location"), first(id, "language"), first(id, "dating")]
            .filter(Boolean).map(esc).join(" · ")}</p>
        </div>
      </header>

      ${readable.length ? readable.map(t => `<section class="entry-block entry-text">
        <h2>What it says</h2>
        <blockquote dir="auto" lang="${esc(t.language === "English" ? "en" : "")}">${esc(t.content)}</blockquote>
        <p class="entry-credit">${esc(credit(t))}</p>
      </section>`).join("") : ""}

      ${withheld.length ? `<section class="entry-block">
        <h2>${readable.length ? "Further texts" : "What it says"}</h2>
        <p class="entry-note">Printed in the edition below rather than reproduced here.</p>
        <ul class="fact-list">${withheld.map(t => `<li><span>${esc(t.text_type)}${t.language ? " · " + esc(t.language) : ""}</span>
          <cite>${t.access_url ? `<a href="${esc(t.access_url)}" rel="noreferrer">${esc(t.access_citation || "edition")}</a>`
            : esc(t.access_citation || "edition")}${t.access_locator ? " · " + esc(t.access_locator) : ""}</cite></li>`).join("")}</ul>
      </section>` : ""}

      ${factList(id, "client", "Who it names")}
      ${factList(id, "practitioner", "Who wrote it, as reported")}
      ${factList(id, "target", "What it acts against")}
      ${factList(id, "ritual", "What it does")}
      ${factList(id, "biblical_intertexts", "Scripture it quotes")}
      ${factList(id, "visual", "What is drawn on it")}
      ${factList(id, "text_form", "How the text is set")}
      ${factList(id, "dimensions", "Size")}
      ${factList(id, "material", "Material")}
      ${factList(id, "condition", "Condition")}
      ${factList(id, "script", "Script")}

      ${editions.length ? `<section class="entry-block"><h2>Where it is published</h2>
        <ul class="fact-list">${editions.map(e => `<li><span>${esc(e.citation)}</span>
          <cite>${e.locator ? esc(e.locator) + " · " : ""}${e.access_url
            ? `<a href="${esc(e.access_url)}" rel="noreferrer">link</a>` : esc(e.access_status || "")}</cite></li>`).join("")}</ul>
      </section>` : ""}

      ${factList(id, "provenance", "Where it is said to come from")}
      <p class="entry-caveat">A reported findspot is a report. Listing an object here says
        nothing about its ownership, export history, or authenticity.</p>

      <details class="entry-apparatus"><summary>Record and evidence</summary>
        <dl>
          <dt>Recorded as</dt><dd>${rawLabels.map(esc).join("<br>") || "—"}</dd>
          <dt>Identity</dt><dd><code>${esc(cluster.identity_id)}</code>
            · ${esc(cluster.record_status)} · ${cluster.member_count} linked record(s)</dd>
          <dt>Evidence</dt><dd>${cluster.source_count} source(s), ${cluster.appearance_count} appearance(s)</dd>
          <dt>Coverage</dt><dd>${cluster.completeness_score}/10 core · ${cluster.content_completeness}/13 content</dd>
        </dl>
        <p><a href="#/explore">Open the research explorer</a> for the full claim-by-claim evidence chain.</p>
      </details>
    </article>`;
  }

  /* How the field grew. Two lines, because ours counts all scholarship held and
     the field line counts only Waller's JBA control list — the gap is the point. */
  function growthChart(rows) {
    /* SVG rather than styled divs: the console's CSP forbids inline styles, and
       geometry belongs in attributes anyway. */
    const live = rows.filter(r => r.held || r.field_control_list);
    const peak = Math.max(...live.map(r => Math.max(r.held, r.field_control_list)), 1);
    const W = 720, H = 150, gap = 3;
    const slot = W / live.length;
    const bars = live.map((r, i) => {
      const x = i * slot;
      const w = (slot - gap) / 2;
      const h1 = (r.held / peak) * H;
      const h2 = (r.field_control_list / peak) * H;
      return `<rect class="bar-held" x="${(x + 1).toFixed(1)}" y="${(H - h1).toFixed(1)}"
          width="${w.toFixed(1)}" height="${h1.toFixed(1)}"><title>${r.decade}s — ${r.held} held</title></rect>
        <rect class="bar-field" x="${(x + w + 2).toFixed(1)}" y="${(H - h2).toFixed(1)}"
          width="${w.toFixed(1)}" height="${h2.toFixed(1)}"><title>${r.decade}s — ${r.field_control_list} on the control list</title></rect>
        <text class="bar-label" x="${(x + slot / 2).toFixed(1)}" y="${H + 13}" text-anchor="middle">${String(r.decade).slice(2)}</text>`;
    }).join("");
    return `<figure class="growth">
      <svg viewBox="0 0 ${W} ${H + 18}" class="growth-plot" role="img"
        aria-label="Publications per decade, held here against Waller's control list">
        ${bars}<line class="bar-axis" x1="0" y1="${H}" x2="${W}" y2="${H}"/></svg>
      <figcaption><span class="key is-held"></span> scholarship held here
        <span class="key is-field"></span> Jewish Babylonian Aramaic publications on Waller's
        control list, 1853–2024. Ours counts every language and genre, so it runs higher after
        2000; the nineteenth century is where the two should agree, and roughly does.</figcaption></figure>`;
  }

  function renderScholarship(view) {
    const works = data.works;
    const held = works.filter(w => w.document_held).length;
    const classified = works.filter(w => w.scope).length;
    const byScope = {};
    works.forEach(w => { const k = w.scope_label; (byScope[k] = byScope[k] || []).push(w); });
    const people = data.contributors;
    view.innerHTML = `<div class="reading-head">
        <span class="eyebrow">1853 to 2024</span>
        <h1 id="reading-title">The literature</h1>
        <p class="standfirst">Every work this index draws on: <strong>${works.length}</strong>
          pieces of scholarship, separate from the ${(data.sources.length - works.length).toLocaleString()}
          museum, auction and dealer records that are sources but not scholarship.
          <strong>${held}</strong> are held here as a document; the rest are cited and unread.</p>
      </div>

      <section class="entry-block"><h2>How the field grew</h2>${growthChart(data.scholarship_decades)}</section>

      <section class="entry-block"><h2>Who wrote it</h2>
        <p class="entry-note">Ranked by publications held. Not by citations — this index has no
          citation graph, and only 9% of its sources carry a DOI, so a citation ranking would
          cover a tenth of the field and flatter whoever has the better metadata.</p>
        <ol class="contributor-list">${people.slice(0, 24).map((p, i) => `<li>
          <span class="rank">${String(i + 1).padStart(2, "0")}</span>
          <span class="who"><strong>${esc(p.display_name)}</strong>
            ${p.needs_check ? `<em title=${JSON.stringify(JSON.parse(p.spellings).join(" · "))}>${JSON.parse(p.spellings).length} spellings</em>` : ""}
            <small>${p.first_year || "?"}–${p.last_year || "?"}</small></span>
          <span class="tally">${p.works} work${p.works === 1 ? "" : "s"}${
            p.objects_published ? ` · ${p.objects_published} bowls` : ""}</span></li>`).join("")}</ol>
      </section>

      <section class="entry-block"><h2>What kind of work</h2>
        <p class="entry-note">${classified} of ${works.length} classified. Scope is a reading
          judgment, so it is derived only where the publication registry settles it and recorded
          as a decision otherwise; the rest are honestly unclassified.</p>
        ${Object.entries(byScope).sort((a, b) => b[1].length - a[1].length).map(([label, rows]) => `
          <details class="scope-group"><summary>${esc(label)} <span>${rows.length}</span></summary>
            <ul class="fact-list">${rows.slice(0, 40).map(w => `<li>
              <span>${esc(w.title)}${w.document_held ? ' <em class="held">held</em>' : ""}</span>
              <cite>${esc((w.authors || "").split(";")[0].split("[")[0])} ${w.issued_year || ""}${
                w.objects_published ? ` · ${w.objects_published} bowls` : ""}</cite></li>`).join("")}
            </ul>${rows.length > 40 ? `<p class="entry-note">and ${rows.length - 40} more</p>` : ""}
          </details>`).join("")}
      </section>`;
  }

  async function render() {
    const view = document.querySelector("#reading-view");
    if (!view) return;
    if (!data.loaded) view.innerHTML = `<p class="dossier-loading">Reading the corpus…</p>`;
    try {
      await load();
    } catch (error) {
      view.innerHTML = `<p class="dossier-loading">Could not read the corpus: ${esc(error.message)}</p>`;
      return;
    }
    const match = location.hash.match(/^#\/reading\/(.+)$/);
    if (location.hash.startsWith("#/scholarship")) renderScholarship(view);
    else if (match) renderObject(view, decodeURIComponent(match[1]));
    else renderIndex(view);
    view.scrollTop = 0;
  }

  window.ReadingRoom = {render};
})();
