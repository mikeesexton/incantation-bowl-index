/* Mike-only operational intelligence. Source wording is always escaped. */
(function () {
  "use strict";
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const human = value => String(value || "unknown").replaceAll("_", " ");
  const meaningful = value => value != null && value !== "" && (!Array.isArray(value) || value.length > 0);
  const shown = value => Array.isArray(value) ? value.join("; ") : value;
  const fieldNames = {full_description:"Source description", description_scope:"Description coverage", language_stated:"Stated language", script_stated:"Stated script", dimensions_text:"Dimensions", condition_text:"Condition", provenance_text:"Source provenance", literature:"Publication references", source_email_ids:"Source emails", image_urls:"Source images", result_text:"Source result"};
  const flagNames = {no_provenance_stated:"Not stated", stated_history_only_after_1970:"History only after 1970", vague_undated_provenance:"Undated collection", country_or_region_mention:"Country or region mentioned", changed_provenance_wording:"Changed wording"};
  const statusNames = {unknown:"Outcome not stated", offered:"Dealer offer", upcoming:"Upcoming", sold:"Sold", unsold:"Unsold", withdrawn:"Withdrawn"};
  function options(rows, field) {
    return [...new Set(rows.map(r => r[field]).filter(Boolean))].sort().map(value => `<option value="${escape(value)}">${escape(human(value))}</option>`).join("");
  }
  function display(row) {
    const flags = (row.provenance_flags || []).map(f => flagNames[f.flag] || human(f.flag)).join("; ");
    const matches = (row.corpus_matches || []).map(m => `<li>${escape(m.object_id || m.appearance_id)} · ${escape(m.basis)} · ranking ${escape(m.score)}</li>`).join("");
    const fields = ["sale_name", "sale_number", "sale_id", "lot_number", "stock_number", "sale_timezone", "full_description", "description_scope", "language_stated", "script_stated", "dimensions_text", "condition_text", "provenance_text", "literature", "estimate_low", "estimate_high", "currency", "starting_bid", "asking_price", "hammer", "premium_total", "buyer_premium", "result_text", "quantity_text", "price_basis", "search_term", "keyword_hits", "source_email_ids", "image_urls", "notes"];
    const details = fields.filter(k => meaningful(row[k])).map(k => `<dt>${escape(fieldNames[k] || human(k))}</dt><dd>${escape(shown(row[k]))}</dd>`).join("");
    const evidenceRows = [...new Map((row.evidence || []).map(e => [[e.kind,e.sha256,e.locator,e.message_id].join("|"), e])).values()];
    const evidence = evidenceRows.map(e => `<li>${escape(e.kind)} · ${escape(e.message_id || "page capture")} · ${escape(e.locator)} · ${escape(e.sha256.slice(0, 12))}</li>`).join("");
    const changes = (row.history || []).filter(h => h.changed).map(h => {
      const keys = Object.keys(h.current).filter(k => h.previous && JSON.stringify(h.previous[k]) !== JSON.stringify(h.current[k]) && (h.previous[k] != null || h.current[k] != null));
      return `<li>${escape(h.observed_at)}${h.new ? " · first observation" : ""}${keys.length ? `<ul>${keys.map(k => `<li>${escape(fieldNames[k] || human(k))}: ${escape(JSON.stringify(h.previous[k]))} → ${escape(JSON.stringify(h.current[k]))}</li>`).join("")}</ul>` : ""}</li>`;
    }).join("");
    const prices = [["Estimate",row.estimate],["Asking",row.asking_price],["Hammer",row.hammer],["Including premium",row.premium_total]].filter(([,v])=>meaningful(v));
    const price = prices.map(([label,value])=>`<span class="market-value-label">${escape(label)}</span>${escape(value)}`).join("<br>") || "Not stated";
    const check = row.source_check;
    const checked = check?.status === "checked";
    const checkLabel = checked ? "Source compared" : check?.status === "needs_correction" ? "Correction queued in chat" : check?.status === "blocked" ? "Source check blocked" : "Source check in morning chat";
    return `<tr><td class="intelligence-listing"><a href="${escape(row.url)}" rel="noreferrer">${escape(row.title)}</a><p class="intelligence-meta">${escape(row.stock_number || row.lot_number || "")}${row.historical ? " · Historical correspondence" : ""}</p><span class="source-check-status">${escape(checkLabel)}</span><details class="listing-details"><summary>Listing details</summary><dl>${details}</dl>${check ? `<p class="source-check-note">${escape(check.note)}<br><small>Source comparison ${escape(check.checked_at.slice(0,10))}; identity suggestions remain separate.</small></p>` : ""}${matches ? `<details><summary>Corpus links to discuss in chat</summary><ul>${matches}</ul></details>` : ""}${evidence ? `<details><summary>Source evidence (${evidenceRows.length})</summary><ul>${evidence}</ul></details>` : ""}${changes ? `<details><summary>Observation history</summary><ol>${changes}</ol></details>` : ""}<p class="intelligence-meta">First recorded ${escape(row.first_seen?.slice(0,10) || "date unknown")}</p></details></td><td>${escape(row.house || "Unknown")}<small class="intelligence-meta">${escape(row.platform || "")}</small></td><td>${escape(statusNames[row.market_status] || human(row.market_status))}<small class="intelligence-meta">${escape(row.sale_date_text || "Sale date not stated")}</small>${row.relevance && row.relevance !== "relevant" ? `<small class="intelligence-meta">${escape(human(row.relevance))}</small>` : ""}</td><td>${price}</td><td>${escape(flags || (row.provenance_text ? "Stated in source" : "Not assessed"))}</td></tr>`;
  }
  function mount(container, data) {
    const rows = data.listings || [];
    const counts = Object.entries(data.counts || {}).map(([k,v]) => `${human(k)}: ${v}`).join(" · ");
    const matchCount = rows.filter(r=>(r.corpus_matches || []).length).length + (data.reappearance_candidates || []).length;
    container.innerHTML = `<header class="intelligence-heading"><h2>Auction alerts</h2><p>${rows.length} listing leads · ${Object.keys(data.processed || {}).length} processed emails${matchCount ? ` · ${matchCount} match suggestions` : ""}</p></header><aside class="market-chat-note"><strong>Checks happen in your morning chat.</strong> The scheduled task compares extracted details with their sources and brings you specific questions about possible bowl matches. This page keeps the evidence and history available.</aside><form class="intelligence-filters" aria-label="Filter auction alerts"><label>House<select name="house"><option value="">All houses</option>${options(rows,"house")}</select></label><label>Platform<select name="platform"><option value="">All platforms</option>${options(rows,"platform")}</select></label><label>Relevance<select name="relevance"><option value="">All included items</option>${options(rows,"relevance")}</select></label><label>Provenance<select name="flags"><option value="">All listings</option><option value="flagged">With provenance flags</option></select></label><label>Result<select name="unknown"><option value="">All outcomes</option><option value="missing">No recorded outcome</option></select></label><label>Sale date from<input type="date" name="from"></label><label>Sale date to<input type="date" name="to"></label></form><p class="intelligence-count" aria-live="polite"></p><p class="intelligence-filter-help">Filters change the listings shown; they do not mark anything checked or approved.</p><div class="market-table-wrap"><table class="market-table"><thead><tr><th>Listing</th><th>House / platform</th><th>Sale / result</th><th>Price</th><th>Provenance</th></tr></thead><tbody></tbody></table></div><div class="intelligence-audit"><details><summary>Email item audit (${(data.dispositions || []).length} references)</summary><p>${escape(counts)}</p><ul>${(data.dispositions || []).map(d => `<li>${escape(d.title || "Untitled")} · ${escape(human(d.disposition))}${d.quoted ? " · quoted reference" : ""} · ${escape(d.reason)}</li>`).join("")}</ul></details>${(data.coverage || []).length ? `<details><summary>Page coverage</summary><ul>${data.coverage.map(c => `<li>${escape(c.url)} · ${escape(human(c.disposition))} · ${escape(c.observed_at)}</li>`).join("")}</ul></details>` : ""}</div>`;
    const form = container.querySelector("form");
    const candidates = data.reappearance_candidates || [];
    if (candidates.length) {
      const review = document.createElement("details");
      review.innerHTML = `<summary>Possible reappearances for your morning chat (${candidates.length})</summary><p>Ranking scores are heuristic, not probabilities. Shared wording or stock photographs can produce similarities.</p><ul>${candidates.map(c => `<li>${escape(c.listing_ids.map(id => rows.find(r => r.listing_id === id)?.title || id).join(" ↔ "))} · ranking ${escape(c.score.toFixed(2))} · ${escape(c.basis.join("; "))}</li>`).join("")}</ul>`;
      container.appendChild(review);
    }
    form.addEventListener("submit", e => e.preventDefault());
    const update = () => {
      const filtered = rows.filter(row => {
        for (const key of ["house","platform","relevance"]) if (form.elements[key].value && row[key] !== form.elements[key].value) return false;
        const date = row.sale_at?.slice(0,10) || (String(row.sale_date_text || "").match(/^\d{4}-\d{2}-\d{2}/) || [])[0];
        if (form.elements.from.value && (!date || date < form.elements.from.value)) return false;
        if (form.elements.to.value && (!date || date > form.elements.to.value)) return false;
        if (form.elements.flags.value && !(row.provenance_flags || []).length) return false;
        if (form.elements.unknown.value && ["sold","unsold","withdrawn"].includes(row.market_status)) return false;
        return true;
      });
      container.querySelector("tbody").innerHTML = filtered.map(display).join("");
      container.querySelector(".intelligence-count").textContent = `${filtered.length} of ${rows.length} listings shown.${form.elements.from.value || form.elements.to.value ? " Listings without a complete sale date are excluded from this range." : ""}`;
    };
    form.addEventListener("change", update);
    update();
  }
  window.MarketIntelligence = {mount};
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".market-intelligence").forEach(container => {
      const source = container.querySelector('script[type="application/json"]');
      if (source) mount(container, JSON.parse(source.textContent));
    });
  });
})();
