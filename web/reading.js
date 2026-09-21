/* The reading room — the tab labelled "Explore", routed at #/explore.
 *
 * The interface has two data providers with the same table shapes. The local
 * console serves Mike's on-device research projection; static Access and public
 * builds serve the rights-gated release projection. The manifest identifies the
 * tier, so a private row can never become readable in a static release merely
 * because this shared interface knows how to display it.
 *
 * A host page opts into the static build by setting, before this script loads:
 *   window.READER_BASE      where the projected tables live  (default /api/reader)
 *   window.READER_SUFFIX    file extension, if any           (default none)
 *   window.READER_STANDALONE  true when there is no console to link back to
 */
(function () {
  "use strict";
  const READER = String(window.READER_BASE || "/api/reader").replace(/\/+$/, "");
  const SUFFIX = String(window.READER_SUFFIX || "");
  const STANDALONE = Boolean(window.READER_STANDALONE);
  const source = name => `${READER}/${name}${SUFFIX}`;
  const TABLES = ["identity_clusters", "objects", "identifiers", "facts", "facets", "texts", "editions", "sources", "media",
    "works", "contributors", "scholarship_decades", "publications"];
  const data = {loaded: false};
  const privateResearch = () => data.manifest?.access_tier === "private_research";
  const readableText = row => row.content_status === "included"
    || (privateResearch() && row.content_status === "private_research");
  const esc = value => String(value === null || value === undefined ? "" : value)
    .replace(/[&<>"']/g, ch => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch]));

  async function load() {
    if (data.loaded) return data;
    const manifest = await fetch(source("manifest")).then(r => r.json());
    const fetched = await Promise.all(TABLES.map(name =>
      fetch(source(name)).then(r => r.json()).then(payload => [name, payload.rows])));
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
    data.facetsBy = bucket("facets");
    data.identifiersBy = bucket("identifiers");
    data.textsBy = bucket("texts");
    data.editionsBy = bucket("editions");
    data.mediaBy = bucket("media");
    data.sourceById = Object.fromEntries(data.sources.map(s => [s.id, s]));
    data.objectById = Object.fromEntries(data.objects.map(o => [o.id, o]));
    data.clusterById = Object.fromEntries(data.identity_clusters.map(c => [c.identity_id, c]));
    data.identity_clusters.forEach(c => {
      const facts = data.factsBy[c.identity_id] || [];
      const facets = data.facetsBy[c.identity_id] || [];
      const text = (data.textsBy[c.identity_id] || []).find(readableText);
      c.haystack = [c.display_name, ...(data.identifiersBy[c.identity_id] || []).flatMap(i => [i.scheme, i.value]),
        ...facts.map(f => f.value), ...facets.map(f => f.facet_label), text ? text.content : ""]
        .join(" ").toLowerCase();
    });
    data.loaded = true;
    return data;
  }

  const factsOf = (id, group) => (data.factsBy[id] || []).filter(f => f.field_group === group);
  const values = (id, group) => [...new Set(factsOf(id, group).map(f => f.value))];
  const first = (id, group) => values(id, group)[0] || "";

  function catalogueReturn() {
    const home = STANDALONE ? "#/explore" : "#/search";
    try {
      const saved = JSON.parse(sessionStorage.getItem("bowlam.catalogue.return") || "null");
      if (saved?.hash?.startsWith(home)) return saved.hash;
    } catch { /* use the collection root */ }
    return home;
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

  /* A Creative Commons deed asks for a link to itself, not just a name. Rows
     published on the open_license basis carry the source's own licence, which is
     narrower than this index's CC BY 4.0, so the credit line has to say which one
     governs the words or image above it. `license_url` may be null where a rights
     statement instead records public-domain status or another reviewed basis. */
  function licenceLink(item) {
    const url = (item.license_url || "").trim();
    if (!url) return "";
    const cc = url.match(/creativecommons\.org\/licenses\/([a-z-]+)\/([\d.]+)/i);
    const label = cc ? `CC ${cc[1].toUpperCase()} ${cc[2]}` : "Licence";
    return ` · <a href="${esc(url)}" rel="license noreferrer">${esc(label)}</a>`;
  }

  function textTerms(item) {
    if (item.content_status === "private_research") {
      return ` · <span class="private-access-note">Private research copy · not cleared for redistribution</span>`;
    }
    return licenceLink(item);
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

  function embeddableImage(url) {
    const clean = String(url || "").split(/[?#]/)[0];
    return clean.startsWith("/api/private-media/")
      || /\.(?:avif|gif|jpe?g|png|webp)$/i.test(clean);
  }

  function mediaSourceLink(image) {
    const sourceRow = data.sourceById?.[image.source_id] || {};
    const editionRow = (data.editions || []).find(row => row.source_id === image.source_id);
    const url = sourceRow.url || editionRow?.access_url || image.url;
    return url ? `<a class="media-source" href="${esc(url)}" rel="noreferrer">Open image source</a>` : "";
  }

  /* Release projections emit approved images only. The on-device projection may
     also emit private research links, identified by their explicit rights note. */
  function mark(cluster, includeSourceLink = true) {
    const image = (data.mediaBy[cluster.identity_id] || [])
      .find(m => m.media_type === "image" && m.url);
    if (!image) return spiral(cluster);
    const sourceLink = includeSourceLink ? mediaSourceLink(image) : "";
    if (!embeddableImage(image.url)) {
      return `<span class="bowl-media is-reference">${spiral(cluster)}${sourceLink}</span>`;
    }
    const privateOnly = privateResearch()
      && String(image.rights_statement || "").startsWith("Private research view only;");
    const rights = privateOnly ? "private research view"
      : image.rights_status === "public_domain" ? "public domain"
      : image.rights_status === "open_license" ? "open licence" : "reviewed reuse";
    return `<span class="bowl-media"><img class="bowl-image" src="${esc(image.url)}"
      alt="${esc(cluster.display_name)}" loading="lazy" decoding="async">
      <span class="media-fallback">${spiral(cluster)}</span>${image.attribution
        ? `<span class="bowl-credit">${esc(image.attribution)} · ${esc(rights)}${licenceLink(image)}</span>` : ""}
      ${sourceLink}</span>`;
  }

  function bindMediaFallbacks(root) {
    root.querySelectorAll(".bowl-media img.bowl-image").forEach(img => {
      const fail = () => img.closest(".bowl-media")?.classList.add("is-broken");
      img.addEventListener("error", fail, {once: true});
      if (img.complete && !img.naturalWidth) fail();
    });
  }

  /* The index's own one-line description of what a bowl's text does, written
     from the edition and published as an own_work summary row. It is marked by
     its editor so it never renders as the bowl's text further down the page. */
  const CARD_LINE_EDITOR = "Incantation Bowl Index card line";
  const cardLine = id => ((data.textsBy[id] || [])
    .find(t => t.editor === CARD_LINE_EDITOR && readableText(t)) || {}).content || "";

  /* Falling back to the claims, choose by field, not by length. The shortest
     ritual value used to win, which put an installation instruction — "Exterior
     directs placement 'for the inner room of the hall'" — at the top of the
     reading room ahead of that bowl's actual purpose. Within the winning field
     the shortest value is still the better card text: the long ones are hedged
     discussion rather than a statement of what the bowl does. */
  const PURPOSE_FIELDS = ["text_purpose", "text_function", "formula_genre",
    "named_demon", "named_angels", "text_tradition"];

  function composedPurpose(id) {
    const rows = factsOf(id, "ritual");
    for (const field of PURPOSE_FIELDS) {
      const found = [...new Set(rows.filter(r => r.field === field).map(r => r.value))];
      if (found.length) return found.sort((a, b) => a.length - b.length)[0];
    }
    return "";
  }

  /* A bowl is recognised by whom it names, so keep the first name whole rather
     than truncating a list of them mid-patronymic. */
  function principalClient(id) {
    const value = values(id, "client")[0] || "";
    const parts = value.split(/\s*[;·]\s*/).map(part => part.trim()).filter(Boolean);
    return parts.length > 1 ? `${parts[0]} and others` : value;
  }

  /* Budget the two halves separately. Clipping the joined string dropped the
     client first, which is exactly the half worth keeping. */
  function purposeAndClient(purpose, client, limit) {
    if (!limit) return `${purpose} — for ${client}`;
    const tail = ` — for ${clip(client, 34)}`;
    return clip(purpose, Math.max(24, limit - tail.length)) + tail;
  }

  function summarise(cluster, limit) {
    const id = cluster.identity_id;
    const written = cardLine(id);
    if (written) return limit ? clip(written, limit) : written;
    const purpose = composedPurpose(id);
    const client = principalClient(id);
    if (purpose && client) return purposeAndClient(purpose, client, limit);
    let line = "";
    if (purpose) line = purpose;
    else if (client) line = `Named for ${client}`;
    else {
      const verses = values(id, "biblical_intertexts");
      if (verses.length) line = `Quotes ${verses.slice(0, 3).join(", ").replace(/[[\]"]/g, "")}`;
    }
    return limit ? clip(line, limit) : line;
  }

  const ORIGINAL_TEXT_TYPES = new Set(["inscription", "transcription", "transliteration", "incipit"]);

  function textCredit(item) {
    return `<p class="entry-credit">${esc(credit(item))}${textTerms(item)}</p>`;
  }

  function originalText(item) {
    const rtl = item.script && item.script !== "Latin";
    return `<div class="original-reading"><h3>${esc(item.text_type)}${item.language
      ? " · " + esc(item.language) : ""}</h3>
      <blockquote class="original-text" dir="${rtl ? "rtl" : "auto"}"
        lang="${rtl ? "arc" : ""}">${esc(item.content)}</blockquote>${textCredit(item)}</div>`;
  }

  function textSections(rows) {
    const translations = rows.filter(item => item.text_type === "translation");
    const originals = rows.filter(item => ORIGINAL_TEXT_TYPES.has(item.text_type));
    const summaries = rows.filter(item => item.text_type === "summary");
    const other = rows.filter(item => item.text_type !== "translation"
      && item.text_type !== "summary" && !ORIGINAL_TEXT_TYPES.has(item.text_type));
    const sections = translations.map(item => `<section class="entry-block entry-text">
      <h2>Translation${item.language && item.language !== "English" ? " · " + esc(item.language) : ""}</h2>
      <blockquote dir="auto" lang="${item.language === "English" ? "en" : ""}">${esc(item.content)}</blockquote>
      ${textCredit(item)}</section>`);
    if (originals.length) sections.push(`<details class="entry-block entry-original">
      <summary>Show original incantation</summary>${originals.map(originalText).join("")}</details>`);
    if (summaries.length) {
      const body = summaries.map(item => `<blockquote>${esc(item.content)}</blockquote>${textCredit(item)}`).join("");
      sections.push(translations.length
        ? `<details class="entry-block entry-summary"><summary>Research summary</summary>${body}</details>`
        : `<section class="entry-block entry-text"><h2>What it says</h2>${body}</section>`);
    }
    sections.push(...other.map(item => `<section class="entry-block entry-text">
      <h2>${esc(item.text_type)}</h2><blockquote>${esc(item.content)}</blockquote>${textCredit(item)}</section>`));
    return sections.join("");
  }

  function card(cluster) {
    const id = cluster.identity_id;
    const text = (data.textsBy[id] || []).find(readableText);
    const line = summarise(cluster, 96);
    const place = cluster.display_collection;
    const tongue = cluster.display_language;
    const when = cluster.display_date;
    return `<article class="bowl-card"><a href="#/explore/${encodeURIComponent(id)}">
      <div class="bowl-card-mark">${mark(cluster, false)}</div>
      <div class="bowl-card-body">
        <h3>${titleMarkup(cluster)}</h3>
        ${line ? `<p class="bowl-card-line">${esc(line)}</p>` : ""}
        <p class="bowl-card-meta">${[place, tongue, when].filter(Boolean).map(esc).join(" · ")}</p>
        ${text ? `<p class="bowl-card-flag">Text you can read</p>` : ""}
      </div></a></article>`;
  }

  /* Ways in. Noisy categorical vocabularies use project-authored controlled
     labels; names, hands and concise visual descriptions remain source terms. */
  const BROWSE = [
    ["ritual", "What they do"], ["client", "People named"],
    ["visual", "What is drawn"], ["biblical_intertexts", "Scripture quoted"],
    ["language", "Language"], ["provenance", "Where they come from"],
    ["location", "Where they are"], ["practitioner", "Hands and scribes"],
  ];

  /* The homepage's coverage links arrive as ?present=<facet>. Most facets are
     fact groups and answer from `facts`, but a text edition and an image are
     not: they live in their own tables. `media` is empty in the gated
     projection, so an image link finds nothing here rather than quietly
     matching every bowl — the honest answer until a rights decision lands. */
  const PRESENT = {
    text_edition: id => (data.textsBy[id] || []).length > 0 || (data.editionsBy[id] || []).length > 0,
    image: id => (data.mediaBy[id] || []).length > 0,
  };
  const PRESENT_LABELS = {
    text_edition: ["Bowls you can trace to an edition", "Bowls this index can point to a published reading of."],
    provenance: ["Bowls with a recorded journey", "Bowls with an account of where they were found or held."],
    image: ["Bowls with a published image", "Bowls whose image references have cleared a rights decision."],
  };
  const hasPresent = (id, facet) =>
    (PRESENT[facet] || (identity => factsOf(identity, facet).length > 0))(id);

  const CONTROLLED_FACETS = new Set([
    "ritual", "biblical_intertexts", "location", "language", "provenance",
  ]);
  const ALPHABETICAL_FACETS = new Set(["client", "practitioner"]);
  const SCRIPTURE_BOOK_ORDER = ["Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg",
    "Ruth", "1 Sam", "2 Sam", "1 Kgs", "2 Kgs", "1 Chron", "2 Chron", "Ezra", "Neh",
    "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan",
    "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag",
    "Zech", "Mal", "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1 Cor", "2 Cor",
    "Gal", "Eph", "Phil", "Col", "1 Thess", "2 Thess", "1 Tim", "2 Tim", "Titus",
    "Phlm", "Heb", "Jas", "1 Pet", "2 Pet", "1 John", "2 John", "3 John", "Jude", "Rev"];
  function scriptureOrder(value) {
    const match = value.match(/^(.*)\s+(\d+):(\d+)/);
    if (!match) return [999, 999, 999, value];
    const book = SCRIPTURE_BOOK_ORDER.indexOf(match[1]);
    return [book < 0 ? 998 : book, Number(match[2]), Number(match[3]), value];
  }
  function compareTuple(a, b) {
    for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
      if (typeof a[i] === "string" || typeof b[i] === "string") {
        const compared = String(a[i] || "").localeCompare(String(b[i] || ""));
        if (compared) return compared;
      } else if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) - (b[i] || 0);
    }
    return 0;
  }

  function facetCounts(group) {
    const tally = {};
    const rows = CONTROLLED_FACETS.has(group)
      ? data.facets.filter(f => f.facet_group === group).map(f => ({...f, value: f.facet_label}))
      : data.facts.filter(f => f.field_group === group);
    rows.forEach(f => {
      const owner = data.clusterById[ownerOf(f.object_id)];
      if (!owner) return;
      f.value.replace(/^\[|\]$/g, "").split(/"\s*,\s*"|;\s*/).forEach(raw => {
        const value = raw.replace(/^"|"$/g, "").trim();
        if (!value) return;
        (tally[value] = tally[value] || new Set()).add(owner.identity_id);
      });
    });
    const result = Object.entries(tally).map(([value, ids]) => ({value, count: ids.size, ids: [...ids]}));
    if (group === "biblical_intertexts") {
      return result.sort((a, b) => compareTuple(scriptureOrder(a.value), scriptureOrder(b.value)));
    }
    if (ALPHABETICAL_FACETS.has(group)) return result.sort((a, b) => a.value.localeCompare(b.value));
    return result.sort((a, b) => b.count - a.count || a.value.localeCompare(b.value));
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
        <a class="entry-back" href="#/explore">← Bowls worth reading</a>
        <h1 id="explore-title">${esc(label)}</h1>
        <p class="standfirst">${rows.length.toLocaleString()} distinct values across
          ${new Set(rows.flatMap(r => r.ids)).size.toLocaleString()} bowls.</p>
      </div>
      <ul class="facet-list">${rows.slice(0, 300).map(r => `<li>
        <a href="#/explore?${group}=${encodeURIComponent(r.value)}">
          <span>${esc(r.value)}</span><em>${r.count}</em></a></li>`).join("")}</ul>
      ${rows.length > 300 ? `<p class="entry-note">and ${rows.length - 300} more</p>` : ""}`;
  }

  function renderPublications(view) {
    const rows = data.publications;
    view.innerHTML = `<div class="reading-head">
        <a class="entry-back" href="#/explore">← Bowls worth reading</a>
        <h1 id="explore-title">Bowls by publication</h1>
        <p class="standfirst">Which edition publishes which bowl — the question the publication
          registry was built to answer. ${rows.filter(r => r.resolution === "resolved").length}
          of ${rows.length} designations resolve to a work in the library.</p>
      </div>
      <ul class="fact-list">${rows.map(r => {
        const source = r.source_id ? data.sourceById[r.source_id] : null;
        return `<li><span><a href="#/explore?publication=${encodeURIComponent(r.publication_key)}">${esc(r.publication_key)}</a>
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
    const present = params.get("present");
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
    } else if (present) {
      pool = pool.filter(c => hasPresent(c.identity_id, present));
      const [label, description] = PRESENT_LABELS[present]
        || [present.replace(/_/g, " "), `Bowls with ${present.replace(/_/g, " ")} recorded.`];
      heading = label;
      note = pool.length
        ? `${description} ${pool.length.toLocaleString()} in the index.`
        : `${description} None has cleared that gate yet.`;
    } else if (term) {
      pool = pool.filter(c => term.split(/\s+/).every(word => c.haystack.includes(word)));
      heading = `“${term}”`; note = `${pool.length.toLocaleString()} bowls match.`;
    }
    const filtered = Boolean(term || facetValue || publication || present);
    /* At equal score, a bowl that can say what it does comes first: ties used to
       fall to the alphabet, which parked six blank Isbell cards near the top. */
    const described = c => (summarise(c) ? 1 : 0);
    const readable = pool
      .filter(c => filtered || c.reading_score >= 4)
      .sort((a, b) => b.reading_score - a.reading_score ||
        described(b) - described(a) ||
        a.display_name.localeCompare(b.display_name));
    const thin = data.identity_clusters.length - readable.length;
    const m = data.manifest;
    const resolvedPublications = data.publications.filter(row => row.resolution === "resolved");
    const publicationObjects = new Set();
    const publicationIdentities = new Set();
    resolvedPublications.forEach(row => {
      JSON.parse(row.object_ids || "[]").forEach(objectId => {
        publicationObjects.add(objectId);
        publicationIdentities.add(ownerOf(objectId));
      });
    });
    // Card lines are counted with the descriptions, not with the texts: the
    // sentence below is about how much of the corpus a visitor can read.
    const readableTexts = data.texts.filter(row => readableText(row)
      && row.editor !== CARD_LINE_EDITOR);
    const readableTranslations = readableTexts.filter(row => row.text_type === "translation").length;
    const readableSummaries = readableTexts.filter(row => row.text_type === "summary").length;
    const privateTexts = readableTexts.filter(row => row.content_status === "private_research");
    const privateTranslations = privateTexts.filter(row => row.text_type === "translation").length;
    const privateSummaries = privateTexts.filter(row => row.text_type === "summary").length;
    const localTier = privateResearch();
    view.innerHTML = `<div class="reading-head">
        ${filtered ? `<a class="entry-back" href="#/explore">← Bowls worth reading</a>` :
          `<span class="eyebrow">Late antique Mesopotamia, roughly 500–700 CE</span>`}
        <h1 id="explore-title">${esc(heading)}</h1>
        ${filtered ? "" : `<p class="standfirst">Explore incantation bowls through what their
          texts do, the people they name, their languages, imagery, histories and publications.</p>
          <dl class="reading-stats">
            <div><dt>Bowls</dt><dd>${data.identity_clusters.length.toLocaleString()}</dd></div>
            <div><dt>Linked editions</dt><dd>${resolvedPublications.length.toLocaleString()}</dd></div>
            <div><dt>Readable texts</dt><dd>${readableTexts.length.toLocaleString()}</dd></div>
            <div><dt>Images</dt><dd>${(localTier ? m.media_available_rows : m.media_approved_rows).toLocaleString()}</dd></div>
          </dl>`}
        ${note ? `<p class="standfirst">${esc(note)}</p>` : ""}
        ${filtered ? "" : localTier ? `<p class="standfirst-note private-reading-notice">This is Mike's
          on-device research bank. Availability here is not permission to publish, redistribute,
          or share a text or image.</p>
          <details class="about-preview"><summary>About this private reader and its coverage</summary>
            <p><strong>${readableTranslations}</strong> translations and
              <strong>${readableSummaries}</strong> research summaries are readable here, along with
              <strong>${data.texts.filter(row => row.editor === CARD_LINE_EDITOR).length}</strong>
              project-authored card descriptions. Of those research texts,
              <strong>${privateTranslations}</strong> translations and
              <strong>${privateSummaries}</strong> summaries are private-only.</p>
            <p>All <strong>${m.media_available_rows}</strong> recorded image links are available;
              <strong>${m.media_private_rows}</strong> are private-only because no public reuse
              approval is recorded. Publication links connect ${publicationObjects.size.toLocaleString()}
              candidate records to ${publicationIdentities.size.toLocaleString()} bowl identities.</p>
          </details>` : `<p class="standfirst-note">Reuse terms appear with each included text
          or image. When modern wording cannot be shown, its citation and locator remain available.</p>
          <details class="about-preview"><summary>About this preview and its coverage</summary>
            <p><strong>${readableTranslations}</strong> public-domain translations and
              <strong>${readableSummaries}</strong> project-authored summaries are readable here;
              <strong>${m.texts_withheld_rows}</strong> text records point to an edition without
              reproducing protected wording.</p>
            <p>Publication links connect ${publicationObjects.size.toLocaleString()} candidate
              records to ${publicationIdentities.size.toLocaleString()} bowl identities. Images
              appear only when their recorded reuse decision and attribution pass the release gate;
              otherwise the interface draws a diagram from the recorded line count.</p>
          </details>`}
      </div>
      <form class="reading-search" id="reading-search-form" role="search">
        <input id="reading-search" type="search" name="q" value="${esc(term)}"
          placeholder="A name, a demon, a verse, a museum, a word in a text…"
          aria-label="Search the corpus" autocomplete="off">
      </form>
      ${filtered ? "" : `<nav class="browse-strip" aria-label="Browse by">
        ${BROWSE.map(([g, l]) => `<a href="#/explore/browse/${g}">${esc(l)}</a>`).join("")}
        <a href="#/explore/publications">By publication</a></nav>`}
      <div class="bowl-grid">${readable.map(card).join("")}</div>
      ${readable.length ? "" : `<p class="thin-note">${term
        ? "Nothing matches. Try fewer words."
        : "Nothing here yet. The note above says why."}</p>`}
      ${filtered ? "" : `<p class="thin-note">${STANDALONE
        ? `A further ${thin.toLocaleString()} records hold little beyond an identifier and a
           source, and are not shown here.`
        : `<a href="#/search">${thin.toLocaleString()} further records</a> hold little beyond an
           identifier and a source. They are in the research explorer.`}</p>`}`;
    const form = view.querySelector("#reading-search-form");
    if (form) form.addEventListener("submit", event => {
      event.preventDefault();
      const value = view.querySelector("#reading-search").value.trim();
      location.hash = value ? `#/explore?q=${encodeURIComponent(value)}` : "#/explore";
    });
  }

  const tidy = value => String(value || "").trim().replace(/\s+/g, " ");
  function dateValue(value) {
    const display = tidy(value).replaceAll("-", "–")
      .replace(/^(?:about\s+the|about|circa|ca\.)\s+/i, "c. ");
    const calendar = /\d|\bcentur(?:y|ies)\b|\b(?:CE|BCE|AD|BC)\b/i.test(display);
    return {key: `${calendar ? "date" : "period"}:${display.replace(/^c\.\s+/i, "").toLowerCase()}`,
      display, calendar};
  }

  function measurementValue(value) {
    const text = tidy(value);
    const found = new Map();
    const add = (role, amount, unit) => {
      role = role.toLowerCase().replace(/^opening\s+/, "");
      const millimetres = Number(amount) * (unit.toLowerCase() === "cm" ? 10 : 1);
      const prior = found.get(role);
      if (prior !== undefined && Math.abs(prior - millimetres) > .0001) return false;
      found.set(role, millimetres);
      return true;
    };
    const patterns = [
      /(opening diameter|diameter|height|depth)\s*(\d+(?:\.\d+)?)\s*(cm|mm)\b/gi,
      /(\d+(?:\.\d+)?)\s*(cm|mm)\s*(opening diameter|diameter|height|depth)\b/gi,
    ];
    let valid = true;
    for (const [index, pattern] of patterns.entries()) {
      for (const match of text.matchAll(pattern)) {
        valid = index === 0 ? add(match[1], match[2], match[3]) && valid
          : add(match[3], match[1], match[2]) && valid;
      }
    }
    if (!valid || found.size < 2) return null;
    const order = ["diameter", "height", "depth"];
    const roles = [...found].sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0]));
    const number = mm => Number((mm / 10).toFixed(3)).toString();
    return {
      key: "measure:" + [...found].sort().map(([role, mm]) => `${role}:${mm.toFixed(3)}`).join("|"),
      display: roles.map(([role, mm]) => `${role[0].toUpperCase() + role.slice(1)} ${number(mm)} cm`).join(" · "),
    };
  }

  function factPresentation(row, group) {
    if (group === "dating") return dateValue(row.value);
    if (group === "dimensions") {
      const measurement = measurementValue(row.value);
      if (measurement) return measurement;
    }
    const display = tidy(row.value).replace(/^\["|"\]$/g, "").replace(/","/g, ", ");
    return {key: `text:${display.toLowerCase()}`, display};
  }

  function groupedFacts(id, group) {
    const grouped = new Map();
    factsOf(id, group).forEach(row => {
      const presentation = factPresentation(row, group);
      if (!grouped.has(presentation.key)) grouped.set(presentation.key, {
        ...presentation, reports: [], variants: new Set(), approximate: false,
      });
      const item = grouped.get(presentation.key);
      item.reports.push(row);
      item.variants.add(tidy(row.recorded_value || row.value));
      if (group === "dating" && /^c\.\s+/i.test(presentation.display)) item.approximate = true;
    });
    for (const item of grouped.values()) {
      if (item.approximate) item.display = `c. ${item.display.replace(/^c\.\s+/i, "")}`;
    }
    return [...grouped.values()];
  }

  function canonicalLocator(value) {
    return tidy(value).toLowerCase().replace(/\bbowl\b/g, "").replace(/[;,·]/g, " ")
      .replace(/\s+/g, " ").trim();
  }

  function citationsFor(reports) {
    const unique = new Map();
    reports.forEach(row => {
      const key = `${row.source_id || ""}|${canonicalLocator(row.locator)}`;
      const prior = unique.get(key);
      if (!prior || tidy(row.locator).length > tidy(prior.locator).length) unique.set(key, row);
    });
    return [...unique.values()].map(row => {
      const source = data.sourceById[row.source_id];
      const cite = source ? `${source.authors || source.title || ""} ${source.issued_year || ""}`.trim() : "";
      return [cite, row.locator].filter(Boolean).join(" · ");
    }).filter(Boolean);
  }

  function distinctLocators(rows) {
    const unique = new Map();
    rows.forEach(row => {
      if (!row.locator) return;
      const key = canonicalLocator(row.locator);
      const prior = unique.get(key);
      if (!prior || tidy(row.locator).length > tidy(prior).length) unique.set(key, row.locator);
    });
    return [...unique.values()];
  }

  function groupedEditions(rows) {
    const grouped = new Map();
    rows.forEach(row => {
      const key = [row.source_id, row.citation, row.access_url].map(tidy).join("|");
      if (!grouped.has(key)) grouped.set(key, {...row, rows: []});
      grouped.get(key).rows.push(row);
    });
    return [...grouped.values()].map(item => ({...item, locators: distinctLocators(item.rows)}));
  }

  function factItems(id, group, showVariants = false) {
    return groupedFacts(id, group).map(item => {
      const citations = citationsFor(item.reports);
      const variants = [...item.variants].filter(Boolean);
      return `<li><span>${item.key.startsWith("period:") ? "<small>Period</small>" : ""}${esc(item.display)}</span>
        ${citations.length ? `<cite>${citations.map(esc).join("; ")}</cite>` : ""}
        ${showVariants && variants.length > 1 ? `<details class="recorded-forms"><summary>Recorded forms</summary><ul>${variants.map(value => `<li>${esc(value)}</li>`).join("")}</ul></details>` : ""}</li>`;
    }).join("");
  }

  function factList(id, group, heading, showVariants = false) {
    if (!factsOf(id, group).length) return "";
    return `<section class="entry-block"><h2>${esc(heading)}</h2><ul class="fact-list">${factItems(id, group, showVariants)}</ul></section>`;
  }

  function datingEvidence(id) {
    const groups = groupedFacts(id, "dating");
    const dates = groups.filter(item => !item.key.startsWith("period:"));
    const periods = groups.filter(item => item.key.startsWith("period:"));
    if (dates.length <= 1 && !periods.length) return "";
    return `<section class="entry-block"><h2>${dates.length > 1 ? "Proposed dates" : "Dating evidence"}</h2>
      <ul class="fact-list">${factItems(id, "dating")}</ul></section>`;
  }

  function recordedFormsSection(id) {
    const groups = [...new Set((data.factsBy[id] || []).map(row => row.field_group))];
    const items = groups.flatMap(group => groupedFacts(id, group)
      .filter(item => item.variants.size > 1)
      .map(item => ({group, ...item})));
    if (!items.length) return "";
    return `<section class="entry-block recorded-source-forms"><h2>Recorded source forms</h2>
      <p class="entry-note">Equivalent wording is combined in the main display; the forms recorded by the sources remain here.</p>
      <ul class="fact-list">${items.map(item => `<li><span><small>${esc(item.group.replaceAll("_", " "))}</small>${esc(item.display)}</span>
        <cite>${citationsFor(item.reports).map(esc).join("; ")}</cite>
        <details class="recorded-forms" open><summary>Recorded forms</summary><ul>${[...item.variants].map(value => `<li>${esc(value)}</li>`).join("")}</ul></details></li>`).join("")}</ul></section>`;
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
      if (!grouped.has(sourceId)) grouped.set(sourceId, {locators: new Map(), url: ""});
      const item = grouped.get(sourceId);
      if (locator) {
        const key = canonicalLocator(locator);
        const prior = item.locators.get(key);
        if (!prior || tidy(locator).length > tidy(prior).length) item.locators.set(key, locator);
      }
      // Text and edition access links are added before media. A local private
      // image derivative is useful to display, but must not replace the
      // publication link in the bibliography.
      if (url && !item.url) item.url = url;
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
      return `<li><span>${link}</span>${item.locators.size ? `<small>${[...item.locators.values()].map(esc).join(" · ")}</small>` : ""}</li>`;
    }).join("")}</ul></section>`;
  }

  function identifierRank(scheme) {
    const value = scheme.toLowerCase();
    if (/accession|museum number|collection designation|registration number|penn catalogue/.test(value)) return 0;
    if (/publication designation|text number|table designation|bibliographic concordance/.test(value)) return 1;
    if (/key|record|uuid|asset|dataset|url|platform|product id/.test(value)) return 3;
    return 2;
  }

  function publicationKeyParts(item) {
    if (item.scheme !== "publication object key" || !tidy(item.value).includes("::")) return null;
    return tidy(item.value).split("::", 2).map(tidy);
  }

  function identifierValue(item, full = false) {
    const value = tidy(item.value);
    const publication = publicationKeyParts(item);
    if (publication) return full ? `${publication[0]} — ${publication[1]}` : publication[1];
    return value;
  }

  function identifierValueMarkup(item, full = false) {
    const value = identifierValue(item, full);
    return /^IsIAO\b/i.test(value)
      ? `<abbr class="identifier-help" tabindex="0" title="Italian Institute for Africa and the Orient; a historical collection prefix.">${esc(value)}</abbr>`
      : esc(value);
  }

  function groupedIdentifiers(identifiers) {
    const grouped = new Map();
    identifiers.forEach(item => {
      const key = identifierValue(item).toLowerCase();
      if (!grouped.has(key)) grouped.set(key, {value: identifierValue(item), rows: []});
      grouped.get(key).rows.push(item);
    });
    return [...grouped.values()].map(group => {
      const rows = [...new Map(group.rows.map(row => [
        `${row.scheme}|${row.value}|${row.assigning_body || ""}`, row,
      ])).values()];
      return {...group, rows, rank: Math.min(...rows.map(row => identifierRank(row.scheme)))};
    }).sort((a, b) => a.rank - b.rank || identifierValue(a.rows[0]).localeCompare(identifierValue(b.rows[0])));
  }

  function identifiersSection(rawLabels, identifiers, displayName) {
    const groups = groupedIdentifiers(identifiers);
    const identifierValues = groups.map(group => group.value.toLowerCase());
    const labels = [...new Set(rawLabels)].filter(label => {
      const normalized = tidy(label).toLowerCase();
      return normalized !== tidy(displayName).toLowerCase()
        && !identifierValues.some(value => value.length > 2 && normalized.includes(value));
    });
    if (!groups.length && !labels.length) return "";
    const rows = groups.map(group => {
      const schemes = [...new Set(group.rows.map(row => {
        const publication = publicationKeyParts(row);
        return publication ? `published in ${publication[0]}` : row.scheme;
      }))]
        .sort((a, b) => identifierRank(a) - identifierRank(b) || a.localeCompare(b));
      return `<li><span>${schemes.map(esc).join(" · ")}</span> ${identifierValueMarkup(group.rows[0])}</li>`;
    });
    if (labels.length) rows.push(...labels.map(label => `<li><span>Also recorded as</span> ${esc(label)}</li>`));
    return `<section class="entry-block"><h2>Names and identifiers</h2><ul class="alias-list">${rows.join("")}</ul></section>`;
  }

  function identifierDetails(identifiers, rawLabels = []) {
    const groups = groupedIdentifiers(identifiers);
    if (!groups.length && !rawLabels.length) return "";
    return `<section class="entry-block identifier-details"><h2>Identifier details</h2>
      <ul class="fact-list">${groups.flatMap(group => {
        const byScheme = new Map();
        group.rows.forEach(row => {
          const key = `${row.scheme}|${row.value}`;
          if (!byScheme.has(key)) byScheme.set(key, {row, bodies: new Set()});
          if (row.assigning_body) byScheme.get(key).bodies.add(row.assigning_body);
        });
        return [...byScheme.values()].map(({row, bodies}) => `<li><span><small>${esc(row.scheme)}</small>${identifierValueMarkup(row, true)}</span>
          ${bodies.size ? `<cite>Assigned by ${[...bodies].map(esc).join("; ")}</cite>` : ""}</li>`);
      }).join("")}
        ${[...new Set(rawLabels)].map(label => `<li><span><small>source record label</small>${esc(label)}</span></li>`).join("")}
      </ul></section>`;
  }

  function renderObject(view, identityId) {
    const cluster = data.clusterById[identityId];
    if (!cluster) { view.innerHTML = `<p class="dossier-loading">No such record.</p>`; return; }
    const id = cluster.identity_id;
    const texts = data.textsBy[id] || [];
    // The card line is our own description, not a text of the bowl; it leads the
    // page as the standfirst and must not appear among its editions below.
    const bowlTexts = texts.filter(t => t.editor !== CARD_LINE_EDITOR);
    const readable = bowlTexts.filter(readableText);
    const withheld = bowlTexts.filter(t => !readableText(t));
    const editions = groupedEditions(data.editionsBy[id] || []);
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
          <h1 id="explore-title">${titleMarkup(cluster)}</h1>
          ${overview ? `<p class="entry-standfirst">${esc(overview)}</p>` : ""}
          <p class="entry-meta">${[cluster.display_date, cluster.display_language, cluster.display_collection]
            .filter(Boolean).map(esc).join(" · ")}</p>
          ${cautions.map(value => `<p class="entry-object-caution">${esc(value.replaceAll("_", " "))}</p>`).join("")}
        </div>
      </header>

      ${textSections(readable)}

      ${withheld.length ? `<section class="entry-block">
        <h2>${readable.length ? "Further texts" : "What it says"}</h2>
        <p class="entry-note">Printed in the edition below rather than reproduced here.</p>
        <ul class="fact-list">${withheld.map(t => `<li><span>${esc(t.text_type)}${t.language ? " · " + esc(t.language) : ""}</span>
          <cite>${t.access_url ? `<a href="${esc(t.access_url)}" rel="noreferrer">${esc(t.access_citation || "edition")}</a>`
            : esc(t.access_citation || "edition")}${t.access_locator ? " · " + esc(t.access_locator) : ""}</cite></li>`).join("")}</ul>
      </section>` : ""}

      ${datingEvidence(id)}
      ${factList(id, "material", "The bowl — material")}
      ${factList(id, "dimensions", "The bowl — dimensions")}
      ${factList(id, "condition", "The bowl — condition")}
      ${factList(id, "script", "The bowl — script")}
      ${factList(id, "visual", "The bowl — what is drawn")}
      ${factList(id, "text_form", "The bowl — inscription layout")}

      ${editions.length ? `<section class="entry-block"><h2>Where it is published</h2>
        <ul class="fact-list">${editions.map(e => `<li><span>${esc(e.citation)}</span>
          <cite>${e.locators.length ? e.locators.map(esc).join(" · ") + " · " : ""}${e.access_url
            ? `<a href="${esc(e.access_url)}" rel="noreferrer">link</a>` : esc(e.access_status || "")}</cite></li>`).join("")}</ul>
      </section>` : ""}

      ${journeySection(id)}
      ${factsOf(id, "provenance").length ? `<p class="entry-caveat">A reported findspot is a report. Listing an object here says
        nothing about its ownership, export history, or authenticity.</p>` : ""}

      ${sourcesSection(id)}

      ${identifiersSection(rawLabels, identifiers, cluster.display_name)}

      <details class="entry-apparatus"><summary>Research details</summary>
        ${recordedFormsSection(id)}
        ${identifierDetails(identifiers, rawLabels)}
        ${factList(id, "client", "Who it names")}
        ${factList(id, "practitioner", "Maker or hand, as reported")}
        ${factList(id, "target", "What it acts against")}
        ${factList(id, "ritual", "What it does")}
        ${factList(id, "biblical_intertexts", "Scripture it quotes")}
        <dl>
          <dt>Identity</dt><dd><code>${esc(cluster.identity_id)}</code>
            · ${esc(cluster.record_status)} · ${cluster.member_count} linked record(s)</dd>
          <dt>Evidence</dt><dd>${cluster.source_count} source(s), ${cluster.appearance_count} appearance(s)</dd>
          <dt>Coverage</dt><dd>${cluster.completeness_score}/10 core · ${cluster.content_completeness}/13 content</dd>
        </dl>
        ${STANDALONE ? "" : `<p><a href="#/search">Open the research explorer</a> for the full claim-by-claim evidence chain.</p>`}
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
        <h1 id="explore-title">Scholarship</h1>
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
    const view = document.querySelector("#explore-view");
    if (!view) return;
    if (!data.loaded) view.innerHTML = `<p class="dossier-loading">Reading the corpus…</p>`;
    try {
      await load();
    } catch (error) {
      view.innerHTML = `<p class="dossier-loading">Could not read the corpus: ${esc(error.message)}</p>`;
      return;
    }
    const hash = location.hash;
    const browse = hash.match(/^#\/explore\/browse\/([a-z_]+)/);
    const object = hash.match(/^#\/explore\/(IDENT-[^?]+)/);
    if (hash.startsWith("#/scholarship")) renderScholarship(view);
    else if (hash.startsWith("#/explore/publications")) renderPublications(view);
    else if (browse) renderBrowse(view, browse[1]);
    else if (object) renderObject(view, decodeURIComponent(object[1]));
    else renderIndex(view, hash.split("?")[1] || "");
    bindMediaFallbacks(view);
    view.scrollTop = 0;
  }

  window.ReadingRoom = {render};
})();
