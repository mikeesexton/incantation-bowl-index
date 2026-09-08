/* The reading room.
 *
 * Reads only /api/reader/*, which serves the same gated projection the file
 * export writes. Everything here would work unchanged against static JSON, so
 * a published version is the same code and cannot see more than this one does.
 */
(function () {
  "use strict";
  const TABLES = ["identity_clusters", "objects", "identifiers", "facts", "texts", "editions", "sources", "media",
    "works", "contributors", "scholarship_decades", "publications"];
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
    data.identifiersBy = bucket("identifiers");
    data.textsBy = bucket("texts");
    data.editionsBy = bucket("editions");
    data.mediaBy = bucket("media");
    data.sourceById = Object.fromEntries(data.sources.map(s => [s.id, s]));
    data.objectById = Object.fromEntries(data.objects.map(o => [o.id, o]));
    data.clusterById = Object.fromEntries(data.identity_clusters.map(c => [c.identity_id, c]));
    data.identity_clusters.forEach(c => {
      const facts = data.factsBy[c.identity_id] || [];
      const text = (data.textsBy[c.identity_id] || []).find(x => x.content_status === "included");
      c.haystack = [c.display_name, ...(data.identifiersBy[c.identity_id] || []).flatMap(i => [i.scheme, i.value]),
        ...facts.map(f => f.value), text ? text.content : ""]
        .join(" ").toLowerCase();
    });
    data.loaded = true;
    return data;
  }

  const factsOf = (id, group) => (data.factsBy[id] || []).filter(f => f.field_group === group);
  const values = (id, group) => [...new Set(factsOf(id, group).map(f => f.value))];
  const first = (id, group) => values(id, group)[0] || "";

  function catalogueReturn() {
    try {
      const saved = JSON.parse(sessionStorage.getItem("bowlam.catalogue.return") || "null");
      if (saved?.hash?.startsWith("#/explore")) return saved.hash;
    } catch { /* use the collection root */ }
    return "#/explore";
  }

  function titleMarkup(cluster) {
    const title = esc(cluster.display_name);
    return title.replace(/\bIsIAO\b/, `<abbr class="identifier-help" tabindex="0"
      title="Italian Institute for Africa and the Orient; a historical collection prefix.">IsIAO</abbr>`);
  }

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

  /* An approved image, or nothing. The projection emits a media row only for a
     current approval, so this cannot show an uncleared picture — there is simply
     no row to render, and the spiral carries the grid until RIGHTS-002 lands. */
  function mark(cluster) {
    const image = (data.mediaBy[cluster.identity_id] || [])
      .find(m => m.media_type === "image" && m.url);
    if (!image) return spiral(cluster);
    return `<img class="bowl-image" src="${esc(image.url)}" alt="${esc(cluster.display_name)}"
      loading="lazy" decoding="async">${image.attribution
        ? `<span class="bowl-credit">${esc(image.attribution)}</span>` : ""}`;
  }

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
    const place = cluster.display_collection;
    const tongue = cluster.display_language;
    const when = cluster.display_date;
    return `<article class="bowl-card"><a href="#/reading/${encodeURIComponent(id)}">
      <div class="bowl-card-mark">${mark(cluster)}</div>
      <div class="bowl-card-body">
        <h3>${titleMarkup(cluster)}</h3>
        ${line ? `<p class="bowl-card-line">${esc(line)}</p>` : ""}
        <p class="bowl-card-meta">${[place, tongue, when].filter(Boolean).map(esc).join(" · ")}</p>
        ${text ? `<p class="bowl-card-flag">Text you can read</p>` : ""}
      </div></a></article>`;
  }

  /* Ways in: every content facet, counted, from the facts already loaded. */
  const BROWSE = [
    ["client", "People named"], ["ritual", "What they do"],
    ["biblical_intertexts", "Scripture quoted"], ["practitioner", "Hands and scribes"],
    ["visual", "What is drawn"], ["location", "Where they are"],
    ["language", "Language"], ["provenance", "Where they come from"],
  ];

  function facetCounts(group) {
    const tally = {};
    data.facts.filter(f => f.field_group === group).forEach(f => {
      const owner = data.clusterById[ownerOf(f.object_id)];
      if (!owner) return;
      f.value.replace(/^\[|\]$/g, "").split(/"\s*,\s*"|;\s*/).forEach(raw => {
        const value = raw.replace(/^"|"$/g, "").trim();
        if (!value) return;
        (tally[value] = tally[value] || new Set()).add(owner.identity_id);
      });
    });
    return Object.entries(tally).map(([value, ids]) => ({value, count: ids.size, ids: [...ids]}))
      .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value));
  }

  let ownerIndex = null;
  function ownerOf(objectId) {
    if (!ownerIndex) {
      ownerIndex = {};
      data.identity_clusters.forEach(c => c.members.forEach(m => { ownerIndex[m] = c.identity_id; }));
    }
    return ownerIndex[objectId];
  }

  function renderBrowse(view, group) {
    const label = (BROWSE.find(b => b[0] === group) || [group, group])[1];
    const rows = facetCounts(group);
    view.innerHTML = `<div class="reading-head">
        <a class="entry-back" href="#/reading">← Bowls worth reading</a>
        <h1 id="reading-title">${esc(label)}</h1>
        <p class="standfirst">${rows.length.toLocaleString()} distinct values across
          ${new Set(rows.flatMap(r => r.ids)).size.toLocaleString()} bowls.</p>
      </div>
      <ul class="facet-list">${rows.slice(0, 300).map(r => `<li>
        <a href="#/reading?${group}=${encodeURIComponent(r.value)}">
          <span>${esc(r.value)}</span><em>${r.count}</em></a></li>`).join("")}</ul>
      ${rows.length > 300 ? `<p class="entry-note">and ${rows.length - 300} more</p>` : ""}`;
  }

  function renderPublications(view) {
    const rows = data.publications;
    view.innerHTML = `<div class="reading-head">
        <a class="entry-back" href="#/reading">← Bowls worth reading</a>
        <h1 id="reading-title">Bowls by publication</h1>
        <p class="standfirst">Which edition publishes which bowl — the question the publication
          registry was built to answer. ${rows.filter(r => r.resolution === "resolved").length}
          of ${rows.length} designations resolve to a work in the library.</p>
      </div>
      <ul class="fact-list">${rows.map(r => {
        const source = r.source_id ? data.sourceById[r.source_id] : null;
        return `<li><span><a href="#/reading?publication=${encodeURIComponent(r.publication_key)}">${esc(r.publication_key)}</a>
          ${source ? `<small>${esc(source.title || "")}</small>` : `<em class="unresolved">${esc(r.resolution)}</em>`}</span>
          <cite>${r.objects} bowl${r.objects === 1 ? "" : "s"}</cite></li>`;
      }).join("")}</ul>`;
  }

  function renderIndex(view, query) {
    const params = new URLSearchParams(query || "");
    const term = (params.get("q") || "").trim().toLowerCase();
    const publication = params.get("publication");
    const facetGroup = BROWSE.map(b => b[0]).find(g => params.get(g));
    const facetValue = facetGroup ? params.get(facetGroup) : null;
    let pool = data.identity_clusters;
    let heading = "Bowls worth reading", note = "";
    if (publication) {
      const row = data.publications.find(p => p.publication_key === publication);
      const ids = new Set((row ? JSON.parse(row.object_ids) : []).map(ownerOf));
      pool = pool.filter(c => ids.has(c.identity_id));
      heading = publication; note = `Bowls published in ${publication}.`;
    } else if (facetValue) {
      const hit = facetCounts(facetGroup).find(f => f.value === facetValue);
      const ids = new Set(hit ? hit.ids : []);
      pool = pool.filter(c => ids.has(c.identity_id));
      heading = facetValue; note = `Bowls where ${facetGroup.replace(/_/g, " ")} is “${facetValue}”.`;
    } else if (term) {
      pool = pool.filter(c => term.split(/\s+/).every(word => c.haystack.includes(word)));
      heading = `“${term}”`; note = `${pool.length.toLocaleString()} bowls match.`;
    }
    const filtered = Boolean(term || facetValue || publication);
    const readable = pool
      .filter(c => filtered || c.reading_score >= 4)
      .sort((a, b) => b.reading_score - a.reading_score ||
        a.display_name.localeCompare(b.display_name));
    const thin = data.identity_clusters.length - readable.length;
    const m = data.manifest;
    view.innerHTML = `<div class="reading-head">
        ${filtered ? `<a class="entry-back" href="#/reading">← Bowls worth reading</a>` :
          `<span class="eyebrow">Late antique Mesopotamia, roughly 500–700 CE</span>`}
        <h1 id="reading-title">${esc(heading)}</h1>
        ${filtered ? "" : `<p class="standfirst">Ordinary clay vessels, inscribed in a spiral and buried upside
          down beneath the floors of houses in Sasanian Mesopotamia to keep something out.
          This index holds <strong>${data.identity_clusters.length.toLocaleString()}</strong>
          records of them. Measured against the field's own control list of published Jewish
          Babylonian Aramaic bowls, it cites <strong>115 of 115</strong> publications and has
          attached objects to almost none of them, so treat coverage as a reading list rather
          than a corpus.</p>`}
        ${note ? `<p class="standfirst">${esc(note)}</p>` : ""}
        ${filtered ? "" : `<p class="standfirst-note">${m.texts_included_rows} bowls have a text you can read here.
          ${m.texts_withheld_rows} more name the edition that prints theirs.
          No image is cleared for reuse yet, so every mark below is drawn from the object's own
          recorded line count.</p>`}
      </div>
      <form class="reading-search" id="reading-search-form" role="search">
        <input id="reading-search" type="search" name="q" value="${esc(term)}"
          placeholder="A name, a demon, a verse, a museum, a word in a text…"
          aria-label="Search the corpus" autocomplete="off">
      </form>
      ${filtered ? "" : `<nav class="browse-strip" aria-label="Browse by">
        ${BROWSE.map(([g, l]) => `<a href="#/reading/browse/${g}">${esc(l)}</a>`).join("")}
        <a href="#/reading/publications">By publication</a></nav>`}
      <div class="bowl-grid">${readable.map(card).join("")}</div>
      ${readable.length ? "" : `<p class="thin-note">Nothing matches. Try fewer words.</p>`}
      ${filtered ? "" : `<p class="thin-note"><a href="#/explore">${thin.toLocaleString()} further records</a>
        hold little beyond an identifier and a source. They are in the research explorer.</p>`}`;
    const form = view.querySelector("#reading-search-form");
    if (form) form.addEventListener("submit", event => {
      event.preventDefault();
      const value = view.querySelector("#reading-search").value.trim();
      location.hash = value ? `#/reading?q=${encodeURIComponent(value)}` : "#/reading";
    });
  }

  function factList(id, group, heading) {
    const rows = factsOf(id, group);
    if (!rows.length) return "";
    const grouped = new Map();
    rows.forEach(r => {
      const key = r.value;
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push(r);
    });
    const items = [...grouped].map(([value, reports]) => {
      const citations = reports.map(r => {
        const source = data.sourceById[r.source_id];
        const cite = source ? `${source.authors || source.title || ""} ${source.issued_year || ""}`.trim() : "";
        return [cite, r.locator].filter(Boolean).join(" · ");
      }).filter(Boolean);
      return `<li><span>${esc(value.replace(/^\["|"\]$/g, "").replace(/","/g, ", "))}</span>
        ${citations.length ? `<cite>${citations.map(esc).join("; ")}</cite>` : ""}</li>`;
    });
    return `<section class="entry-block"><h2>${esc(heading)}</h2><ul class="fact-list">${items.join("")}</ul></section>`;
  }

  function journeySection(id) {
    const rows = factsOf(id, "provenance");
    if (!rows.length) return "";
    const labels = {findspot: "Findspot", excavation_context: "Excavation context",
      origin: "Reported origin", findspot_or_origin: "Reported findspot or origin",
      collection_history: "Collection history", provenance: "Provenance report",
      provenance_summary: "Provenance report", production_place: "Production place",
      current_location: "Current collection", current_or_reported_collection: "Reported collection"};
    return `<section class="entry-block"><h2>Its journey</h2><ul class="fact-list">${rows.map(r => {
      const source = data.sourceById[r.source_id];
      const cite = source ? [source.authors || source.title, source.issued_year, r.locator].filter(Boolean).join(" · ") : r.locator;
      return `<li><span><small>${esc(labels[r.field] || r.field.replaceAll("_", " "))}</small>${esc(r.value)}</span>
        ${cite ? `<cite>${esc(cite)}</cite>` : ""}</li>`;
    }).join("")}</ul></section>`;
  }

  function sourcesSection(id) {
    const grouped = new Map();
    const add = (sourceId, locator, url) => {
      if (!sourceId) return;
      if (!grouped.has(sourceId)) grouped.set(sourceId, {locators: new Set(), url: ""});
      const item = grouped.get(sourceId);
      if (locator) item.locators.add(locator);
      if (url) item.url = url;
    };
    (data.factsBy[id] || []).forEach(r => add(r.source_id, r.locator));
    (data.textsBy[id] || []).forEach(r => add(r.source_id, r.access_locator, r.access_url));
    (data.editionsBy[id] || []).forEach(r => add(r.source_id, r.locator, r.access_url));
    (data.mediaBy[id] || []).forEach(r => add(r.source_id, "", r.url));
    if (!grouped.size) return "";
    return `<section class="entry-block"><h2>Sources</h2><ul class="source-groups">${[...grouped].map(([sourceId, item]) => {
      const source = data.sourceById[sourceId] || {};
      const label = source.citation || source.title || sourceId;
      const link = item.url ? `<a href="${esc(item.url)}" rel="noreferrer">${esc(label)}</a>` : esc(label);
      return `<li><span>${link}</span>${item.locators.size ? `<small>${[...item.locators].map(esc).join(" · ")}</small>` : ""}</li>`;
    }).join("")}</ul></section>`;
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
    const identifiers = data.identifiersBy[id] || [];
    const objects = cluster.members.map(m => data.objectById[m]).filter(Boolean);
    const cautions = [...new Set(objects.map(o => o.authenticity)
      .filter(value => ["suspected_fake", "disputed", "uncertain", "pseudo_script"].includes(value)))];
    const overview = summarise(cluster);

    view.innerHTML = `<article class="entry">
      <a class="entry-back" href="${esc(catalogueReturn())}">← Back to the collection</a>
      <header class="entry-head">
        <div class="entry-mark">${mark(cluster)}</div>
        <div>
          <h1 id="reading-title">${titleMarkup(cluster)}</h1>
          ${overview ? `<p class="entry-standfirst">${esc(overview)}</p>` : ""}
          <p class="entry-meta">${[cluster.display_date, cluster.display_language, cluster.display_collection]
            .filter(Boolean).map(esc).join(" · ")}</p>
          ${cautions.map(value => `<p class="entry-object-caution">${esc(value.replaceAll("_", " "))}</p>`).join("")}
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

      ${factList(id, "client", "People and purpose — who it names")}
      ${factList(id, "practitioner", "People and purpose — maker or hand, as reported")}
      ${factList(id, "target", "People and purpose — what it acts against")}
      ${factList(id, "ritual", "People and purpose — what it does")}
      ${factList(id, "biblical_intertexts", "People and purpose — scripture it quotes")}

      ${cluster.display_date === "Multiple proposed dates" ? factList(id, "dating", "Proposed dates") : ""}
      ${factList(id, "material", "The bowl — material")}
      ${factList(id, "dimensions", "The bowl — dimensions")}
      ${factList(id, "condition", "The bowl — condition")}
      ${factList(id, "script", "The bowl — script")}
      ${factList(id, "visual", "The bowl — what is drawn")}
      ${factList(id, "text_form", "The bowl — inscription layout")}

      ${editions.length ? `<section class="entry-block"><h2>Where it is published</h2>
        <ul class="fact-list">${editions.map(e => `<li><span>${esc(e.citation)}</span>
          <cite>${e.locator ? esc(e.locator) + " · " : ""}${e.access_url
            ? `<a href="${esc(e.access_url)}" rel="noreferrer">link</a>` : esc(e.access_status || "")}</cite></li>`).join("")}</ul>
      </section>` : ""}

      ${journeySection(id)}
      ${factsOf(id, "provenance").length ? `<p class="entry-caveat">A reported findspot is a report. Listing an object here says
        nothing about its ownership, export history, or authenticity.</p>` : ""}

      ${sourcesSection(id)}

      <section class="entry-block"><h2>Other names and catalogue numbers</h2>
        <ul class="alias-list">${[...new Set(rawLabels)].map(label => `<li>${esc(label)}</li>`).join("")}
        ${identifiers.map(item => `<li><span>${esc(item.scheme)}</span> ${/^IsIAO\b/i.test(item.value)
          ? `<abbr class="identifier-help" tabindex="0" title="Italian Institute for Africa and the Orient; a historical collection prefix.">${esc(item.value)}</abbr>`
          : esc(item.value)}</li>`).join("")}</ul>
      </section>

      <details class="entry-apparatus"><summary>Research details</summary>
        <dl>
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
    const hash = location.hash;
    const browse = hash.match(/^#\/reading\/browse\/([a-z_]+)/);
    const object = hash.match(/^#\/reading\/(IDENT-[^?]+)/);
    if (hash.startsWith("#/scholarship")) renderScholarship(view);
    else if (hash.startsWith("#/reading/publications")) renderPublications(view);
    else if (browse) renderBrowse(view, browse[1]);
    else if (object) renderObject(view, decodeURIComponent(object[1]));
    else renderIndex(view, hash.split("?")[1] || "");
    view.scrollTop = 0;
  }

  window.ReadingRoom = {render};
})();
