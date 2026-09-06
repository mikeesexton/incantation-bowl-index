const state = {
  page: 1, pageSize: 40, total: 0, stats: null, csrf: "", route: "explore",
  queueAction: "", currentReview: null, identityRequest: 0,
};
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

function humanize(value = "") {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase());
}

function safeUrl(value) {
  if (!value) return "";
  try {
    const parsed = new URL(value);
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : "";
  } catch { return ""; }
}

function externalLink(url, label) {
  const safe = safeUrl(url);
  if (!safe) return escapeHtml(label || "Source unavailable online");
  return `<a href="${escapeHtml(safe)}" target="_blank" rel="noreferrer">${escapeHtml(label || url)}</a>`;
}

function valueOf(claim) {
  return claim.normalized_value || claim.value_text || claim.value_json || "—";
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("is-visible");
  window.setTimeout(() => node.classList.remove("is-visible"), 3200);
}

function optionList(select, values) {
  const current = select.value;
  values.filter(value => ![...select.options].some(option => option.value === value)).forEach(value => select.insertAdjacentHTML(
    "beforeend", `<option value="${escapeHtml(value)}">${escapeHtml(humanize(value))}</option>`
  ));
  select.value = current;
}

function queryParams() {
  const params = new URLSearchParams(new FormData($("#filters")));
  for (const [key, value] of [...params]) if (!value) params.delete(key);
  if (state.queueAction) params.set("next_action", state.queueAction);
  params.set("page", state.page);
  params.set("page_size", state.pageSize);
  params.set("sort", $("#sort").value);
  return params;
}

function renderActiveFilters(params) {
  const labels = [];
  for (const [key, value] of params) {
    if (["page", "page_size", "sort"].includes(key)) continue;
    const label = key === "present" ? "Recorded field" : key === "coverage" ? "Missing field" : humanize(key);
    labels.push(`<button class="filter-chip" type="button" data-clear-filter="${escapeHtml(key)}">${escapeHtml(label)}: ${escapeHtml(humanize(value))} <span aria-hidden="true">×</span></button>`);
  }
  $("#active-filters").innerHTML = labels.join("");
  $$(`[data-clear-filter]`).forEach(button => button.addEventListener("click", () => {
    if (button.dataset.clearFilter === "next_action") state.queueAction = "";
    else {
      const control = $(`[name="${button.dataset.clearFilter}"]`, $("#filters"));
      if (control) control.value = "";
    }
    state.page = 1;
    loadIdentities();
  }));
}

function identityRow(item) {
  const context = [...item.locations.slice(0, 1), ...item.languages.slice(0, 1)].filter(Boolean);
  const date = item.dating[0];
  const conflicts = item.conflict_fields.length
    ? `<span class="conflict-flag">${item.conflict_fields.length} field${item.conflict_fields.length === 1 ? "" : "s"} to review</span>`
    : "No flagged differences";
  const identifiers = item.identifiers.slice(0, 2).join(" · ");
  return `<tr tabindex="0" data-identity="${escapeHtml(item.identity_id)}" aria-label="Open ${escapeHtml(item.label)} dossier">
    <td><div class="identity-name"><span class="identity-monogram" aria-hidden="true">${item.member_count}</span><div>
      <strong>${escapeHtml(item.label)}</strong>
      <div class="meta-line"><span>${escapeHtml(item.identity_id)}</span><span>${escapeHtml(humanize(item.record_status))}</span>${item.member_count > 1 ? `<span>${item.member_count} linked records</span>` : ""}</div>
      <div class="identifier-preview" title="${escapeHtml(identifiers)}">${escapeHtml(identifiers || "No identifier recorded")}</div>
    </div></div></td>
    <td><div class="context-main">${escapeHtml(context.join(" · ") || "Context not yet established")}</div><div class="context-sub">${escapeHtml(date || "Dating missing")}</div></td>
    <td><span class="evidence-number">${item.source_count}</span><span class="evidence-label">source${item.source_count === 1 ? "" : "s"} · ${item.appearance_count} appearance${item.appearance_count === 1 ? "" : "s"}</span><div class="context-sub">${conflicts}</div></td>
    <td class="coverage-cell"><progress class="coverage-progress" value="${item.completeness_score}" max="10" aria-label="${item.completeness_score} of 10 core fields covered">${item.completeness_score}/10</progress><div class="coverage-caption"><span>${item.completeness_score}/10</span><span>Next: ${escapeHtml(humanize(item.next_action))}</span></div></td>
  </tr>`;
}

async function loadIdentities() {
  const request = ++state.identityRequest;
  const params = queryParams();
  if (state.route === "explore") history.replaceState(null, "", `#/explore?${params}`);
  renderActiveFilters(params);
  $("#identity-rows").innerHTML = `<tr><td colspan="4" class="dossier-loading">Reading identity index…</td></tr>`;
  try {
    const data = await api(`/api/identities?${params}`);
    if (request !== state.identityRequest) return;
    state.total = data.total;
    $("#result-count").textContent = `${data.total.toLocaleString()} matching ${data.total === 1 ? "identity" : "identities"}`;
    $("#identity-rows").innerHTML = data.items.map(identityRow).join("");
    $("#empty-state").hidden = data.items.length !== 0;
    $("#previous-page").disabled = data.page <= 1;
    $("#next-page").disabled = data.page * data.page_size >= data.total;
    $("#page-label").textContent = `Page ${data.page} of ${Math.max(1, Math.ceil(data.total / data.page_size))}`;
    if (!$("#status-filter").dataset.ready) {
      optionList($("#status-filter"), data.facets.statuses);
      optionList($("#authenticity-filter"), data.facets.authenticities);
      optionList($("#type-filter"), data.facets.object_types);
      $("#status-filter").dataset.ready = "true";
    }
    bindIdentityLinks();
  } catch (error) {
    if (request !== state.identityRequest) return;
    $("#identity-rows").innerHTML = `<tr><td colspan="4">Records could not be loaded. Change a filter or refresh to retry.</td></tr>`;
    toast(error.message);
  }
}

function coverageBadges(summary) {
  const fields = ["location", "provenance", "dating", "dimensions", "material", "language", "script", "text_edition", "translation", "image"];
  return fields.map(field => `<span class="coverage-badge ${summary[`has_${field}`] ? "is-present" : "is-missing"}"><i aria-hidden="true"></i>${escapeHtml(humanize(field))}</span>`).join("");
}

function sourceNote(item) {
  return `<div class="source-note">${externalLink(item.source_url, item.source_title || item.source_citation)}${item.locator ? ` <span>· ${escapeHtml(item.locator)}</span>` : ""}</div>`;
}

function claimsSection(claims) {
  if (!claims.length) return `<div class="section-empty">No source-attributed claims yet.</div>`;
  const grouped = claims.reduce((result, claim) => {
    (result[claim.field] ||= []).push(claim);
    return result;
  }, {});
  return `<div class="claim-grid">${Object.entries(grouped).map(([field, values]) => `<article class="claim-card">
    <h4>${escapeHtml(humanize(field))}${values.length > 1 ? `<span>${values.length} reports</span>` : ""}</h4>
    ${values.map(claim => `<div class="claim-value"><strong>${escapeHtml(valueOf(claim))}</strong><span class="certainty">${escapeHtml(humanize(claim.certainty))}</span>${claim.notes ? `<p>${escapeHtml(claim.notes)}</p>` : ""}${sourceNote(claim)}</div>`).join("")}
  </article>`).join("")}</div>`;
}

function appearancesSection(items) {
  if (!items.length) return `<div class="section-empty">No source appearances recorded.</div>`;
  return `<div class="source-list">${items.map(item => `<article class="source-row">
    <span class="source-type">${escapeHtml(humanize(item.source_type))}</span>
    <div><h4>${externalLink(item.url || item.source_url, item.title || item.source_title)}</h4>
      <p>${escapeHtml(item.description || item.source_citation || "No description")}</p>
      <div class="meta-line"><span>${escapeHtml(item.locator)}</span><span>${Math.round(item.confidence * 100)}% link confidence</span><span>${escapeHtml(humanize(item.rights_status))}</span></div>
    </div>
  </article>`).join("")}</div>`;
}

function textsSection(items) {
  if (!items.length) return `<div class="section-empty">No transcription, translation, incipit, or text summary recorded.</div>`;
  return `<div class="text-list">${items.map(item => `<article class="text-card">
    <div class="meta-line"><span>${item.proofreading_status === "reading_text_checked" ? "Scan-checked reading text · normalized typography" : "Text proofreading not complete"}</span></div><header><div><span class="source-type">${escapeHtml(humanize(item.text_type))}</span><h4>${escapeHtml(item.language || "Language not stated")}${item.script ? ` · ${escapeHtml(item.script)}` : ""}</h4></div><span class="rights-label ${item.public_ok ? "is-public" : ""}">${item.public_ok ? "Public reuse cleared" : escapeHtml(humanize(item.rights_status))}</span></header>
    <pre dir="auto">${escapeHtml(item.content)}</pre>${sourceNote(item)}
  </article>`).join("")}</div>`;
}

function eventsSection(items) {
  if (!items.length) return `<div class="section-empty">No provenance or object-history events recorded.</div>`;
  return `<div class="timeline">${items.map(item => `<article>
    <span class="timeline-dot" aria-hidden="true"></span><div class="timeline-date">${escapeHtml(item.start_date || "Date unknown")}</div>
    <h4>${escapeHtml(humanize(item.event_type))}${item.place ? ` · ${escapeHtml(item.place)}` : ""}</h4>
    <p>${escapeHtml(item.details)}</p>${item.actor ? `<div class="meta-line"><span>${escapeHtml(item.actor)}</span></div>` : ""}${sourceNote(item)}
  </article>`).join("")}</div>`;
}

function membersSection(data) {
  const identifiersByObject = data.identifiers.reduce((result, item) => {
    (result[item.object_id] ||= []).push(`${item.scheme}: ${item.value}`);
    return result;
  }, {});
  return `<div class="member-list">${data.members.map(item => `<article>
    <div><span class="source-type">${escapeHtml(humanize(item.object_type))}</span><h4>${escapeHtml(item.label)}</h4><p>${escapeHtml(item.summary || "No record-level summary")}</p></div>
    <div class="member-meta"><code>${escapeHtml(item.id)}</code><span>${escapeHtml(humanize(item.record_status))}</span><span>${escapeHtml(humanize(item.authenticity))}</span><small>${escapeHtml((identifiersByObject[item.id] || []).join(" · "))}</small></div>
  </article>`).join("")}</div>`;
}

function mediaSection(items) {
  if (!items.length) return `<div class="section-empty">No image or drawing reference recorded.</div>`;
  return `<div class="media-list">${items.map(item => `<a href="${escapeHtml(safeUrl(item.url || item.source_url) || "#")}" target="_blank" rel="noreferrer">
    <span class="media-mark" aria-hidden="true">▧</span><strong>${escapeHtml(humanize(item.media_type))}</strong><small>${escapeHtml(item.source_title)} · ${escapeHtml(humanize(item.rights_status))} · reuse: ${escapeHtml(humanize(item.public_reuse_decision || "needs_review"))}</small>
  </a>`).join("")}</div>`;
}

function dossierMarkup(data) {
  const s = data.summary;
  const conflict = s.conflict_fields.length ? `<aside class="conflict-callout"><strong>Claim differences require review</strong><span>${escapeHtml(s.conflict_fields.map(humanize).join(" · "))}</span></aside>` : "";
  return `<div class="dossier-overview">
    <div class="metric"><strong>${s.member_count}</strong><span>source records</span></div>
    <div class="metric"><strong>${s.source_count}</strong><span>sources</span></div>
    <div class="metric"><strong>${s.claim_count}</strong><span>claims</span></div>
    <div class="metric"><strong>${s.completeness_score}/10</strong><span>core coverage</span></div>
  </div>
  ${conflict}
  <div class="coverage-badges">${coverageBadges(s)}</div>
  <nav class="section-nav" aria-label="Dossier sections">
    <button type="button" data-dossier-section="claims">Claims <span>${data.claims.length}</span></button><button type="button" data-dossier-section="appearances">Appearances <span>${data.appearances.length}</span></button><button type="button" data-dossier-section="texts">Texts <span>${data.texts.length}</span></button><button type="button" data-dossier-section="events">History <span>${data.events.length}</span></button><button type="button" data-dossier-section="members">Records <span>${data.members.length}</span></button>
  </nav>
  <section class="dossier-section" id="claims"><div class="section-heading"><span>01</span><div><h3>Claims by field</h3><p>Alternative reports remain separate and source-attributed.</p></div></div>${claimsSection(data.claims)}</section>
  <section class="dossier-section" id="appearances"><div class="section-heading"><span>02</span><div><h3>Source appearances</h3><p>Museum pages, catalogues, publications, auctions, and repositories.</p></div></div>${appearancesSection(data.appearances)}</section>
  <section class="dossier-section" id="texts"><div class="section-heading"><span>03</span><div><h3>Texts and translations</h3><p>This private view displays research content alongside its reuse status.</p></div></div>${textsSection(data.texts)}</section>
  <section class="dossier-section" id="events"><div class="section-heading"><span>04</span><div><h3>Provenance and object history</h3></div></div>${eventsSection(data.events)}</section>
  <section class="dossier-section" id="media"><div class="section-heading"><span>05</span><div><h3>Images and media</h3></div></div>${mediaSection(data.media)}</section>
  <section class="dossier-section" id="members"><div class="section-heading"><span>06</span><div><h3>Underlying object records</h3><p>These records are linked, never erased by the identity layer.</p></div></div>${membersSection(data)}</section>`;
}

async function openDossier(identityId) {
  const dialog = $("#dossier");
  $("#dossier-id").textContent = identityId;
  $("#dossier-title").textContent = "Loading dossier…";
  $("#dossier-content").innerHTML = `<p class="dossier-loading">Gathering claims and appearances…</p>`;
  if (!dialog.open) dialog.showModal();
  try {
    const data = await api(`/api/identities/${encodeURIComponent(identityId)}`);
    $("#dossier-title").textContent = data.summary.label;
    $("#dossier-content").innerHTML = dossierMarkup(data);
    $$(`[data-dossier-section]`, $("#dossier-content")).forEach(button => button.addEventListener("click", () => {
      $(`#${button.dataset.dossierSection}`, $("#dossier-content")).scrollIntoView({behavior: "smooth", block: "start"});
    }));
    return data;
  } catch (error) {
    $("#dossier-content").innerHTML = `<p>${escapeHtml(error.message)}</p>`;
    throw error;
  }
}

function bindIdentityLinks(root = document) {
  $$(`[data-identity]`, root).forEach(node => {
    const open = () => openDossier(node.dataset.identity);
    node.addEventListener("click", event => {
      if (node.matches("button") || !event.target.closest("a,button")) void open().catch(() => {});
    });
    node.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); void open().catch(() => {}); }
    });
  });
}

function queueMarkup(stats) {
  const total = stats.identities;
  const labels = {
    location: "Establish location", provenance: "Trace provenance", dating: "Resolve dating",
    dimensions: "Record dimensions", material: "Describe material", language: "Classify language",
    script: "Classify script", text_edition: "Locate a text edition", translation: "Locate a translation",
    image: "Review imagery", "rights review": "Review reuse rights",
  };
  const order = Object.entries(stats.next_actions).sort((a, b) => b[1] - a[1]);
  const coverageOrder = ["location", "provenance", "dating", "dimensions", "material", "language", "script", "text_edition", "translation", "image"];
  const coverage = coverageOrder.map(field => [field, stats.coverage[field] || 0]);
  return `<div class="workspace-head"><div><span class="eyebrow">Corpus worklist</span><h1 id="queues-title">Enrichment queues</h1></div><div class="queue-summary"><strong>${total.toLocaleString()}</strong><span>working identities</span></div></div>
    <div class="queue-intro"><p>Each identity is assigned its earliest missing core field. Pick a queue to continue in the explorer.</p><div><span class="legend-dot present"></span>Recorded <span class="legend-dot missing"></span>Missing</div></div>
    <section class="queue-section"><div class="section-heading"><span>01</span><div><h2>Next best action</h2><p>Mutually exclusive queues ordered by corpus impact.</p></div></div>
      <div class="queue-grid">${order.map(([action, count], index) => `<button class="queue-card" type="button" data-queue="${escapeHtml(action)}"><span class="queue-rank">${String(index + 1).padStart(2, "0")}</span><strong>${count.toLocaleString()}</strong><h3>${escapeHtml(labels[action] || humanize(action))}</h3><p>${(count / total * 100).toFixed(1)}% of identities</p><span class="queue-arrow" aria-hidden="true">→</span></button>`).join("")}</div>
    </section>
    <section class="queue-section"><div class="section-heading"><span>02</span><div><h2>Coverage map</h2><p>Presence only; conflicting values are counted as present and flagged separately.</p></div></div>
      <div class="coverage-matrix">${coverage.map(([field, count]) => {
        const percent = total ? count / total * 100 : 0;
        const missing = Math.max(0, total - count);
        return `<article class="coverage-category"><header><strong>${escapeHtml(humanize(field))}</strong><span>${percent.toFixed(1)}%</span></header><progress class="matrix-progress" value="${count}" max="${total || 1}" aria-label="${escapeHtml(humanize(field))}: ${percent.toFixed(1)}% covered">${percent.toFixed(1)}%</progress><div class="coverage-counts"><span>${count.toLocaleString()} covered</span><span>${missing.toLocaleString()} missing</span></div></article>`;
      }).join("")}</div>
    </section>
    <section class="queue-section"><div class="section-heading"><span>03</span><div><h2>Review pressure</h2></div></div>
      <div class="pressure-grid"><article><strong>${stats.conflicted_identities}</strong><span>identities with differences to review</span><button type="button" data-conflicts>Open conflicts</button></article><article><strong>${stats.pending_reviews}</strong><span>pending concordance decisions</span><a href="#/reviews">Open workbench</a></article><article><strong>${stats.multi_record_identities}</strong><span>multi-record identities</span><button type="button" data-multirecord>Inspect linked records</button></article></div>
    </section>`;
}

function renderQueues() {
  $("#queues-view").innerHTML = queueMarkup(state.stats);
  $$(`[data-queue]`, $("#queues-view")).forEach(button => button.addEventListener("click", () => {
    state.queueAction = button.dataset.queue;
    state.page = 1;
    location.hash = `#/explore?${queryParams()}`;
  }));
  $("[data-conflicts]", $("#queues-view")).addEventListener("click", () => {
    $(`[name="conflict"]`).value = "yes";
    state.queueAction = "";
    state.page = 1;
    location.hash = `#/explore?${queryParams()}`;
  });
  $("[data-multirecord]", $("#queues-view")).addEventListener("click", () => {
    $("#sort").value = "sources";
    state.queueAction = "";
    state.page = 1;
    location.hash = `#/explore?${queryParams()}`;
  });
}

function reviewListItem(item) {
  return `<button class="review-list-item ${state.currentReview === item.id ? "is-active" : ""}" type="button" data-review="${escapeHtml(item.id)}">
    <span class="review-state ${escapeHtml(item.status)}">${escapeHtml(humanize(item.status))}</span>
    <strong>${escapeHtml(item.object_a_label)}</strong><i>compared with</i><strong>${escapeHtml(item.object_b_label)}</strong>
    <small>${escapeHtml(item.method)} · score ${item.score.toFixed(3)}</small>
  </button>`;
}

function comparisonIdentity(dossier, side) {
  if (!dossier) return `<div class="section-empty">Identity unavailable.</div>`;
  const s = dossier.summary;
  const topClaims = dossier.claims.slice(0, 10);
  return `<article class="compare-column"><span class="compare-side">Object ${side}</span><button class="compare-title" type="button" data-identity="${escapeHtml(s.identity_id)}">${escapeHtml(s.label)}</button>
    <code>${escapeHtml(s.identity_id)}</code>
    <div class="compare-stats"><span><strong>${s.member_count}</strong> records</span><span><strong>${s.source_count}</strong> sources</span><span><strong>${s.completeness_score}</strong>/10 coverage</span></div>
    <h4>Identifiers</h4><ul>${s.identifiers.map(item => `<li>${escapeHtml(item)}</li>`).join("") || "<li>None recorded</li>"}</ul>
    <h4>Reported facts</h4><dl>${topClaims.map(item => `<div><dt>${escapeHtml(humanize(item.field))}</dt><dd>${escapeHtml(valueOf(item))}</dd></div>`).join("") || "<div><dd>No claims recorded</dd></div>"}</dl>
  </article>`;
}

function reviewDetailMarkup(item) {
  const evidence = item.evidence.length ? item.evidence.map(entry => `<article><span class="support-mark support-${entry.supports_match}">${entry.supports_match > 0 ? "+" : entry.supports_match < 0 ? "−" : "?"}</span><div><strong>${escapeHtml(humanize(entry.evidence_type))}</strong><p>${escapeHtml(entry.notes || "No note")}</p>${entry.source_title ? externalLink(entry.source_url, entry.source_title) : ""}</div></article>`).join("") : `<div class="section-empty">No evidence entries yet.</div>`;
  return `<div class="review-detail-head"><div><span class="eyebrow">${escapeHtml(item.id)}</span><h2>${escapeHtml(humanize(item.status))}</h2></div><div><span>Method</span><strong>${escapeHtml(humanize(item.method))}</strong><span>Score</span><strong>${item.score.toFixed(3)}</strong></div></div>
    <div class="rationale"><strong>Why this pair was generated</strong><p>${escapeHtml(item.rationale)}</p></div>
    <div class="comparison">${comparisonIdentity(item.identity_a, "A")}${comparisonIdentity(item.identity_b, "B")}</div>
    <section class="evidence-panel"><h3>Decision evidence</h3>${evidence}</section>
    <form id="review-form" class="decision-form">
      <div><label>Decision<select name="status"><option value="same_object" ${item.status === "same_object" ? "selected" : ""}>Same physical object</option><option value="different_objects" ${item.status === "different_objects" ? "selected" : ""}>Different physical objects</option><option value="insufficient_evidence" ${item.status === "insufficient_evidence" || item.status === "pending" ? "selected" : ""}>Insufficient evidence</option></select></label></div>
      <label class="decision-note">Evidence note<textarea name="note" rows="3" minlength="12" required placeholder="State the identifiers, measurements, provenance, or textual features supporting this decision."></textarea></label>
      <button class="primary-button" type="submit">Record reversible decision</button>
    </form>`;
}

async function loadReview(id) {
  state.currentReview = id;
  const panel = $("#review-detail");
  panel.innerHTML = `<p class="dossier-loading">Building comparison…</p>`;
  try {
    const item = await api(`/api/reviews/${encodeURIComponent(id)}`);
    panel.innerHTML = reviewDetailMarkup(item);
    bindIdentityLinks(panel);
    $("#review-form").addEventListener("submit", async event => {
      event.preventDefault();
      const button = $("button[type=submit]", event.currentTarget);
      button.disabled = true;
      try {
        const payload = Object.fromEntries(new FormData(event.currentTarget));
        const updated = await api(`/api/reviews/${encodeURIComponent(id)}`, {
          method: "POST", headers: {"Content-Type": "application/json", "X-IBI-Token": state.csrf},
          body: JSON.stringify(payload),
        });
        panel.innerHTML = reviewDetailMarkup(updated);
        state.stats = await api("/api/stats");
        toast("Decision recorded; identity index refreshed.");
        await loadReviews();
      } catch (error) { toast(error.message); button.disabled = false; }
    });
  } catch (error) { panel.innerHTML = `<p>${escapeHtml(error.message)}</p>`; }
}

async function loadReviews() {
  const status = $("#review-status")?.value || "unresolved";
  const q = $("#review-search")?.value || "";
  const data = await api(`/api/reviews?status=${encodeURIComponent(status)}&q=${encodeURIComponent(q)}&limit=80`);
  $("#review-list").innerHTML = data.items.length ? data.items.map(reviewListItem).join("") : `<div class="section-empty">No decisions in this view.</div>`;
  $$(`[data-review]`, $("#review-list")).forEach(button => button.addEventListener("click", () => loadReview(button.dataset.review)));
  if (data.items.length && (!state.currentReview || !data.items.some(item => item.id === state.currentReview))) loadReview(data.items[0].id);
  if (!data.items.length) $("#review-detail").innerHTML = `<div class="review-zero"><span>✓</span><h2>The queue is clear</h2><p>Try a reviewed status to audit prior identity decisions.</p></div>`;
}

function renderReviews() {
  $("#reviews-view").innerHTML = `<div class="workspace-head"><div><span class="eyebrow">Reversible identity decisions</span><h1 id="reviews-title">Concordance workbench</h1></div><div class="review-controls"><input id="review-search" type="search" aria-label="Search concordance reviews" placeholder="Search compared objects…"><select id="review-status" aria-label="Review status"><option value="unresolved">Needs attention</option><option value="pending">Pending</option><option value="insufficient_evidence">Insufficient evidence</option><option value="same_object">Same object</option><option value="different_objects">Different objects</option><option value="all">All decisions</option></select></div></div>
    <div class="review-workbench"><aside id="review-list" class="review-list"></aside><div id="review-detail" class="review-detail"><p class="dossier-loading">Loading review queue…</p></div></div>`;
  let timer;
  $("#review-status").addEventListener("change", () => { state.currentReview = null; loadReviews(); });
  $("#review-search").addEventListener("input", () => { window.clearTimeout(timer); timer = window.setTimeout(loadReviews, 180); });
  loadReviews().catch(error => toast(error.message));
}

function activateRoute() {
  const previous = state.route;
  const route = (location.hash.match(/^#\/(home|reading|scholarship|explore|queues|reviews)(?:[/?]|$)/) || [])[1] || "home";
  state.route = route;
  document.body.classList.toggle("is-home", route === "home");
  const viewId = route === "scholarship" ? "reading-view" : `${route}-view`;
  $$(".view").forEach(view => view.classList.toggle("is-active", view.id === viewId));
  $$(".view-tab").forEach(tab => {
    tab.classList.toggle("is-active", tab.dataset.route === route);
    if (tab.dataset.route === route) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  });
  $(".sidebar").classList.toggle("is-hidden", route !== "explore");
  if (route === "home") window.Introduction?.render();
  if ((route === "reading" || route === "scholarship") && window.ReadingRoom) window.ReadingRoom.render();
  if (route === "explore") {
    const params = new URLSearchParams(location.hash.split("?")[1] || "");
    for (const control of $("#filters").elements) {
      if (!control.name) continue;
      const value = params.get(control.name) || "";
      // Facet options arrive with the first search response. Preserve direct links.
      if (value && control.tagName === "SELECT" && ![...control.options].some(option => option.value === value)) {
        control.add(new Option(humanize(value), value));
      }
      control.value = value;
    }
    state.queueAction = params.get("next_action") || "";
    state.page = Math.max(1, parseInt(params.get("page"), 10) || 1);
    $("#sort").value = params.get("sort") || "completeness_desc";
    loadIdentities();
  }
  if (route === "queues" && state.stats) renderQueues();
  if (route === "reviews") renderReviews();
  if (route !== previous) window.scrollTo({top: 0, behavior: "instant"});
  $("#workspace").focus({preventScroll: true});
}

async function recordDecision(dedupeId, status, note) {
  if (!dedupeId || !["same_object", "different_objects", "insufficient_evidence"].includes(status)) {
    throw new Error("A review ID and valid decision status are required.");
  }
  if (!note || note.trim().length < 12) throw new Error("The evidence note must be at least 12 characters.");
  const updated = await api(`/api/reviews/${encodeURIComponent(dedupeId)}`, {
    method: "POST", headers: {"Content-Type": "application/json", "X-IBI-Token": state.csrf},
    body: JSON.stringify({status, note}),
  });
  state.stats = await api("/api/stats");
  if (state.route === "reviews") renderReviews();
  return updated;
}

function registerWebMCP() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const register = tool => Promise.resolve(context.registerTool(tool)).catch(error => console.error("WebMCP registration failed", error));
  register({
    name: "search_bowl_identities", title: "Search bowl identities",
    description: "Search the local incantation-bowl corpus and update the visible identity explorer.",
    inputSchema: {type: "object", properties: {query: {type: "string"}, missingField: {type: "string", enum: ["", "location", "provenance", "dating", "dimensions", "material", "language", "script", "text_edition", "translation", "image"]}}, additionalProperties: false},
    annotations: {readOnlyHint: true, untrustedContentHint: true},
    async execute(input) {
      $("#search").value = input?.query || "";
      $(`[name="coverage"]`).value = input?.missingField || "";
      state.page = 1; state.queueAction = "";
      if (location.hash !== `#/explore?${queryParams()}`) location.hash = `#/explore?${queryParams()}`;
      await loadIdentities();
      return {matchingIdentities: state.total, query: $("#search").value};
    },
  });
  register({
    name: "open_bowl_identity", title: "Open bowl identity",
    description: "Open the evidence dossier for one local identity ID.",
    inputSchema: {type: "object", properties: {identityId: {type: "string", pattern: "^IDENT-[A-F0-9]{12}$"}}, required: ["identityId"], additionalProperties: false},
    annotations: {readOnlyHint: true, untrustedContentHint: true},
    async execute(input) {
      const data = await openDossier(input.identityId);
      return {identityId: data.summary.identity_id, label: data.summary.label, sources: data.summary.source_count, conflicts: data.summary.conflict_fields};
    },
  });
  register({
    name: "record_concordance_decision", title: "Record concordance decision",
    description: "Record a reversible evidence-backed same-object, different-object, or insufficient-evidence decision for an existing review pair.",
    inputSchema: {type: "object", properties: {dedupeId: {type: "string", pattern: "^DED-[A-F0-9]{12}$"}, status: {type: "string", enum: ["same_object", "different_objects", "insufficient_evidence"]}, note: {type: "string", minLength: 12}}, required: ["dedupeId", "status", "note"], additionalProperties: false},
    annotations: {readOnlyHint: false, untrustedContentHint: false},
    async execute(input) {
      const updated = await recordDecision(input.dedupeId, input.status, input.note);
      return {dedupeId: updated.id, status: updated.status, decidedAt: updated.decided_at};
    },
  });
}

async function initialize() {
  activateRoute();
  try {
    const [config, stats] = await Promise.all([api("/api/config"), api("/api/stats")]);
    state.csrf = config.csrf_token;
    state.stats = stats;
    $("#identity-count").textContent = `${stats.identities.toLocaleString()} identities`;
    if (state.route === "queues") renderQueues();
    registerWebMCP();
  } catch (error) { toast(error.message); }
}

let searchTimer;
$("#filters").addEventListener("input", () => {
  state.page = 1;
  state.queueAction = "";
  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(loadIdentities, 180);
});
$("#filters").addEventListener("reset", () => {
  state.page = 1;
  state.queueAction = "";
  window.setTimeout(loadIdentities, 0);
});
$("#sort").addEventListener("change", () => { state.page = 1; loadIdentities(); });
$("#previous-page").addEventListener("click", () => { state.page -= 1; loadIdentities(); });
$("#next-page").addEventListener("click", () => { state.page += 1; loadIdentities(); });
$("#close-dossier").addEventListener("click", () => $("#dossier").close());
$("#dossier").addEventListener("click", event => { if (event.target === $("#dossier")) $("#dossier").close(); });
$("#refresh-corpus").addEventListener("click", async event => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    state.stats = await api("/api/refresh", {
      method: "POST", headers: {"Content-Type": "application/json", "X-IBI-Token": state.csrf}, body: "{}",
    });
    $("#identity-count").textContent = `${state.stats.identities.toLocaleString()} identities`;
    window.Introduction?.invalidate();
    activateRoute();
    toast("Corpus reloaded from SQLite.");
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
});
// Filters stay in the DOM on narrow screens — they used to be display:none —
// but start collapsed so they do not push the records off the first screen.
// The summary is hidden above 900px, so widening the window must reopen the
// panel or the filters would be shut with no control to reopen them.
const narrow = window.matchMedia("(max-width: 900px)");
function fitFilterPanel(query) {
  const panel = $("#filter-panel");
  if (panel) panel.open = !query.matches;
}
fitFilterPanel(narrow);
narrow.addEventListener("change", fitFilterPanel);
window.addEventListener("hashchange", activateRoute);

initialize();
