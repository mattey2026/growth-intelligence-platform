/* Enterprise Growth Command Center: renderer core.
   RULE: this file renders a Dashboard Contract. It computes no business values: every value, delta, label and
   classification comes from the contract. Arithmetic here is presentation only (chart pixel scales, sorting). */
"use strict";
const C = JSON.parse(document.getElementById("gi-contract").textContent);
const D = C.dashboard, EV = Object.fromEntries(C.evidence.map(e => [e.id, e])), DRILL = C.drill;
const KEY = `gi:${D.tenant || "t"}:${D.id}:${D.entity_id}`;
const DEF = { view: C.state_defaults.view, persona: C.state_defaults.persona, filters: {}, theme: C.state_defaults.theme || "light", density: "comfortable",
  trend: "revenue", trendSeries: { actual: true, target: true, previous_year: true, forecast: true }, range: C.state_defaults.time_range || "24m",
  compare: "current_vs_previous", scenario: null, expanded: {}, saved: [] };
let S = Object.assign({}, DEF);
try { const raw = localStorage.getItem(KEY); if (raw) S = Object.assign({}, DEF, JSON.parse(raw)); } catch (e) { /* storage unavailable: defaults */ }
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
function h(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) n.addEventListener(k.slice(2), v); else if (k === "html") n.innerHTML = v; else if (k === "style" && typeof v === "object") { for (const [sk, sv] of Object.entries(v)) sk.startsWith("--") ? n.style.setProperty(sk, sv) : (n.style[sk] = sv); } else n.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat(9)) if (k != null && k !== false) n.append(k.nodeType ? k : document.createTextNode(String(k)));
  return n;
}
const SVGNS = "http://www.w3.org/2000/svg";
function s(tag, attrs = {}, ...kids) { const n = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(attrs)) { if (v == null) continue; if (k.startsWith("on")) n.addEventListener(k.slice(2), v); else n.setAttribute(k, v); } for (const k of kids.flat(9)) if (k != null) n.append(k.nodeType ? k : document.createTextNode(String(k))); return n; }
const sentCls = x => x === "positive" ? "pos" : x === "negative" ? "neg" : "neu";
const arrow = d => d === "up" ? "▲" : d === "down" ? "▼" : d === "flat" ? "▬" : "";
const ctag = t => t ? h("span", { class: "ct " + t, title: "Claim type" }, t === "DERIVED" ? "CALC" : t) : null;
function pv(ids, title) {
  ids = (ids || []).filter(Boolean); if (!ids.length) return null;
  return h("button", { class: "pv", title: `${ids.length} evidence item${ids.length > 1 ? "s" : ""}: open sources`, "aria-label": "Open evidence", "data-ev": ids.join(","),
    onclick: e => { e.stopPropagation(); openEvidence(ids, title || "Evidence"); } }, String(ids.length));
}
function conf(c) { if (c == null) return null; return h("span", { class: "conf", title: `Confidence ${Math.round(c * 100)}%` }, h("i", {}, h("b", { style: { width: Math.round(c * 100) + "%" } })), Math.round(c * 100) + "%"); }
const CAT = ["New Business", "Expansion", "Cross-sell", "Displacement", "Renewal", "Transformation"];
const RCAT = ["Customer", "Competitive", "Financial", "Market", "Pipeline", "Operational"];
const colorOf = (list, v) => `var(--c${(list.indexOf(v) % 6) + 1})`;
/* ---------- cross-filter (presentation: matches facets supplied by the contract) ---------- */
function match(o) {
  const f = Object.entries(S.filters); if (!f.length) return true;
  const fc = (o && o.facets) || {}; let rel = true;
  for (const [dim, val] of f) { if (!(dim in fc)) { rel = null; continue; } if (!fc[dim].includes(val)) return false; }
  return rel;
}
function setFilter(dim, val) { if (S.filters[dim] === val) delete S.filters[dim]; else S.filters[dim] = val; save(); render(); }
function clearFilters() { S.filters = {}; save(); render(); }
function filterLabel(dim, val) { const f = C.filters.find(x => x.dimension === dim); const v = f && f.values.find(x => x.value === val); return v ? v.label : val; }
/* ---------- drawer ---------- */
let trail = [];
function drawer(title, body, crumbs) {
  const d = $("#drawer"); d.innerHTML = "";
  d.append(h("div", { class: "dh" }, h("div", {}, crumbs || null, h("h3", { id: "drawer-title" }, title)),
    h("button", { class: "ib", "aria-label": "Close", onclick: closeDrawer, html: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>' })),
    h("div", { class: "db" }, body));
  d.classList.add("open"); d.setAttribute("aria-hidden", "false"); $("#scrim").classList.add("open"); d.querySelector(".ib").focus();
}
function closeDrawer() { $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); $("#scrim").classList.remove("open"); trail = []; }
function evCard(e) {
  if (!e) return null;
  return h("div", { class: "ev", "data-evid": e.id },
    h("div", { class: "ev-h" }, h("span", {}, ctag(e.claim_type), e.date || "undated"), conf(e.confidence)),
    h("div", {}, e.observation),
    h("dl", { class: "kv", style: { marginTop: "8px", marginBottom: 0 } },
      h("dt", {}, "Source"), h("dd", {}, e.source, e.data_mode === "public" ? h("span", { class: "pill Low", style: { marginLeft: "6px" } }, "Public source") : e.data_mode === "demo" ? h("span", { class: "pill Medium", style: { marginLeft: "6px" } }, "Demo") : null),
      e.historical_context ? [h("dt", {}, "Historical context"), h("dd", {}, e.historical_context)] : null,
      e.related_signals && e.related_signals.length ? [h("dt", {}, "Related signals"), h("dd", {}, e.related_signals.join(", "))] : null,
      e.related_opportunity ? [h("dt", {}, "Related opportunity"), h("dd", {}, h("button", { class: "btn", onclick: () => openDrill("D-opp-" + e.related_opportunity) }, e.related_opportunity))] : null,
      e.related_decision ? [h("dt", {}, "Related decision"), h("dd", {}, e.related_decision)] : null));
}
function openEvidence(ids, title) {
  const list = ids.map(i => EV[i]).filter(Boolean);
  drawer(title || "Evidence", [h("p", { class: "note" }, `${list.length} item${list.length === 1 ? "" : "s"}. Claim type, source, date and confidence are shown for each.`), list.map(evCard),
    list.length ? null : h("div", { class: "empty" }, "No evidence recorded for this item.")]);
  $("#drawer").dataset.kind = "evidence";
}
function openDrill(id, push = true) {
  const n = DRILL[id]; if (!n) return;
  if (push) { const i = trail.indexOf(id); trail = i >= 0 ? trail.slice(0, i + 1) : trail.concat(id); }
  const crumbs = h("div", { class: "crumbs" }, trail.slice(0, -1).map(t => [h("button", { onclick: () => openDrill(t) }, DRILL[t].label), " / "]));
  const kids = (n.children || []).map(c => DRILL[c]).filter(Boolean);
  const L = n.links || {};
  const body = [
    h("div", { class: "kpi-v num", style: { marginBottom: "4px" } }, n.display || ""),
    n.text ? h("p", { class: "note" }, n.text) : null,
    kids.length ? [h("div", { class: "sub" }, "Breakdown"), h("ul", { class: "rows", style: { border: "1px solid var(--line)", borderRadius: "3px" } },
      kids.map(k => h("li", { class: "click", "data-drill": k.id, onclick: () => openDrill(k.id) }, h("div", { class: "row-h" }, h("span", { class: "row-t" }, k.label), h("span", { class: "num" }, k.display || "")))))] : null,
    L.facet ? h("button", { class: "btn", style: { marginTop: "10px" }, onclick: () => { const [d, v] = Object.entries(L.facet)[0]; closeDrawer(); setFilter(d, v); } }, "Filter the dashboard by this") : null,
    L.signals && L.signals.length ? [h("div", { class: "sub" }, "Signals"), h("ul", { class: "rows" }, L.signals.map(id => C.signals.find(x => x.id === id)).filter(Boolean).map(sg => h("li", {}, h("div", { class: "row-h" }, h("span", {}, sg.label), pv(sg.evidence)), h("div", { class: "row-m" }, sg.timestamp, sg.domain))))] : null,
    L.threads && L.threads.length ? [h("div", { class: "sub" }, "Competitive threads"), L.threads.map(t => h("button", { class: "btn", style: { marginRight: "6px" }, onclick: () => openThread(t) }, (C.competitive_threads.find(x => x.id === t) || {}).label || t))] : null,
    L.actions && L.actions.length ? [h("div", { class: "sub" }, "Action"), L.actions.map(a => actionRow(C.actions.find(x => x.id === a)))] : null,
    L.thread ? h("button", { class: "btn", style: { marginTop: "10px" }, onclick: () => openThread(L.thread) }, "Open thread timeline") : null,
    (n.evidence || []).length ? [h("div", { class: "sub" }, "Evidence"), n.evidence.map(e => evCard(EV[e]))] : null];
  drawer(n.label, body, crumbs); $("#drawer").dataset.kind = "drill"; $("#drawer").dataset.node = id;
}
/* ---------- Ask Intelligence: UI navigation + hand-off to the Business Orchestrator (no local reasoning) ---------- */
// Order matters: scenario questions first, then word-bounded keywords ("new" must not match inside "renewal").
const ROUTES = [[/what happens|what if|\bscenario/i, { view: "decisions", focus: "scenario_lab" }], [/\bchang|\bnew\b|last 30/i, { view: "overview", focus: "changes" }], [/competi|gaining|threat|thread/i, { view: "competition", focus: "threads" }],
  [/evidence|source|prove/i, { evidence: true }], [/should i do|next|action/i, { view: "actions", focus: "actions" }],
  [/financial signal/i, { filter: { domain: "financial" } }], [/warming|marketing|campaign|pipeline from/i, { view: "marketing", focus: "marketing_summary" }],
  [/opportunit|growth potential|biggest/i, { view: "growth", focus: "radar" }], [/why .*growth|growth change/i, { view: "overview", focus: "trend" }]];
function ask(q, capability) {
  q = (q || "").trim(); if (!q) return;
  if (!capability) { const k = C.queries.find(x => x.question === q); capability = k && k.capability; }
  let r = null; const known = C.queries.find(x => x.question.toLowerCase() === q.toLowerCase());
  if (known && known.ui_target) r = known.ui_target; else for (const [re, t] of ROUTES) if (re.test(q)) { r = t; break; }
  if (r) uiTarget(r);
  const ctx = `[Growth Intelligence dashboard: ${D.entity_name} · persona ${S.persona} · view ${S.view}${capability ? " · capability " + capability : ""}${Object.keys(S.filters).length ? " · filters " + JSON.stringify(S.filters) : ""}] `;
  const msg = ctx + q;
  if (typeof window.sendPrompt === "function") { window.sendPrompt(msg); toast("Sent to the Business Orchestrator."); }
  else if (window.claude && typeof window.claude.ask === "function") { toast("Sent to the Business Orchestrator."); window.claude.ask(msg); }
  else {
    // Clipboard writes are asynchronous and may be refused (permissions, locked-down browsers): never claim a copy that failed.
    const ok = () => toast("Question copied with dashboard context. Paste it into your Claude conversation: the Business Orchestrator answers and refreshes this dashboard.");
    const fail = () => toast("Copy this into your Claude conversation: " + msg);
    try { (navigator.clipboard && navigator.clipboard.writeText) ? navigator.clipboard.writeText(msg).then(ok, fail) : fail(); } catch (e) { fail(); }
  }
  document.body.dataset.lastAsk = msg;
}
function uiTarget(t) {
  if (t.filter) { S.filters = Object.assign({}, S.filters, t.filter); }
  if (t.view && C.navigation.some(n => n.id === t.view)) S.view = t.view;
  save(); render();
  if (t.focus) { const w = $(`[data-widget="${t.focus}"]`); if (w) { w.scrollIntoView({ block: "start", behavior: "instant" }); w.classList.add("flash"); setTimeout(() => w.classList.remove("flash"), 1400); } }
  if (t.evidence) { const d = $("#drawer"); if (d.classList.contains("open") && d.dataset.node && DRILL[d.dataset.node]) openEvidence(DRILL[d.dataset.node].evidence, "Evidence"); else openEvidence(C.narrative.summary.flatMap(x => x.evidence).slice(0, 8), "Evidence behind the summary"); }
}
/* ---------- Explore capabilities (starter prompts from the contract's discovery block) ---------- */
function openExplore(cat) {
  const X = C.discovery; if (!X) return;
  const cats = X.explore.filter(e => e.capabilities.length);
  const sel = cat || cats[0].category;
  const card = (p, cap) => h("button", { class: "pcard", "data-prompt": p, onclick: () => { closeDrawer(); ask(p, cap); } }, h("span", { class: "pc-ic", "aria-hidden": "true" }, "▶"), h("span", {}, p));
  drawer("Explore capabilities", [
    h("p", { class: "note" }, "Choose what you want to accomplish. Prompts run in the current context (" + D.entity_name + ")."),
    h("div", { class: "seg", style: { flexWrap: "wrap", marginBottom: "10px" } }, cats.map(e => h("button", { "aria-pressed": String(e.category === sel), "data-explore": e.category, onclick: () => openExplore(e.category) }, e.category))),
    cats.find(e => e.category === sel).capabilities.map(cn => { const m = X.menus[cn];
      return h("div", { class: "ev", "data-capability": cn }, h("div", { class: "row-t" }, cn), h("div", { class: "note", style: { marginBottom: "6px" } }, m.description), m.prompts.map(p => card(p, cn))); })]);
  $("#drawer").dataset.kind = "explore";
}
function toast(t) { const n = $("#toast"); n.textContent = t; n.style.display = "block"; clearTimeout(toast._t); toast._t = setTimeout(() => n.style.display = "none", 5200); }
/* ---------- tooltip ---------- */
function tip(e, text) { const t = $("#tip"); if (!text) { t.style.display = "none"; return; } t.textContent = text; t.style.display = "block"; t.style.left = Math.min(e.clientX + 12, innerWidth - 310) + "px"; t.style.top = (e.clientY + 12) + "px"; }
