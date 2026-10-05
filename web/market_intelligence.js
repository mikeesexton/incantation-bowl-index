/* Mike-only operational intelligence view. Source strings are always escaped. */
(function () {
  "use strict";
  const escape = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const human = value => String(value || "unknown").replaceAll("_", " ");
  function options(rows, field) {
    return [...new Set(rows.map(r => r[field]).filter(Boolean))].sort().map(value => `<option value="${escape(value)}">${escape(human(value))}</option>`).join("");
  }
  function display(row) {
    const flags = (row.provenance_flags || []).map(f => human(f.flag)).join("; ");
    const matches = (row.corpus_matches || []).map(m => `${escape(m.object_id || m.appearance_id)}: ${escape(m.basis)} · ranking ${escape(m.score)}`).join("<br>");
    const fields = ["sale_name", "sale_number", "sale_id", "lot_number", "stock_number", "sale_timezone", "full_description", "description_scope", "language_stated", "script_stated", "dimensions_text", "condition_text", "provenance_text", "literature", "estimate_low", "estimate_high", "currency", "starting_bid", "asking_price", "hammer", "premium_total", "buyer_premium", "result_text", "quantity_text", "price_basis", "search_term", "keyword_hits", "source_email_ids", "image_urls", "notes"];
    const details = fields.filter(k => row[k] != null && row[k] !== "").map(k => `<dt>${escape(human(k))}</dt><dd style="white-space:pre-wrap">${escape(row[k])}</dd>`).join("");
    const evidence = (row.evidence || []).map(e => `<li>${escape(e.kind)} · ${escape(e.message_id || "page capture")} · ${escape(e.locator)} · ${escape(e.sha256.slice(0, 12))}</li>`).join("");
    const changes = (row.history || []).filter(h => h.changed).map(h => {
      const keys = Object.keys(h.current).filter(k => h.previous && JSON.stringify(h.previous[k]) !== JSON.stringify(h.current[k]) && (h.previous[k] != null || h.current[k] != null));
      return `<li>${escape(h.observed_at)}${h.new ? " · first observation" : ""}<ul>${keys.map(k => `<li>${escape(human(k))}: ${escape(JSON.stringify(h.previous[k]))} → ${escape(JSON.stringify(h.current[k]))}</li>`).join("")}</ul></li>`;
    }).join("");
    const price = [row.estimate && `estimate ${row.estimate}`, row.asking_price && `asking ${row.asking_price}`, row.hammer && `hammer ${row.hammer}`, row.premium_total && `including premium ${row.premium_total}`].filter(Boolean).join("; ") || "Not stated";
    return `<tr><td><a href="${escape(row.url)}" rel="noreferrer">${escape(row.title)}</a>${row.historical ? "<br><small>Historical correspondence</small>" : ""}<details><summary>Evidence and history</summary><dl>${details}</dl>${matches ? `<p>Matches awaiting Mike:<br>${matches}</p>` : ""}<ul>${evidence}</ul><ol>${changes}</ol></details></td><td>${escape(row.house || "Unknown")}<br><small>${escape(row.platform || "")}</small></td><td>${escape(row.sale_date_text || "Unknown")}<br><small>First seen ${escape(row.first_seen?.slice(0,10))}</small></td><td>${escape(human(row.market_status))}<br><small>${escape(human(row.relevance))}</small></td><td>${escape(price)}</td><td>${escape(flags)}</td></tr>`;
  }
  function mount(container, data) {
    const rows = data.listings || [];
    const counts = Object.entries(data.counts || {}).map(([k,v]) => `${human(k)}: ${v}`).join(" · ");
    container.innerHTML = `<h2>Auction alert intelligence</h2><p>${rows.length} listing leads from ${Object.keys(data.processed || {}).length} processed emails. Match suggestions await Mike's review.</p><form class="intelligence-filters" style="display:flex;flex-wrap:wrap;gap:.8rem"><label>House <select name="house"><option value="">All</option>${options(rows,"house")}</select></label><label>Platform <select name="platform"><option value="">All</option>${options(rows,"platform")}</select></label><label>Relevance <select name="relevance"><option value="">All</option>${options(rows,"relevance")}</select></label><label>Sale date from <input type="date" name="from"></label><label>to <input type="date" name="to"></label><label><input type="checkbox" name="flags"> Provenance flags</label><label><input type="checkbox" name="unknown"> Missing result</label></form><p class="intelligence-count"></p><div class="market-table-wrap" style="overflow:auto"><table class="market-table"><thead><tr><th>Listing</th><th>House/platform</th><th>Date</th><th>Status</th><th>Price wording</th><th>Flags</th></tr></thead><tbody></tbody></table></div><details><summary>Email item audit (${(data.dispositions || []).length} references)</summary><p>${escape(counts)}</p><ul>${(data.dispositions || []).map(d => `<li>${escape(d.title || "Untitled")} · ${escape(human(d.disposition))}${d.quoted ? " · quoted reference" : ""} · ${escape(d.reason)}</li>`).join("")}</ul></details>${(data.coverage || []).length ? `<details><summary>Page coverage</summary><ul>${data.coverage.map(c => `<li>${escape(c.url)} · ${escape(human(c.disposition))} · ${escape(c.observed_at)}</li>`).join("")}</ul></details>` : ""}`;
    const form = container.querySelector("form");
    const candidates = data.reappearance_candidates || [];
    if (candidates.length) {
      const review = document.createElement("details");
      review.innerHTML = `<summary>Possible reappearances awaiting Mike (${candidates.length})</summary><p>Ranking scores are heuristic, not probabilities. Shared wording or stock photographs can produce similarities.</p><ul>${candidates.map(c => `<li>${escape(c.listing_ids.map(id => rows.find(r => r.listing_id === id)?.title || id).join(" ↔ "))} · ranking ${escape(c.score.toFixed(2))} · ${escape(c.basis.join("; "))}</li>`).join("")}</ul>`;
      container.appendChild(review);
    }
    form.addEventListener("submit", e => e.preventDefault());
    const update = () => {
      const filtered = rows.filter(row => {
        for (const key of ["house","platform","relevance"]) if (form.elements[key].value && row[key] !== form.elements[key].value) return false;
        const date = row.sale_at?.slice(0,10) || (String(row.sale_date_text || "").match(/^\d{4}-\d{2}-\d{2}/) || [])[0];
        if (form.elements.from.value && (!date || date < form.elements.from.value)) return false;
        if (form.elements.to.value && (!date || date > form.elements.to.value)) return false;
        if (form.elements.flags.checked && !(row.provenance_flags || []).length) return false;
        if (form.elements.unknown.checked && ["sold","unsold","withdrawn"].includes(row.market_status)) return false;
        return true;
      });
      container.querySelector("tbody").innerHTML = filtered.map(display).join("");
      container.querySelector(".intelligence-count").textContent = `${filtered.length} of ${rows.length} leads shown. Dates are filtered only when the source supplies a complete date.`;
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
