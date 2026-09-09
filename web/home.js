/* A local-only introduction. It consumes presence flags, not text or media content. */
(() => {
  "use strict";
  const root = document.querySelector("#home-view");
  const find = selector => root.querySelector(selector);
  const all = selector => [...root.querySelectorAll(selector)];
  const number = value => value.toLocaleString();
  const labels = {all: "All bowls", text_edition: "Text references",
    provenance: "Collection history", image: "Image references"};
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const desktop = matchMedia("(min-width: 701px)");
  let snapshot = null, request = 0, active = "all", lastScrollStep = null, frame = 0;
  let chartObserver = null;

  function animateYear(date, delay) {
    const firstYear = 750;
    const lastYear = Number(date.dataset.year);
    const duration = 3200;
    date.textContent = String(firstYear);
    window.setTimeout(() => {
      const started = performance.now();
      const tick = now => {
        const progress = Math.min(1, (now - started) / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        date.textContent = String(Math.round(firstYear + (lastYear - firstYear) * eased));
        if (progress < 1) window.requestAnimationFrame(tick);
      };
      window.requestAnimationFrame(tick);
    }, delay);
  }

  // Visual state is independent of the data request, including when it fails.
  function updateBrowsePosition() {
    const heroButton = find(".intro-hero .intro-button");
    const headerButton = document.querySelector(".intro-browse-link");
    if (!heroButton?.getBoundingClientRect || !headerButton) return;
    const passed = heroButton.getBoundingClientRect().bottom <= 100;
    headerButton.classList.toggle("is-docked", passed);
    headerButton.inert = !passed;
    headerButton.setAttribute("aria-hidden", String(!passed));
  }

  function setupMotion() {
    const dates = all("[data-year]");
    if (reducedMotion.matches || !("IntersectionObserver" in window)) {
      dates.forEach(date => { date.textContent = date.dataset.year; });
      return;
    }
    dates.forEach(date => { date.textContent = "750"; });
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in-view");
        if (entry.target.classList.contains("intro-milestones")) {
          dates.forEach((date, index) => animateYear(date, index * 280));
        }
        observer.unobserve(entry.target);
      });
    }, {threshold: .18});
    all(".intro-milestones, .intro-map, .intro-section-heading, .intro-finale h2").forEach(node => observer.observe(node));
  }
  setupMotion();
  window.addEventListener("scroll", updateBrowsePosition, {passive: true});
  window.addEventListener("resize", updateBrowsePosition, {passive: true});

  function setCoverage(field) {
    if (!snapshot || !(field in labels)) return;
    active = field;
    all("[data-coverage]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.coverage === field)));
    all(".intro-circle").forEach((circle, index) => {
      circle.classList.toggle("is-softened", field !== "all" && !snapshot.identities[index][field]);
    });
    const count = field === "all" ? snapshot.identity_count : snapshot.coverage[field];
    const percent = snapshot.identity_count ? (100 * count / snapshot.identity_count).toFixed(1) : "0.0";
    const description = `${labels[field]}: ${number(count)} of ${number(snapshot.identity_count)} (${percent}%).`;
    find("#intro-selection").textContent = description;
    find("#intro-field-desc").textContent = `${description} Each circle represents one bowl. Lighter circles have no reference of this kind in the index.`;
  }

  function renderField() {
    const rows = snapshot.identities;
    const cols = Math.max(1, Math.ceil(Math.sqrt(rows.length * 1.5)));
    const height = Math.max(60, Math.ceil(rows.length / cols) * 13 + 16);
    const width = cols * 13 + 16;
    const svg = find("#intro-circle-field");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.querySelector("g")?.remove();
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("aria-hidden", "true");
    const fragment = document.createDocumentFragment();
    rows.forEach((row, index) => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", 14 + index % cols * 13);
      circle.setAttribute("cy", 14 + Math.floor(index / cols) * 13);
      circle.setAttribute("r", "4.2");
      circle.setAttribute("class", "intro-circle");
      circle.dataset.bowlIdentity = row.identity_id;
      fragment.append(circle);
    });
    group.append(fragment); svg.append(group);
    find("#intro-total").textContent = number(snapshot.identity_count);
    find("#intro-identity-count").textContent = number(snapshot.identity_count);
    find("#intro-record-count").textContent = number(snapshot.source_record_count);
    all("[data-count]").forEach(element => {
      const count = snapshot.coverage[element.dataset.count];
      const percent = snapshot.identity_count ? (100 * count / snapshot.identity_count).toFixed(1) : "0.0";
      element.innerHTML = `${number(count)} <span> / ${number(snapshot.identity_count)}</span><small>${percent}% of bowls</small>`;
    });
    all("[data-coverage]").forEach(button => { button.disabled = false; });
    setCoverage(active);
  }

  function renderChart() {
    chartObserver?.disconnect();
    const source = snapshot.scholarship.decades;
    const current = Math.floor(snapshot.snapshot.current_year / 10) * 10;
    const years = source.map(row => row.decade);
    const start = Math.min(current, ...years);
    const end = Math.max(current, ...years);
    const byDecade = new Map(source.map(row => [row.decade, row]));
    const rows = [];
    for (let decade = start; decade <= end; decade += 10) {
      rows.push(byDecade.get(decade) || {decade, indexed: 0, incomplete: decade === current});
    }
    const max = Math.max(1, ...rows.map(row => row.indexed));
    const ceiling = Math.max(5, Math.ceil(max / 5) * 5);
    const width = 1000, left = 44, right = 16, top = 28, baseline = 278;
    const step = (width - left - right) / rows.length;
    const barWidth = Math.min(42, step * .65);
    const grid = Array.from({length: 6}, (_, i) => {
      const value = ceiling * i / 5, y = baseline - (baseline - top) * i / 5;
      return `<line x1="${left}" y1="${y}" x2="984" y2="${y}" stroke="#c9bfad" stroke-width=".7"/><text x="31" y="${y + 4}" text-anchor="end">${value}</text>`;
    }).join("");
    const bars = rows.map((row, index) => {
      const x = left + step * index + step / 2;
      const height = row.indexed / ceiling * (baseline - top);
      const showLabel = index % Math.max(1, Math.ceil(rows.length / 9)) === 0 || index === rows.length - 1;
      return `<g><title>${row.decade}s: ${row.indexed} indexed publications${row.incomplete ? "; current decade, incomplete" : ""}</title><rect class="intro-bar intro-bar-${index + 1}${row.incomplete ? " intro-bar-current" : ""}" x="${x - barWidth / 2}" y="${baseline - height}" width="${barWidth}" height="${height}"/>${row.indexed ? `<text x="${x}" y="${baseline - height - 9}" text-anchor="middle">${row.indexed}</text>` : ""}${showLabel ? `<text x="${x}" y="307" text-anchor="middle">${row.decade}${row.incomplete ? "*" : ""}</text>` : ""}</g>`;
    }).join("");
    find("#intro-chart").innerHTML = `<svg class="intro-chart-svg" viewBox="0 0 1000 330" role="img" aria-labelledby="intro-chart-title intro-chart-desc"><title id="intro-chart-title">Scholarly publications indexed, by decade</title><desc id="intro-chart-desc">${rows.map(row => `${row.decade}s: ${row.indexed}`).join("; ")}. The current decade is incomplete. Exact values are also available in the table.</desc><defs><pattern id="intro-current-decade" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#5d4939"/><path d="M-1 1l8 8M5-1l3 3" stroke="#d9954f" stroke-width="2"/></pattern></defs>${grid}${bars}</svg>`;
    find("#intro-chart-data").innerHTML = `<table><caption>Indexed publications; current decade marked incomplete</caption><thead><tr><th scope="col">Decade</th><th scope="col">Publications</th></tr></thead><tbody>${rows.map(row => `<tr><th scope="row">${row.decade}s${row.incomplete ? " (incomplete)" : ""}</th><td>${number(row.indexed)}</td></tr>`).join("")}</tbody></table>`;
    find("#intro-decade-note").textContent = `* ${current}s: current decade, incomplete. ${number(snapshot.scholarship.undated_count)} undated works excluded.`;
    if (!reducedMotion.matches && "IntersectionObserver" in window) {
      const svg = find(".intro-chart-svg");
      chartObserver = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          svg.classList.add("is-revealing"); chartObserver.disconnect();
        }
      }, {threshold: .25});
      chartObserver.observe(svg);
    }
  }

  async function load() {
    const version = ++request;
    find("#intro-data-status").textContent = "Loading the collection…";
    find("#intro-data-status").classList.remove("is-error");
    try {
      const response = await fetch("/api/introduction");
      if (!response.ok) throw new Error("Introduction unavailable");
      const data = await response.json();
      if (version !== request) return;
      if (!Array.isArray(data.identities) || data.identities.length !== data.identity_count) throw new Error("Invalid snapshot");
      snapshot = data;
      renderField(); renderChart();
      const date = new Date(data.snapshot.loaded_at).toLocaleDateString(undefined, {month: "short", day: "numeric", year: "numeric"});
      find("#intro-data-status").textContent = data.identity_count ? `Local snapshot · ${date} · counts reflect the current index` : "This snapshot has no bowl identities yet. The database is still available below.";
      find("#intro-snapshot-note").textContent = `Local snapshot · ${date} · ${data.snapshot.id.slice(0, 8)}`;
      lastScrollStep = null; onScroll();
    } catch {
      if (version !== request) return;
      find("#intro-data-status").classList.add("is-error");
      find("#intro-data-status").innerHTML = `The introductory counts could not be loaded. <a href="#/explore">Browse the database</a> or <button type="button" id="intro-retry">Try again</button>.`;
      find("#intro-retry").addEventListener("click", load);
      if (!snapshot) {
        find("#intro-chart").textContent = "Publication history is temporarily unavailable.";
        find("#intro-chart-data").textContent = "Publication counts are temporarily unavailable.";
        find("#intro-selection").textContent = "Coverage counts are temporarily unavailable.";
      }
    }
  }

  function onScroll() {
    if (frame || !snapshot || !root.classList.contains("is-active") || !desktop.matches) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      const steps = all("[data-step]");
      const target = innerHeight * .52;
      const visible = steps.filter(step => {
        const box = step.getBoundingClientRect();
        return box.bottom > 100 && box.top < innerHeight;
      });
      if (!visible.length) return;
      const closest = visible.reduce((a, b) =>
        Math.abs(a.getBoundingClientRect().top + a.offsetHeight / 2 - target) <
        Math.abs(b.getBoundingClientRect().top + b.offsetHeight / 2 - target) ? a : b);
      // Manual buttons remain selected until scrolling reaches a different chapter.
      if (closest.dataset.step !== lastScrollStep) {
        lastScrollStep = closest.dataset.step;
        setCoverage(lastScrollStep);
      }
    });
  }
  all("[data-coverage]").forEach(button => button.addEventListener("click", () => setCoverage(button.dataset.coverage)));
  all("[data-intro-scroll]").forEach(button => button.addEventListener("click", event => {
    event.preventDefault();
    const section = document.getElementById(button.dataset.introScroll);
    section.scrollIntoView({behavior: reducedMotion.matches ? "instant" : "smooth", block: "start"});
    section.setAttribute("tabindex", "-1"); section.focus({preventScroll: true});
  }));
  window.addEventListener("scroll", onScroll, {passive: true});
  window.addEventListener("resize", onScroll, {passive: true});
  window.Introduction = {
    render() { updateBrowsePosition(); if (!snapshot) return load(); onScroll(); },
    invalidate() {
      snapshot = null; request++; chartObserver?.disconnect();
      all("[data-coverage]").forEach(button => { button.disabled = true; });
      find("#intro-circle-field g")?.remove();
      find("#intro-total").textContent = "—";
      find("#intro-record-count").textContent = "—";
      find("#intro-identity-count").textContent = "—";
      all("[data-count]").forEach(node => { node.textContent = "—"; });
      find("#intro-chart").textContent = "Loading the publication history…";
      find("#intro-chart-data").textContent = "Loading publication counts…";
      find("#intro-snapshot-note").textContent = "Local collection · snapshot refresh pending";
      find("#intro-decade-note").textContent = "";
      find("#intro-selection").textContent = "Loading the collection…";
      find("#intro-field-desc").textContent = "Coverage snapshot refresh pending.";
    },
  };
})();
