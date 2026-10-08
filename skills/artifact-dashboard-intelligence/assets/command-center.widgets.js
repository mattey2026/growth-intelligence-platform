/* Widgets: each draws one contract section. No business computation. */
function nice(max, n = 4) { if (!(max > 0)) return [0, 1]; const raw = max / n, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p; const st = (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p; const out = []; for (let v = 0; v <= max + st * 0.01; v += st) out.push(+v.toFixed(10)); if (out[out.length - 1] < max) out.push(out[out.length - 1] + st); return out; }
const FMT = { money: v => "$" + v.toFixed(v >= 100 ? 0 : 1) + "M", pct: v => (v * 100).toFixed(Math.abs(v) < 0.1 ? 1 : 0) + "%", num: v => String(+v.toFixed(2)), pp: v => v.toFixed(1) + "pp" };
function widthOf(el) { return Math.max(260, Math.floor(el.getBoundingClientRect().width || 600)); }
function lineChart(box, series, opt) {
  const W = widthOf(box), H = opt.h || 260, m = { l: 52, r: 16, t: 14, b: 26 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const xs = [...new Set(series.flatMap(s_ => s_.points.map(p => p.t)))].sort();
  const vals = series.flatMap(s_ => s_.points.map(p => p.v)); const vmin = Math.min(...vals), hi = Math.max(...vals);
  // Line charts use a data-fitted baseline (labelled on the axis) so changes stay legible; zero is kept when data crosses it.
  const span_ = (hi - vmin) || Math.abs(hi) || 1; let lo = vmin < 0 ? vmin - span_ * 0.1 : Math.max(0, vmin - span_ * 0.35);
  const st0 = nice(hi - lo, 4); const stepv = st0[1] - st0[0]; lo = Math.floor(lo / stepv) * stepv;
  const ticks = []; for (let v = lo; v <= hi + stepv * 0.999; v += stepv) ticks.push(+v.toFixed(8));
  const y0 = ticks[0], y1 = ticks[ticks.length - 1];
  const X = t => m.l + (xs.length === 1 ? iw / 2 : xs.indexOf(t) / (xs.length - 1) * iw), Y = v => m.t + ih - (v - y0) / (y1 - y0 || 1) * ih;
  const f = FMT[opt.fmt] || FMT.num;
  const svg = s("svg", { class: "ch", viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opt.label || "chart" });
  ticks.forEach(v => { svg.append(s("line", { class: "gl", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }), s("text", { x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, f(v))); });
  const step = Math.ceil(xs.length / Math.max(2, Math.floor(iw / 70)));
  xs.forEach((t, i) => { if (i % step === 0 || i === xs.length - 1) svg.append(s("text", { x: X(t), y: H - 6, "text-anchor": "middle" }, t)); });
  (opt.annotations || []).forEach(a => { if (!xs.includes(a.t)) return; const x = X(a.t);
    svg.append(s("line", { x1: x, x2: x, y1: m.t, y2: m.t + ih, stroke: "var(--warn)", "stroke-dasharray": "3 3" }),
      s("circle", { class: "mark", cx: x, cy: m.t + 5, r: 5, fill: "var(--surface)", stroke: "var(--warn)", "stroke-width": 1.5, "data-annot": a.t,
        onclick: () => openEvidence([a.evidence], a.label), onmousemove: e => tip(e, a.t + ": " + a.label), onmouseleave: e => tip(e) })); });
  const STY = { actual: { c: "var(--accent)", w: 2 }, target: { c: "var(--slate)", w: 1.25, d: "5 4" }, previous_year: { c: "var(--faint)", w: 1.25 }, forecast: { c: "var(--c3)", w: 2, d: "2 3" }, prior_forecast: { c: "var(--c4)", w: 1.5, d: "4 3" } };
  series.forEach(sr => { const st = STY[sr.name] || { c: "var(--c2)", w: 1.5 }; const d = sr.points.map((p, i) => (i ? "L" : "M") + X(p.t).toFixed(1) + " " + Y(p.v).toFixed(1)).join(" ");
    svg.append(s("path", { d, fill: "none", stroke: st.c, "stroke-width": st.w, "stroke-dasharray": st.d || null, "data-series": sr.name }));
    sr.points.forEach(p => svg.append(s("circle", { cx: X(p.t), cy: Y(p.v), r: 7, fill: "transparent", onmousemove: e => tip(e, `${sr.name.replace("_", " ")} · ${p.t}: ${f(p.v)}`), onmouseleave: e => tip(e) }))); });
  return svg;
}
function scatter(box, pts, opt) {
  const W = widthOf(box), H = opt.h || 300, m = { l: 52, r: 18, t: 12, b: 34 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const ymax = opt.ymax || Math.max(...pts.map(p => p.y)) * 1.1, yt = opt.yticks || nice(ymax); const Y1 = yt[yt.length - 1];
  const X = v => m.l + v * iw, Y = v => m.t + ih - v / Y1 * ih;
  const svg = s("svg", { class: "ch", viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": opt.label });
  if (opt.quadrants) { svg.append(s("rect", { x: X(0.5), y: m.t, width: iw / 2, height: ih / 2, fill: "var(--risk-soft)", opacity: 0.55 })); }
  yt.forEach(v => svg.append(s("line", { class: "gl", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }), s("text", { x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, opt.yfmt(v))));
  [0, .25, .5, .75, 1].forEach(v => svg.append(s("line", { class: "gl", x1: X(v), x2: X(v), y1: m.t, y2: m.t + ih }), s("text", { x: X(v), y: m.t + ih + 14, "text-anchor": "middle" }, Math.round(v * 100) + "%")));
  svg.append(s("text", { x: m.l + iw / 2, y: H - 2, "text-anchor": "middle", style: "fill:var(--ink-2)" }, opt.xlab), s("text", { x: 12, y: m.t + ih / 2, transform: `rotate(-90 12 ${m.t + ih / 2})`, "text-anchor": "middle", style: "fill:var(--ink-2)" }, opt.ylab));
  const placed = [], circles = pts.map(p => ({ x: X(p.x), y: Y(p.y), r: p.r }));
  const hits = (bx) => placed.some(q => !(bx.x2 < q.x1 || bx.x1 > q.x2 || bx.y2 < q.y1 || bx.y1 > q.y2)) ||
    circles.some(c => c.x + c.r > bx.x1 && c.x - c.r < bx.x2 && c.y + c.r > bx.y1 && c.y - c.r < bx.y2 && !(bx.own && c.x === bx.own.x && c.y === bx.own.y)) || bx.x1 < m.l || bx.x2 > W - m.r;
  const labelPos = p => { if (!p.label) return null; const cx = X(p.x), cy = Y(p.y), w = p.label.length * 6.1, own = { x: cx, y: cy };
    const cands = [[cx + p.r + 3, cy + 4], [cx - p.r - 3 - w, cy + 4], [cx - w / 2, cy - p.r - 5], [cx - w / 2, cy + p.r + 13]];   // right, left, above, below
    for (const [x1, by] of cands) { const bx = { x1, x2: x1 + w, y1: by - 11, y2: by + 2, own };
      if (!hits(bx)) { placed.push(bx); return { x: x1, y: by }; } } return null; };
  pts.sort((a, b) => b.r - a.r).forEach(p => { const g = s("g", { class: "mark" + (p.dim ? " dim" : ""), "data-id": p.id, tabindex: 0, role: "button", "aria-label": p.tip,
      onclick: () => p.onclick(), onkeydown: e => { if (e.key === "Enter") p.onclick(); }, onmousemove: e => tip(e, p.tip), onmouseleave: e => tip(e) });
    g.append(s("circle", { cx: X(p.x), cy: Y(p.y), r: p.r, fill: p.color, "fill-opacity": 0.22, stroke: p.color, "stroke-width": 1.5 }));
    const lp = labelPos(p); if (lp) g.append(s("text", { x: lp.x, y: lp.y, style: "fill:var(--ink-2);font-size:11px", "data-label": p.id }, p.label));
    svg.append(g); });
  return svg;
}
function spark(vals, w = 72, h = 20) { if (!vals || vals.length < 2) return null; const lo = Math.min(...vals), hi = Math.max(...vals), r = hi - lo || 1;
  return s("svg", { width: w, height: h, viewBox: `0 0 ${w} ${h}`, class: "spark", "aria-hidden": "true" }, s("path", { d: vals.map((v, i) => (i ? "L" : "M") + (i / (vals.length - 1) * (w - 2) + 1).toFixed(1) + " " + (h - 2 - (v - lo) / r * (h - 4)).toFixed(1)).join(" "), fill: "none", stroke: "var(--slate)", "stroke-width": 1.25 })); }
function legend(items, onToggle) { return h("div", { class: "lg" }, items.map(it => h("button", { class: it.off ? "off" : "", "aria-pressed": String(!it.off), onclick: () => onToggle && onToggle(it.key) }, h("i", { style: { background: it.color } }), it.label))); }
/* ---------- widgets ---------- */
const WIDGETS = {
 kpi_strip(w) {
  const fdim = Object.keys(S.filters)[0], fval = S.filters[fdim];
  const kp = personaLayout().kpis.map(id => C.metrics.find(m => m.id === id)).filter(Boolean);
  return h("div", { class: "kpis", style: { gridTemplateColumns: `repeat(${Math.min(kp.length, 9)},minmax(0,1fr))` } }, kp.map(m => {
    const sub = fdim && m.by_facet && m.by_facet[fdim] ? m.by_facet[fdim][fval] || { display: m.unit === "ratio" ? "—" : "$0.0M" } : null;
    const dim = fdim && !sub;
    return h("button", { class: "kpi" + (dim ? " dim" : ""), "data-kpi": m.id, title: dim ? `Not split by ${fdim}` : m.note || m.label, onclick: () => openDrill(m.drill_down_target) },
      h("div", { class: "kpi-l" }, m.label), h("div", { class: "kpi-v num" }, sub ? sub.display : m.display),
      sub ? h("div", { class: "kpi-p" }, `Filtered: ${filterLabel(fdim, fval)} · total ${m.display}`) :
        [h("div", { class: "kpi-d " + sentCls(m.sentiment) }, h("span", {}, arrow(m.direction)), h("span", { class: "num" }, m.delta_display || "—")),
         h("div", { class: "kpi-p num" }, "vs " + (m.previous_display || "—"))],
      h("div", { class: "kpi-f" }, spark(m.trend), h("span", {}, conf(m.confidence), pv(m.evidence, m.label))));
  }));
 },
 narrative() {
  const N = C.narrative;
  return h("div", { class: "state" },
    h("div", { class: "state-sum" }, N.summary.filter(x => match(x) !== false).map(x => h("p", {}, ctag(x.claim_type), x.text, pv(x.evidence))), h("p", { class: "note" }, N.method)),
    h("div", { class: "mv" }, h("h4", { class: "pos" }, "Positive movements"), N.positive.length ? null : h("p", { class: "note" }, "None yet: needs a previous snapshot."), h("ul", {}, N.positive.map(x => h("li", {}, h("span", {}, x.text, pv(x.evidence)), h("span", { class: "pos num" }, x.delta_display || ""))))),
    h("div", { class: "mv state-neg" }, h("h4", { class: "neg" }, "Negative movements"), N.negative.length ? null : h("p", { class: "note" }, "None yet: needs a previous snapshot."), h("ul", {}, N.negative.map(x => h("li", {}, h("span", {}, x.text, pv(x.evidence)), h("span", { class: "neg num" }, x.delta_display || ""))))));
 },
 change_list() {
  if (!C.changes.length) return h("div", { class: "empty", style: { margin: "12px 16px" } }, "No changes yet. What changed appears after the second refresh, when there is a previous snapshot to compare with.");
  const doms = [...new Set(C.changes.map(c => c.domain))];
  const items = C.changes.filter(c => match(c) !== false);
  const t = h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Domain", "Change", "Previous", "Current", "Delta", "Date", "Confidence", "Source"].map((x, i) => h("th", { class: i >= 2 && i <= 4 ? "r" : "" }, x)))),
    h("tbody", {}, items.map(c => h("tr", { class: "click" + (match(c) === null ? " dimmed" : ""), "data-change": c.id, onclick: () => openDrill(c.drill_down_target) },
      h("td", {}, h("button", { class: "btn", style: { height: "22px" }, onclick: e => { e.stopPropagation(); setFilter("domain", c.domain); } }, c.domain)),
      h("td", { style: { whiteSpace: "normal", minWidth: "220px" } }, c.label, " ", c.change_type !== "changed" ? h("span", { class: "pill " + (c.change_type === "contradictory" ? "High" : "None") }, c.change_type) : null),
      h("td", { class: "r num" }, c.previous_display ?? "—"), h("td", { class: "r num" }, c.display ?? "—"),
      h("td", { class: "r num " + sentCls(c.sentiment) }, c.delta_display ? arrow(c.direction) + " " + c.delta_display : ""), h("td", { class: "num" }, (c.date || "").slice(0, 10)),
      h("td", {}, conf(c.confidence)), h("td", { style: { maxWidth: "260px", overflow: "hidden", textOverflow: "ellipsis" }, title: c.source }, pv(c.evidence), " ", c.source)))));
  return [h("div", { class: "tbl-tools" }, h("span", { class: "note" }, `${items.length} of ${C.changes.length} changes since the previous snapshot · domains: ${doms.join(", ")}`)), h("div", { class: "tw" }, t)];
 },
 trend_chart(w, box) {
  if (!C.trends || !C.trends.length) return h("div", { class: "empty" }, "No time series yet. Monthly billing and CRM history (at least 24 months) populates revenue, growth, pipeline, bookings and margin trends.");
  const T = C.trends.find(t => t.id === S.trend) || C.trends[0];
  const n = S.range === "12m" ? 12 : 99;
  const all = T.series.map(sr => ({ name: sr.name, points: sr.points.slice(-Math.max(n, sr.name === "forecast" ? 3 : n)) })).filter(sr => S.trendSeries[sr.name] !== false);
  const body = h("div", {});
  const hdr = h("div", { style: { display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "8px", marginBottom: "8px" } },
    h("div", { class: "seg", role: "group", "aria-label": "Metric" }, C.trends.map(t => h("button", { "aria-pressed": String(t.id === T.id), "data-trend": t.id, onclick: () => { S.trend = t.id; save(); render(); } }, t.label.split(" (")[0]))),
    h("div", { class: "seg" }, ["12m", "24m"].map(r => h("button", { "aria-pressed": String(S.range === r), onclick: () => { S.range = r; save(); render(); } }, r === "12m" ? "12 months" : "24 months"))));
  const lg = legend(T.series.map(sr => ({ key: sr.name, label: sr.name.replace("_", " "), color: { actual: "var(--accent)", target: "var(--slate)", previous_year: "var(--faint)", forecast: "var(--c3)", prior_forecast: "var(--c4)" }[sr.name], off: S.trendSeries[sr.name] === false })),
    k => { S.trendSeries[k] = S.trendSeries[k] === false; save(); render(); });
  body.append(hdr, lg);
  requestAnimationFrame(() => { const holder = $("#trend-holder"); if (holder) holder.append(lineChart(holder, all, { fmt: T.format, annotations: T.annotations, label: T.label + " trend", h: 250 })); });
  body.append(h("div", { id: "trend-holder", style: { marginTop: "8px" } }), h("div", { class: "note" }, "Dashed markers are material events; select one for its evidence.", pv(T.evidence)));
  return body;
 },
 driver_tree() {
  const R = C.drivers;
  if (!R || R.available === false || !R.children || !R.children.length) return h("div", { class: "empty" }, "Growth drivers are not available: needs " + ((R && R.needs) || "incremental growth values per opportunity") + ".");
  const mx = Math.max(...R.children.map(c => c.value), 0.0001);
  return [h("div", { class: "dt-root" }, h("span", { class: "row-t" }, R.label), h("button", { class: "btn num", onclick: () => openDrill(R.drill_down_target) }, R.display)),
    h("ul", { class: "dt" }, R.children.map(c => h("li", {}, h("button", { "data-driver": c.label, "aria-pressed": String(S.filters.driver === c.label), onclick: () => setFilter("driver", c.label) },
      h("span", {}, c.label), h("span", { class: "bar-t" }, h("b", { style: { width: (c.value / mx * 100) + "%" } })), h("span", { class: "num", style: { textAlign: "right" } }, c.display))))),
    h("p", { class: "note" }, "Select a driver to filter the dashboard; open the total for the full breakdown.")];
 },
 opportunity_radar(w, box) {
  const holder = h("div", {});
  const mx = Math.max(...C.opportunities.map(o => o.value));
  requestAnimationFrame(() => { const el = $("#radar-" + w.id); if (!el) return;
    el.append(scatter(el, C.opportunities.map(o => ({ id: o.id, x: o.probability, y: o.value, r: o.strategic_impact == null ? 8 : 6 + o.strategic_impact * 16, color: o.category === "Unclassified" ? "var(--neutral)" : colorOf(CAT, o.category), dim: match(o) === false || match(o) === null,
      label: [...C.opportunities].sort((a, b) => b.value * (b.strategic_impact ?? 0.5) - a.value * (a.strategic_impact ?? 0.5)).slice(0, 4).some(x => x.id === o.id) ? (o.label.length > 30 ? o.label.slice(0, 29) + "…" : o.label) : null, tip: `${o.label} · ${o.display} · ${o.probability_display} · ${o.category}${o.strategic_impact == null ? " · strategic impact not recorded" : ""}`, onclick: () => openDrill(o.drill_down_target) })),
      { h: 300, ymax: mx * 1.12, yfmt: v => "$" + v + "M", xlab: "Probability", ylab: "Value ($M)", label: "Opportunity radar" })); });
  return [legend(CAT.filter(c => C.opportunities.some(o => o.category === c)).map(c => ({ key: c, label: c, color: colorOf(CAT, c), off: S.filters.category && S.filters.category !== c })), k => setFilter("category", k)),
    h("div", { id: "radar-" + w.id, style: { marginTop: "6px" } }), h("p", { class: "note" }, "Bubble size is strategic impact. Select a bubble for its drill-down.")];
 },
 risk_matrix(w) {
  requestAnimationFrame(() => { const el = $("#risk-" + w.id); if (!el) return;
    el.append(scatter(el, C.risks.map(r => ({ id: r.id, x: r.likelihood, y: r.impact, r: 7, color: colorOf(RCAT, r.category), dim: match(r) === false || match(r) === null, label: null,
      tip: `${r.label} · ${r.category} · owner ${r.owner} · ${r.trend}`, onclick: () => openRisk(r.id) })),
      { h: 300, ymax: 1, yticks: [0, .25, .5, .75, 1], yfmt: v => Math.round(v * 100) + "%", xlab: "Likelihood", ylab: "Business impact", quadrants: true, label: "Risk matrix" })); });
  return [legend(RCAT.filter(c => C.risks.some(r => r.category === c)).map(c => ({ key: c, label: c, color: colorOf(RCAT, c) })), null), h("div", { id: "risk-" + w.id, style: { marginTop: "6px" } }),
    h("p", { class: "note" }, "Shaded: high likelihood and high impact. Select a risk for owner, mitigation and evidence.")];
 },
 competitor_landscape() {
  return h("div", { class: "tw" }, h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Competitor", "Threat", "Momentum", "Overlap", "Overlap value", "Stakeholders touched", "Signals (90 days)", "Displacement opportunity", "Threads"].map((x, i) => h("th", { class: i >= 3 && i !== 7 ? "r" : "" }, x)))),
    h("tbody", {}, C.competition.landscape.map(c => h("tr", { class: "click" + (match(c) === false ? " dimmed" : ""), "data-competitor": c.label, onclick: () => setFilter("competitor", c.label) },
      h("td", { class: "row-t" }, c.label, pv(c.evidence, c.label)), h("td", {}, h("span", { class: "pill " + c.threat }, c.threat)), h("td", {}, c.momentum), h("td", { class: "r num" }, c.overlap_opportunities),
      h("td", { class: "r num" }, c.overlap_display), h("td", { class: "r num" }, c.footprint), h("td", { class: "r num" }, c.activity_90d), h("td", {}, c.displacement_opportunity ? h("span", { class: "pill Low" }, c.displacement_opportunity) : "—"),
      h("td", { class: "r" }, h("button", { class: "btn", onclick: e => { e.stopPropagation(); openDrill(c.drill_down_target); } }, `${c.threads} · open`)))))), h("p", { class: "note", style: { padding: "0 16px" } }, "Select a row to filter every widget by that competitor."));
 },
 thread_list() {
  const rows = C.competitive_threads.filter(t => match(t) !== false);
  return h("div", { class: "tw" }, h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Competitor", "Thread", "Status", "Momentum", "Signals", "Velocity", "Confidence", "Risk", "Opportunity"].map((x, i) => h("th", { class: [4, 5].includes(i) ? "r" : "" }, x)))),
    h("tbody", {}, rows.map(t => h("tr", { class: "click", "data-thread": t.id, onclick: () => openThread(t.id) },
      h("td", { class: "row-t" }, t.competitor), h("td", {}, t.thread_type.replace(/_/g, " ")), h("td", {}, t.status), h("td", { class: sentCls(t.momentum_sentiment) }, t.momentum.split(" (")[0]),
      h("td", { class: "r num" }, t.signal_count), h("td", { class: "r num" }, t.velocity_display), h("td", {}, conf(t.confidence)), h("td", {}, h("span", { class: "pill " + t.risk }, t.risk)), h("td", {}, h("span", { class: "pill " + t.opportunity_level }, t.opportunity_level)))))));
 },
 financial_panel() {
  const F = C.financial, out = [];
  if (F.public) {
    const P = F.public;
    out.push(h("div", { class: "sub" }, `${P.entity}: published financials (${P.periods.join(" → ")})`), h("div", { class: "tw" }, h("table", { class: "t" },
      h("thead", {}, h("tr", {}, ["Metric", P.periods[1] || "", P.periods[0], "Change", "Claim", "Confidence", "Source"].map((x, i) => h("th", { class: i >= 1 && i <= 3 ? "r" : "" }, x)))),
      h("tbody", {}, P.metrics.map(r => h("tr", { "data-fin": r.id, class: r.available ? "" : "dimmed" }, h("td", { class: "row-t" }, r.label), h("td", { class: "r num" }, r.display), h("td", { class: "r num" }, r.previous_display),
        h("td", { class: "r num " + (r.direction === "up" ? "pos" : r.direction === "down" ? "neg" : "") }, r.delta_display || ""), h("td", {}, r.available ? ctag(r.claim_type) : h("span", { class: "note" }, "Needs: " + r.missing_reason)),
        h("td", {}, conf(r.confidence)), h("td", { style: { maxWidth: "280px", overflow: "hidden", textOverflow: "ellipsis" }, title: r.source || "" }, pv(r.evidence, r.label), " ", r.source || "")))))),
      h("p", { class: "note" }, P.note + ". Metrics shown as Not available are absent from the cited sources and are not estimated."));
    const br = P.bridge, bw = h("div", { id: "bridge" });
    out.push(h("div", { class: "split" }, h("div", { style: { gridColumn: "span 7" } }, h("div", { class: "sub" }, br.title, pv(br.evidence)), bw, h("p", { class: "note" }, br.method)),
      h("div", { style: { gridColumn: "span 5" } }, h("div", { class: "sub" }, P.investment_mix.title, pv(P.investment_mix.evidence)), bars(P.investment_mix.items), h("div", { class: "sub" }, "Financial drivers"),
        h("ul", { class: "rows" }, P.drivers.map(d => h("li", {}, h("div", {}, ctag(d.signal_claim_type), d.what_changed, pv(d.evidence)), h("div", { class: "row-m" }, h("span", {}, "Implication: ", d.implication), ctag(d.claim_type), conf(d.confidence))))))));
    requestAnimationFrame(() => { const el = $("#bridge"); if (el) el.append(waterfall(el, br.steps)); });
  }
  if (F.account) {
    const A = F.account;
    out.push(h("div", { class: "sub" }, "Account economics (our business with this account)"), h("div", { class: "split" },
      h("div", { style: { gridColumn: "span 7" }, id: "acc-rev" }), h("div", { style: { gridColumn: "span 5" } }, h("div", { class: "note" }, A.revenue_mix.title + " · " + A.revenue_mix.basis), bars(A.revenue_mix.items, "growth_display"),
        h("table", { class: "t", style: { marginTop: "10px" } }, h("thead", {}, h("tr", {}, ["Business unit", "Revenue", "Growth", "Margin"].map((x, i) => h("th", { class: i ? "r" : "" }, x)))),
          h("tbody", {}, A.bu_performance.map(b => h("tr", {}, h("td", {}, b.label), h("td", { class: "r num" }, b.revenue_display), h("td", { class: "r num " + (b.direction === "up" ? "pos" : "neg") }, b.growth_display), h("td", { class: "r num" }, b.margin_display))))))),
      h("div", { class: "sub" }, "Account financial signals"), h("ul", { class: "rows" }, A.signals.filter(x => match(x) !== false).map(x => h("li", {}, h("div", { class: "row-h" }, h("span", {}, x.text, pv(x.evidence)), h("span", { class: sentCls(x.sentiment) }, arrow(x.direction)))))));
    requestAnimationFrame(() => { const el = $("#acc-rev"); if (el) el.append(h("div", { class: "note" }, "Quarterly account revenue and gross margin"), lineChart(el, [{ name: "actual", points: A.revenue }], { fmt: "money", h: 180, label: "Account revenue" }), lineChart(el, [{ name: "forecast", points: A.margin }], { fmt: "pct", h: 150, label: "Account margin" })); });
  } else if (C.permissions.restricted.length) out.push(h("div", { class: "empty" }, "Account economics are restricted for your role (needs financial data access)."));
  return out.length ? out : h("div", { class: "empty" }, "No financial data available. Connect filings or finance data to populate this section.");
 },
 marketing_panel() {
  const M = C.marketing; if (!M || !M.engagement) return h("div", { class: "empty" }, "No marketing data available for this role or account.");
  const hm = M.heatmap, mx = Math.max(1, ...hm.cells.flat());
  return [h("div", { class: "split" },
    stat("Account engagement", M.engagement.change_display, M.engagement.direction, M.engagement.evidence), stat("Executive engagement", `${M.executive_engagement.current} touches (was ${M.executive_engagement.previous})`, M.executive_engagement.current > M.executive_engagement.previous ? "up" : "flat", [], M.executive_engagement.roles.join(", ")),
    stat("Buying intent", `${M.intent.current} signals${M.intent.surge ? " · surge" : ""}`, M.intent.surge ? "up" : "flat", [], M.intent.types.join(", ")), stat("Marketing → pipeline", M.marketing_to_pipeline_display, null, [], M.marketing_to_pipeline_claim)),
   h("div", { class: "split", style: { marginTop: "12px" } },
    h("div", { style: { gridColumn: "span 4" } }, h("div", { class: "sub" }, "Warming accounts"), h("ul", { class: "rows" }, M.warming.map(u => h("li", { "data-warming": u.id }, h("div", { class: "row-h" }, h("span", { class: "row-t" }, u.label), h("span", { class: "pos num" }, u.change_display))))),
      h("div", { class: "sub" }, "Cooling accounts"), h("ul", { class: "rows" }, M.cooling.map(u => h("li", { "data-cooling": u.id }, h("div", { class: "row-h" }, h("span", { class: "row-t" }, u.label), h("span", { class: "neg num" }, u.change_display))))),
      h("div", { class: "sub" }, "Marketing → revenue"), h("p", { class: "note" }, M.marketing_to_revenue_note)),
    h("div", { style: { gridColumn: "span 8" } }, h("div", { class: "sub" }, "Campaigns and ABM programs"), h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Campaign", "Touches", "Influenced opportunities", "Pipeline influenced", "Claim"].map((x, i) => h("th", { class: i === 1 || i === 3 ? "r" : "" }, x)))),
      h("tbody", {}, M.campaigns.map(c => h("tr", {}, h("td", { class: "row-t" }, c.label), h("td", { class: "r num" }, c.touches), h("td", { class: "wrap" }, c.influenced.map(i => i.opportunity + " (" + Math.round(i.share * 100) + "%)").join(", ") || "—"),
        h("td", { class: "r num" }, c.pipeline_influenced_display), h("td", {}, ctag(c.claim_type === "MIXED" ? "CORRELATION" : c.claim_type)))))),
      h("div", { class: "sub" }, "Engagement heatmap (signals by category and month)"),
      h("table", { class: "t", "data-heatmap": "1" }, h("thead", {}, h("tr", {}, h("th", {}, ""), hm.cols.map(c => h("th", { class: "r" }, c)))),
        h("tbody", {}, hm.rows.map((r, i) => h("tr", {}, h("td", {}, r), hm.cells[i].map(v => h("td", { class: "r num", style: { background: v ? `color-mix(in srgb, var(--accent) ${Math.round(v / mx * 70) + 8}%, transparent)` : "", color: v / mx > 0.6 ? "#fff" : "" } }, v || "")))))))),
   h("div", { class: "sub" }, "Marketing timeline"), h("ul", { class: "rows" }, M.timeline.slice(-10).reverse().map(x => h("li", { class: match({ facets: { domain: ["marketing"], ...(x.stakeholder ? { stakeholder: [x.stakeholder] } : {}) } }) === false ? "dimmed" : "" },
     h("div", { class: "row-h" }, h("span", {}, x.label, x.executive ? h("span", { class: "pill Low", style: { marginLeft: "6px" } }, "executive") : null), h("span", { class: "note num" }, x.t))))),
   M.hypotheses.length ? [h("div", { class: "sub" }, "Hypotheses"), M.hypotheses.map(x => h("p", {}, ctag("HYPOTHESIS"), x.text, " ", conf(x.confidence), pv(x.evidence), x.missing_evidence.length ? h("span", { class: "note" }, " Missing: " + x.missing_evidence.join("; ")) : null))] : null];
 },
 relationship_map(w) {
  const R = C.relationships;
  requestAnimationFrame(() => { const el = $("#rel-" + w.id); if (!el) return;
    el.append(scatter(el, R.map(x => ({ id: x.id, x: x.strength_value, y: x.influence, r: x.champion ? 11 : 7, color: x.risk === "High" ? "var(--risk)" : x.risk === "Medium" ? "var(--warn)" : "var(--pos)", dim: match(x) === false || match(x) === null,
      label: x.role.length > 26 ? x.role.slice(0, 24) + "…" : x.role, tip: `${x.label} · ${x.role} · ${x.strength} (${x.trend}) · last ${x.last_interaction}${x.champion ? " · champion" : ""}`, onclick: () => openDrill(x.drill_down_target) })),
      { h: 340, ymax: 1, yticks: [0, .25, .5, .75, 1], yfmt: v => Math.round(v * 100) + "%", xlab: "Relationship strength (weak → strong)", ylab: "Influence", label: "Relationship map" })); });
  return h("div", { class: "split" }, h("div", { style: { gridColumn: "span 6" } }, h("div", { id: "rel-" + w.id }), h("p", { class: "note" }, "Larger circles are champions; color is relationship risk.")),
    h("div", { style: { gridColumn: "span 6" } }, table({ columns: [{ id: "n", label: "Stakeholder", type: "text" }, { id: "r", label: "Role", type: "text" }, { id: "s", label: "Strength", type: "level" }, { id: "t", label: "Trend", type: "text" }, { id: "l", label: "Last interaction", type: "date" }, { id: "k", label: "Risk", type: "level" }],
      rows: R.map(x => ({ id: x.id, facets: x.facets, drill_down_target: x.drill_down_target, cells: { n: x.label + (x.champion ? " ★" : ""), r: x.role, s: x.strength === "Strong" ? "Low" : x.strength === "Weak" ? "High" : "Medium", sLabel: x.strength, t: x.trend, l: x.last_interaction, k: x.risk } })) }, "stk")));
 },
 swot() {
  const Q = [["strengths", "Strengths"], ["weaknesses", "Weaknesses"], ["opportunities", "Opportunities"], ["threats", "Threats"]];
  const item = x => h("li", {},
    h("div", {}, ctag(x.claim_type), x.text, pv(x.evidence)),
    h("div", { class: "row-m" }, h("span", {}, "Impact " + x.impact), h("span", {}, "Trend " + arrow(x.trend === "up" ? "up" : x.trend === "down" ? "down" : "flat")),
      h("span", {}, x.date || ""), conf(x.confidence), h("span", { title: x.source }, (x.source || "").slice(0, 48))));
  const quad = ([k, l]) => { const L = C.swot[k] || [];
    return h("div", { "data-swot": k }, h("h4", {}, l), L.length ? h("ul", { class: "rows" }, L.map(item)) : h("div", { class: "empty" }, "No evidence-backed items.")); };
  return h("div", { class: "swot" }, Q.map(quad));
 },
 health() {
  return [h("div", { class: "health" }, C.health.dimensions.map(d => h("div", { class: "hd", "data-health": d.id }, h("div", { class: "hd-h" }, h("span", { class: "row-t" }, d.label), h("span", { class: "pill " + d.status }, d.status)),
    h("div", { class: "hd-h" }, h("span", { class: "hd-s num" }, d.status === "restricted" ? "—" : d.score), h("span", { class: sentCls(d.trend === "up" ? "positive" : d.trend === "down" ? "negative" : "neutral") }, arrow(d.trend))),
    h("div", { class: "meter" }, h("b", { style: { width: d.score + "%", background: d.status === "healthy" ? "var(--pos)" : d.status === "watch" ? "var(--warn)" : "var(--risk)" } })),
    h("div", { class: "note" }, d.basis, pv(d.evidence, d.label))))), h("p", { class: "note", style: { padding: "8px 16px" } }, C.health.note)];
 },
 action_list() {
  const rows = C.actions.filter(a => match(a) !== false);
  return h("ul", { class: "rows" }, rows.map(a => actionRow(a)));
 },
 scenario_lab() {
  const L = C.scenarios; if (!L.length) return h("div", { class: "empty" }, "No scenarios for this context.");
  const sc = L.find(x => x.id === S.scenario) || L[0];
  return [h("div", { class: "seg", role: "tablist" }, L.map(x => h("button", { "aria-pressed": String(x.id === sc.id), "data-scenario": x.id, onclick: () => { S.scenario = x.id; save(); render(); } }, x.label))),
    h("h3", { style: { margin: "14px 0 4px", fontSize: "16px" } }, sc.question), h("div", {}, ctag("MODELED"), h("span", { class: "note" }, "Modeled output, not a forecast of record. "), conf(sc.confidence), pv(sc.evidence)),
    h("div", { class: "split", style: { marginTop: "10px" } },
      h("div", { style: { gridColumn: "span 4" } }, h("div", { class: "sub" }, "Assumptions"), h("ol", { style: { margin: 0, paddingLeft: "18px" } }, sc.assumptions.map(x => h("li", { style: { marginBottom: "4px" } }, x)))),
      h("div", { style: { gridColumn: "span 8" } }, h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Metric", "Baseline", "Scenario", "Delta"].map((x, i) => h("th", { class: i ? "r" : "" }, x)))),
        h("tbody", {}, sc.rows.map(r => h("tr", {}, h("td", {}, r.metric), h("td", { class: "r num" }, r.baseline), h("td", { class: "r num" }, r.scenario), h("td", { class: "r num " + (r.delta_value < 0 ? "neg" : r.delta_value > 0 ? "pos" : "") }, r.delta))))),
        h("div", { class: "split", style: { marginTop: "10px" } }, Object.entries(sc.impacts).map(([k, v]) => h("div", { style: { gridColumn: "span 3" }, class: "ev" }, h("div", { class: "note" }, k[0].toUpperCase() + k.slice(1) + " impact"), h("div", {}, v)))),
        sc.variants.length ? [h("div", { class: "sub" }, "Probability variants"), h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Variant", "Expected revenue impact", "Expected forecast impact"].map((x, i) => h("th", { class: i ? "r" : "" }, x)))),
          h("tbody", {}, sc.variants.map(v => h("tr", {}, h("td", {}, v.label), h("td", { class: "r num neg" }, v.expected_revenue_impact), h("td", { class: "r num neg" }, v.expected_forecast_impact)))))] : null))];
 },
 comparison() {
  const modes = Object.keys(C.comparisons || {}), un = C.comparisons_unavailable || {};
  const unNote = Object.keys(un).length ? h("p", { class: "note", style: { padding: "8px 16px" } }, "Not available: " + Object.entries(un).map(([k, v]) => k.replace(/_/g, " ") + " (needs " + v + ")").join("; ")) : null;
  if (!modes.length) return [h("div", { class: "empty" }, "No comparisons are available with the current data."), unNote];
  const m = C.comparisons[S.compare] || C.comparisons[modes[0]];
  const body = m.columns ? h("table", { class: "t" }, h("thead", {}, h("tr", {}, h("th", {}, ""), m.columns.map(c => h("th", { class: "r" }, c)))), h("tbody", {}, m.rows.map(r => h("tr", {}, h("td", {}, r.label), r.values.map(v => h("td", { class: "r num" }, v))))))
    : h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["", m.a_label, m.b_label, "Delta"].map((x, i) => h("th", { class: i ? "r" : "" }, x)))), h("tbody", {}, m.rows.map(r => h("tr", {}, h("td", {}, r.label), h("td", { class: "r num" }, r.a), h("td", { class: "r num" }, r.b), h("td", { class: "r num " + sentCls(r.sentiment) }, r.delta ? arrow(r.direction) + " " + r.delta : "")))));
  return [h("div", { class: "tbl-tools" }, h("label", { class: "lbl" }, "Compare ", h("select", { class: "sel", "data-compare": "1", onchange: e => { S.compare = e.target.value; save(); render(); } }, modes.map(k => h("option", { value: k, selected: k === S.compare }, C.comparisons[k].label))))), h("div", { class: "tw" }, body),
    unNote, m.public ? [h("div", { class: "sub", style: { padding: "0 16px" } }, "Published financials"), h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["", m.public.a_label, m.public.b_label, "Change"].map((x, i) => h("th", { class: i ? "r" : "" }, x)))), h("tbody", {}, m.public.rows.map(r => h("tr", {}, h("td", {}, r.label), h("td", { class: "r num" }, r.a), h("td", { class: "r num" }, r.b), h("td", { class: "r num" }, r.delta || "")))))] : null];
 },
 table(w) { const T = (C.tables || {})[w.id === "accounts_table" ? "accounts" : "opportunities"];
  return T && T.rows && T.rows.length ? table(T, w.id) : h("div", { class: "empty" }, w.id === "accounts_table" ? "No account data yet. Account revenue and pipeline populate this table." : "No opportunities recorded for this account."); },
 insight_list() { return h("ul", { class: "rows" }, C.insights.filter(i => match(i) !== false).map(i => h("li", { "data-insight": i.id }, h("div", { class: "row-h" }, h("span", {}, ctag(i.claim_type), h("b", {}, i.label), i.anomaly ? h("span", { class: "pill High", style: { marginLeft: "6px" } }, "anomaly") : null), conf(i.confidence)), h("div", {}, i.text, pv(i.evidence)), i.missing_evidence && i.missing_evidence.length ? h("div", { class: "note" }, "Missing evidence: " + i.missing_evidence.join("; ")) : null))); },
 decision_list() { return h("ul", { class: "rows" }, (C.decisions || []).map(d => h("li", {}, h("div", { class: "row-h" }, h("span", { class: "row-t" }, d.question), h("span", { class: "pill Medium" }, d.status)), h("div", { class: "row-m" }, h("span", {}, "Owner " + d.owner), h("span", {}, "Deadline " + d.deadline), conf(d.confidence), pv(["EV-" + d.id])),
   h("table", { class: "t" }, h("thead", {}, h("tr", {}, ["Option", "Financial impact", "Risks"].map(x => h("th", {}, x)))), h("tbody", {}, d.options.map(o => h("tr", {}, h("td", {}, o.name), h("td", {}, o.financial_impact), h("td", {}, o.risks))))), h("div", {}, ctag("RECOMMENDATION"), d.recommendation)))); },
 metric_grid() { return h("div", { class: "health" }, C.operations.map(o => h("div", { class: "hd" }, h("div", { class: "row-t" }, o.label), h("div", { class: "hd-s num" }, o.display), h("div", { class: sentCls(o.sentiment) }, o.delta_display, h("span", { class: "note" }, " vs " + o.previous_display)), h("div", { class: "note" }, o.source, pv(o.evidence))))); },
 event_list() { return (C.market || []).length ? h("ul", { class: "rows" }, C.market.map(e => h("li", {}, h("div", { class: "row-h" }, h("span", {}, ctag(e.claim_type), e.label, pv(e.evidence)), h("span", { class: "note" }, e.date)), h("div", { class: "row-m" }, e.source)))) : h("div", { class: "empty" }, "No market events recorded. Market intelligence populates this from cited sources."); },
 signal_list() { const L = C.signals.filter(x => match(x) !== false).slice(0, 40); return h("ul", { class: "rows" }, L.map(x => h("li", { "data-signal": x.id }, h("div", { class: "row-h" }, h("span", {}, ctag(x.claim_type), x.label, pv(x.evidence)), h("span", { class: "note num" }, x.timestamp)), h("div", { class: "row-m" }, h("span", {}, x.domain), conf(x.confidence))))); },
};
function stat(label, value, dir, ev, sub) { return h("div", { class: "ev", style: { gridColumn: "span 3", marginBottom: 0 } }, h("div", { class: "note" }, label), h("div", { class: "kpi-v num", style: { fontSize: "18px" } }, value, " ", dir ? h("span", { class: dir === "up" ? "pos" : dir === "down" ? "neg" : "neu" }, arrow(dir)) : null, pv(ev)), sub ? h("div", { class: "note" }, sub) : null); }
function bars(items, extra) { const mx = Math.max(...items.map(i => i.value), 0.0001); return h("div", {}, items.map(i => h("div", { style: { display: "grid", gridTemplateColumns: "120px 1fr 90px", gap: "8px", alignItems: "center", margin: "5px 0" } },
  h("span", {}, i.label), h("span", { class: "meter", style: { margin: 0 } }, h("b", { style: { width: (i.value / mx * 100) + "%", background: "var(--accent)" } })), h("span", { class: "num", style: { textAlign: "right" } }, i.display, extra && i[extra] ? h("span", { class: "note" }, " " + i[extra]) : null)))); }
function waterfall(box, steps) {
  const W = widthOf(box), H = 220, m = { l: 44, r: 10, t: 16, b: 40 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  let run = 0; const bars_ = steps.map(st => { if (st.kind === "start") { run = st.value; return { ...st, a: 0, b: st.value }; } if (st.kind === "end") return { ...st, a: 0, b: st.value }; const a = run; run += st.value; return { ...st, a, b: run }; });
  const lo = Math.min(...bars_.map(b => Math.min(b.a, b.b))), hi = Math.max(...bars_.map(b => Math.max(b.a, b.b)));
  // A bridge zooms to the range of the change: start/end bars are drawn from a non-zero baseline, which the axis states.
  const runLo = Math.min(...bars_.filter(b => b.kind === "delta").map(b => Math.min(b.a, b.b)), ...bars_.map(b => b.b));
  const y0 = Math.floor(runLo - (hi - runLo) * 0.6 - 0.5), y1 = Math.ceil(hi + (hi - runLo) * 0.25 + 0.3), Y = v => m.t + ih - (Math.max(v, y0) - y0) / (y1 - y0) * ih, bw = iw / bars_.length * 0.62;
  const svg = s("svg", { class: "ch", viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": "Margin bridge" });
  [y0, (y0 + y1) / 2, y1].forEach(v => svg.append(s("line", { class: "gl", x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }), s("text", { x: m.l - 6, y: Y(v) + 4, "text-anchor": "end" }, v.toFixed(1) + "%")));
  svg.append(s("text", { x: m.l, y: H - 4, style: "fill:var(--muted);font-size:10.5px" }, `Axis starts at ${y0.toFixed(1)}%`));
  bars_.forEach((b, i) => { const x = m.l + i * (iw / bars_.length) + (iw / bars_.length - bw) / 2; const top = Y(Math.max(b.a, b.b)), ht = Math.max(1.5, Math.abs(Y(b.a) - Y(b.b)));
    const col = b.kind === "delta" ? (b.value >= 0 ? "var(--pos)" : "var(--risk)") : "var(--accent)";
    svg.append(s("rect", { x, y: b.kind === "delta" ? top : Y(b.b), width: bw, height: b.kind === "delta" ? ht : Y(y0) - Y(b.b), fill: col, "fill-opacity": b.kind === "delta" ? 0.85 : 0.9 }),
      s("text", { x: x + bw / 2, y: (b.kind === "delta" ? top : Y(b.b)) - 4, "text-anchor": "middle", style: "fill:var(--ink-2)" }, b.display),
      s("text", { x: x + bw / 2, y: H - 22, "text-anchor": "middle" }, b.label.length > 16 ? b.label.slice(0, 15) + "…" : b.label)); });
  return svg;
}
const TBL = {};
function table(T, key) {
  const st = TBL[key] = TBL[key] || { sort: null, dir: 1, q: "", hidden: {}, menu: false };
  let rows = T.rows.filter(r => match(r) !== false && (!st.q || JSON.stringify(r.cells).toLowerCase().includes(st.q.toLowerCase())));
  if (st.sort) { const k = st.sort; rows = rows.slice().sort((a, b) => { const va = a.cells[k], vb = b.cells[k]; const x = va && va.v != null ? va.v : va, y = vb && vb.v != null ? vb.v : vb; return (x > y ? 1 : x < y ? -1 : 0) * st.dir; }); }
  const cols = T.columns.filter(c => !st.hidden[c.id]);
  const cell = (c, v, r) => { if (c.type === "spark") return h("td", {}, spark(v)); if (c.type === "level") return h("td", {}, h("span", { class: "pill " + v }, r.cells[c.id + "Label"] || r.cells.sLabel && c.id === "s" ? r.cells.sLabel : v));
    if (v && typeof v === "object") return h("td", { class: "r num" }, v.d, v.delta ? h("span", { class: "note", style: { marginLeft: "6px" } }, v.delta) : null, c.id === "growth" ? h("span", { class: v.v >= 0 ? "pos" : "neg", style: { marginLeft: "4px" } }, v.v >= 0 ? "▲" : "▼") : null);
    return h("td", { class: c.type === "money" || c.type === "pct" ? "r num" : "" }, v ?? "—"); };
  const wrap = h("div", { "data-table": key },
    h("div", { class: "tbl-tools" }, h("input", { type: "search", placeholder: "Filter rows", value: st.q, "aria-label": "Filter rows", oninput: e => { st.q = e.target.value; const p = wrap.parentNode; p.replaceChild(table(T, key), wrap); p.querySelector("input").focus(); } }),
      h("div", { style: { display: "flex", gap: "6px" } }, h("span", { class: "note", style: { alignSelf: "center" } }, `${rows.length} rows`),
        h("button", { class: "btn", "aria-pressed": String(S.density === "compact"), onclick: () => { S.density = S.density === "compact" ? "comfortable" : "compact"; save(); render(); } }, S.density === "compact" ? "Comfortable" : "Compact"),
        h("div", { class: "menu" }, h("button", { class: "btn", "data-cols": key, onclick: () => { st.menu = !st.menu; render(); } }, "Columns"),
          st.menu ? h("div", { class: "menu-pop" }, T.columns.map(c => h("label", {}, h("input", { type: "checkbox", checked: !st.hidden[c.id], "data-col": c.id, onchange: () => { st.hidden[c.id] = !st.hidden[c.id]; render(); } }), c.label))) : null))),
    h("div", { class: "tw" }, h("table", { class: "t" }, h("thead", {}, h("tr", {}, cols.map(c => h("th", { "data-sort": c.id, class: c.type === "money" || c.type === "pct" ? "r" : "", onclick: () => { st.dir = st.sort === c.id ? -st.dir : 1; st.sort = c.id; render(); } }, c.label, st.sort === c.id ? h("span", { class: "ar" }, st.dir > 0 ? " ▲" : " ▼") : "")))),
      h("tbody", {}, rows.map(r => h("tr", { class: (r.drill_down_target ? "click" : "") + (match(r) === null ? " dimmed" : ""), "data-row": r.id, onclick: () => r.drill_down_target && openDrill(r.drill_down_target) }, cols.map(c => cell(c, r.cells[c.id], r))))))));
  return wrap;
}
function actionRow(a) {
  if (!a) return null;
  return h("li", { "data-action": a.id }, h("div", { class: "row-h" }, h("span", {}, h("span", { class: "pill " + (a.priority === "P1" ? "High" : "Medium") }, a.priority), " ", h("b", {}, a.label), pv(a.evidence)),
      h("button", { class: "btn" + (a.approval_required ? " pri" : ""), "data-request": a.id, onclick: () => ask(`${a.approval_required ? "Request approval for" : "Proceed with"} action ${a.id} (${a.catalog_action}): ${a.label}`) }, a.approval_required ? "Request approval" : "Send to Action Center")),
    h("div", { class: "row-m" }, h("span", {}, "Why: " + a.reason), h("span", {}, "Owner " + a.owner), a.due ? h("span", {}, "Due " + a.due) : null, h("span", {}, "Impact: " + a.expected_impact), h("span", {}, a.catalog_action), h("span", {}, a.governance)));
}
function openRisk(id) { const r = C.risks.find(x => x.id === id); openDrill(r.drill_down_target); }
function openThread(id) {
  const t = C.competitive_threads.find(x => x.id === id); if (!t) return;
  const box = h("div", { id: "tl-box" });
  drawer(t.label, [h("div", { class: "row-m", style: { marginBottom: "8px" } }, h("span", { class: "pill " + t.risk }, "Risk " + t.risk), h("span", {}, t.momentum), h("span", {}, t.signal_count + " signals"), h("span", {}, t.velocity_display), conf(t.confidence)),
    h("div", { class: "sub" }, "Chronology"), box,
    h("ul", { class: "rows" }, t.chronology.map(c => h("li", { "data-chrono": c.t }, h("div", { class: "row-h" }, h("span", {}, h("b", {}, c.label), " · ", c.text, c.evidence ? pv([c.evidence]) : null), h("span", { class: "note num" }, c.t)), h("div", { class: "row-m " + (c.polarity > 0 === (t.thread_type !== "displacement_opportunity") ? "neg" : "pos") }, c.polarity > 0 ? "competitor gaining" : "competitor weakening")))),
    t.counter_evidence.length ? [h("div", { class: "sub" }, "Counter-evidence"), h("ul", { class: "rows" }, t.counter_evidence.map(c => h("li", {}, c.text, h("span", { class: "note" }, " · " + c.at))))] : null,
    t.predicted_next_event ? [h("div", { class: "sub" }, "Predicted next event"), h("p", {}, ctag("PREDICTION"), t.predicted_next_event.event, h("span", { class: "note" }, ` (confidence ${t.predicted_next_event.confidence}; ${t.predicted_next_event.basis})`))] : null,
    t.recommended_action_id ? [h("div", { class: "sub" }, "Recommended action"), h("ul", { class: "rows" }, actionRow(C.actions.find(a => a.id === t.recommended_action_id)))] : null,
    h("div", { class: "sub" }, "Evidence"), t.evidence.map(e => evCard(EV[e]))]);
  $("#drawer").dataset.kind = "thread"; $("#drawer").dataset.node = t.drill_down_target;
  requestAnimationFrame(() => { const el = $("#tl-box"); if (!el) return; const W = widthOf(el), H = 150, m = 24; const ts = t.chronology.map(c => new Date(c.t).getTime()); const a = Math.min(...ts), b = Math.max(...ts, a + 864e5 * 30);
    const X = v => m + (v - a) / (b - a) * (W - 2 * m); const svg = s("svg", { class: "ch", viewBox: `0 0 ${W} ${H}`, width: W, height: H, "data-timeline": t.id });
    svg.append(s("line", { class: "ax", x1: m, x2: W - m, y1: H - 26, y2: H - 26 }));
    const mo = new Date(a); mo.setDate(1); for (let d = new Date(mo); d.getTime() <= b; d.setMonth(d.getMonth() + 1)) { if (d.getTime() < a) continue; svg.append(s("text", { x: X(d.getTime()), y: H - 8, "text-anchor": "middle" }, d.toLocaleString("en", { month: "short" }))); }
    t.chronology.forEach((c, i) => { const x = X(new Date(c.t).getTime()), y = 18 + (i % 4) * 26; const col = (c.polarity > 0) === (t.thread_type !== "displacement_opportunity") ? "var(--risk)" : "var(--pos)";
      svg.append(s("line", { x1: x, x2: x, y1: y + 6, y2: H - 26, stroke: col, "stroke-width": 1 }), s("circle", { cx: x, cy: H - 26, r: 4, fill: col }), s("text", { x: x > W * 0.68 ? x - 4 : x + 4, y: y + 4, "text-anchor": x > W * 0.68 ? "end" : "start", style: "fill:var(--ink-2)" }, c.label)); });
    el.append(svg); });
}
/* ---------- persona + page ---------- */
function personaLayout() { return (C.persona_layouts && C.persona_layouts[S.persona]) || { label: D.persona_label, navigation: C.navigation, kpis: C.metrics.map(m => m.id), views: C.layout.views }; }
const ICON = { search: '<path d="M11 18a7 7 0 1 1 0-14 7 7 0 0 1 0 14zM20 20l-4-4"/>', ask: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 10h8M8 13h5"/>', changes: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>', alerts: '<path d="M6 16V11a6 6 0 1 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>', profile: '<circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4 5-5 8-5s6.5 1 8 5"/>', settings: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>' };
const ib = (k, label, on, badge) => h("button", { class: "ib", "aria-label": label, title: label, "data-tool": k, onclick: on, html: `<svg viewBox="0 0 24 24">${ICON[k]}</svg>` + (badge ? `<span class="dot">${badge}</span>` : "") });
function render() {
  document.documentElement.setAttribute("data-theme", S.theme);
  const PL = personaLayout(); if (!PL.navigation.some(n => n.id === S.view)) S.view = PL.navigation[0].id;
  const app = $("#app"); const y = scrollY; app.innerHTML = "";
  const hi = C.risks.filter(r => r.likelihood * r.impact >= 0.3).length;
  app.append(h("header", { class: "hdr" },
    h("div", { class: "brand" }, h("span", { class: "brand-mark", "aria-hidden": "true" }), h("span", {}, "GROWTH INTELLIGENCE")),
    h("div", { class: "ctx" }, h("span", { class: "ctx-entity" }, D.entity_name), h("span", { class: "ctx-meta" }, D.entity_segment), h("span", { class: "ctx-meta" }, D.period),
      h("span", { class: "ctx-meta" }, "Data as of " + D.data_freshness.as_of + " · confidence " + Math.round(D.overall_confidence * 100) + "%")),
    h("div", { class: "hdr-tools" }, ib("search", "Search", () => $("#ask").focus()), ib("ask", "Ask Intelligence", () => $("#ask").focus()), ib("changes", "Recent changes", () => uiTarget({ view: "overview", focus: "changes" })),
      ib("alerts", "Alerts", () => openEvidence(C.risks.filter(r => r.likelihood * r.impact >= 0.3).flatMap(r => r.evidence).slice(0, 12), "Alerts: high-exposure risks"), hi || null),
      ib("profile", "Persona and role", () => personaMenu()), ib("settings", "Settings", () => settingsMenu()))));
  if (D.data_mode === "demo") app.append(h("div", { class: "demo", role: "note" }, h("b", {}, "DEMO DATA — NOT REAL CUSTOMER DATA. "), D.data_notice ? D.data_notice.replace(/^DEMO DATA — NOT REAL CUSTOMER DATA\.?\s*/, "") : ""));
  app.append(h("nav", { class: "nav", role: "tablist", "aria-label": "Sections" }, PL.navigation.map(n => h("button", { role: "tab", "aria-selected": String(n.id === S.view), "data-view": n.id, onclick: () => { S.view = n.id; save(); render(); scrollTo(0, 0); } }, n.label))));
  const fchips = Object.entries(S.filters);
  app.append(h("div", { class: "bar" },
    h("form", { class: "ask", role: "search", onsubmit: e => { e.preventDefault(); ask($("#ask").value); } }, h("span", { html: '<svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/></svg>' }),
      h("input", { id: "ask", placeholder: "Ask anything about this business…", "aria-label": "Ask Intelligence", autocomplete: "off" }), h("kbd", {}, "/")),
    h("label", { class: "lbl" }, "Filter ", h("select", { class: "sel", "data-filter-select": "1", onchange: e => { if (!e.target.value) return; const [d, v] = e.target.value.split("::"); setFilter(d, v); } },
      h("option", { value: "" }, "Add a filter…"), C.filters.map(f => h("optgroup", { label: f.label }, f.values.map(v => h("option", { value: f.dimension + "::" + v.value }, `${v.label} (${v.count})`)))))),
    h("div", { class: "chips" }, fchips.map(([d, v]) => h("span", { class: "chip", "data-chip": d }, `${C.filters.find(f => f.dimension === d)?.label || d}: ${filterLabel(d, v)}`, h("button", { "aria-label": "Remove filter", onclick: () => setFilter(d, v) }, "×"))),
      fchips.length ? h("button", { class: "btn", onclick: clearFilters }, "Clear") : null)));
  app.append(h("div", { class: "suggest", role: "group", "aria-label": "Suggested prompts" }, C.queries.slice(0, 5).map(q => h("button", { "data-query": q.id, title: q.why ? "Suggested because " + q.why : (q.capability || ""),
      onclick: () => ask(q.question, q.capability) }, q.tier === "contextual" ? h("span", { class: "sig", "aria-label": "signal" }) : null, q.question)),
    C.discovery ? h("button", { class: "explore", "data-explore-open": "1", onclick: () => openExplore() }, "Explore capabilities") : null));
  const main = h("main", { class: "main" }), grid = h("div", { class: "grid" });
  (PL.views[S.view] || []).forEach(w => { const fn = WIDGETS[w.type]; if (!fn) return;
    const sec = h("section", { class: "w", "data-widget": w.id, "data-type": w.type, style: { "--span": w.span }, "aria-labelledby": "t-" + w.id },
      w.type === "kpi_strip" ? null : h("div", { class: "wh" }, h("h2", { class: "wt", id: "t-" + w.id }, w.title), h("span", { class: "wm" }, meta(w))));
    const b = h("div", { class: "wb" + (["kpi_strip", "narrative", "change_list", "competitor_landscape", "thread_list", "action_list", "swot", "health", "insight_list", "signal_list", "event_list", "table", "comparison"].includes(w.type) ? " flush" : "") });
    try { b.append(...[fn(w, b)].flat(9).filter(x => x != null && x !== false)); } catch (err) { b.append(h("div", { class: "empty" }, "This section could not be displayed: " + err.message)); }
    sec.append(b); grid.append(sec); });
  main.append(grid, h("p", { class: "note", style: { marginTop: "16px" } }, `${C.provenance.builder} · provider ${C.provenance.provider} · generated ${C.provenance.generated_at} · persona ${PL.label} · role ${C.permissions.role}`));
  app.append(main);
  document.body.classList.toggle("dense", S.density === "compact");
  scrollTo(0, y);
}
function meta(w) { const m = { kpi_strip: "", narrative: "Generated from computed metrics; every sentence cites evidence", change_list: C.changes.length ? "Delta Intelligence, since the previous snapshot" : "Delta Intelligence", trend_chart: "Billing and CRM", opportunity_radar: "Probability × value · size = strategic impact",
  risk_matrix: "Likelihood × impact", thread_list: "Persistent threads from Business Memory", scenario_lab: "Modeled outputs", action_list: "Governed by the Action Center", health: "No composite score" }; return m[w.type] || ""; }
function personaMenu() {
  const P = C.persona_layouts || {};
  drawer("Persona and role", [h("p", { class: "note" }, "Persona changes what is emphasized. Your role controls which data you can see and is set by your administrator."),
    h("dl", { class: "kv" }, h("dt", {}, "Role"), h("dd", {}, C.permissions.role), h("dt", {}, "Data classes"), h("dd", {}, C.permissions.data_classes.join(", ")),
      C.permissions.restricted.length ? [h("dt", {}, "Restricted"), h("dd", {}, C.permissions.restricted.map(r => r.item).join("; "))] : null),
    h("div", { class: "sub" }, "Persona"), h("div", { class: "seg", style: { flexWrap: "wrap" } }, Object.entries(P).map(([k, v]) => h("button", { "aria-pressed": String(k === S.persona), "data-persona": k, onclick: () => { S.persona = k; save(); closeDrawer(); render(); } }, v.label)))]);
}
function settingsMenu() {
  drawer("Settings and saved views", [h("div", { class: "sub" }, "Theme"), h("div", { class: "seg" }, ["light", "dark"].map(t => h("button", { "aria-pressed": String(S.theme === t), "data-theme-btn": t, onclick: () => { S.theme = t; save(); render(); settingsMenu(); } }, t === "light" ? "Light" : "Dark"))),
    h("div", { class: "sub" }, "Density"), h("div", { class: "seg" }, ["comfortable", "compact"].map(t => h("button", { "aria-pressed": String(S.density === t), onclick: () => { S.density = t; save(); render(); settingsMenu(); } }, t[0].toUpperCase() + t.slice(1)))),
    h("div", { class: "sub" }, "Saved views"), h("button", { class: "btn", "data-save-view": "1", onclick: () => { S.saved.push({ name: `View ${S.saved.length + 1}: ${S.view}${Object.keys(S.filters).length ? " (filtered)" : ""}`, view: S.view, filters: { ...S.filters }, persona: S.persona }); save(); settingsMenu(); } }, "Save current view"),
    h("ul", { class: "rows" }, S.saved.map((v, i) => h("li", { class: "click", onclick: () => { Object.assign(S, { view: v.view, filters: { ...v.filters }, persona: v.persona }); save(); closeDrawer(); render(); } }, v.name))),
    h("div", { class: "sub" }, "About this dashboard"), h("dl", { class: "kv" }, h("dt", {}, "Contract"), h("dd", {}, C.contract_version), h("dt", {}, "Engines"), h("dd", {}, C.provenance.engines.join(", ")), h("dt", {}, "Oldest source"), h("dd", {}, D.data_freshness.oldest_source_date || "—"),
      h("dt", {}, "Stale sources"), h("dd", {}, (D.data_freshness.stale_sources_over_180_days || []).length + " over 180 days"))]);
}
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); if (e.key === "/" && document.activeElement.tagName !== "INPUT") { e.preventDefault(); $("#ask").focus(); } });
let rz; addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(render, 150); });
window.GI = { state: () => S, setFilter, clearFilters, openDrill, openThread, openEvidence, ask, uiTarget, render, contract: C };
render();
