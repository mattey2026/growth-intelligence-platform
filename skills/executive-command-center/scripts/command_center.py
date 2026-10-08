#!/usr/bin/env python3
"""
command_center.py: generates the Adaptive Executive Command Center as one self-contained HTML page.

INPUT JSON (assembled by the executive-command-center skill from the memory graph, KPI engine,
forecast, and analyses):
{ "title": "", "asof": "", "previous_review": "",
  "context": {"business_model": "", "industry": "", "scale": "", "confidence": 0.0},
  "kpis": [{"name":"", "value":0, "unit":"$|%|x|#", "previous":null, "change_pct":null, "forecast":null,
            "previous_forecast":null, "target":null, "benchmark":null, "confidence":"High|Medium|Low", "source":"", "status":"actual"}],
  "views": {"CEO": ["kpi names"], "Investor": [...], "Owner": [...]},
  "changes": [{"when":"", "what":"", "why":"", "severity":"risk|watch|opportunity|info"}],
  "drivers": [{"text":"", "evidence":""}],
  "next": [{"text":"", "kind":"prediction", "confidence":"", "basis":""}],
  "actions": [{"text":"", "owner":"", "due":"", "approval":true, "impact":""}],
  "unsupported": ["KPI (needs …)"], "sources": [{"name":"", "refreshed":"", "status":"Healthy|Stale"}] }
USAGE: python command_center.py cc.json --out command_center.html
The page answers five questions: How are we doing? What changed? Why? What happens next? What should I do?
Only supported metrics are shown; unsupported ones are listed once, with what they need.
"""
import argparse, json, html

ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("--out", required=True); a = ap.parse_args()
D = json.load(open(a.inp))
E = html.escape

def fmt(v, u):
    if v is None:
        return "—"
    if u == "$":
        return f"${v/1e6:,.1f}M" if abs(v) >= 1e6 else f"${v:,.0f}"
    if u == "%":
        return f"{v*100:.1f}%"
    if u == "x":
        return f"{v:.2f}×"
    return f"{v:,.0f}"

def card(k):
    ch = k.get("change_pct")
    arrow = "" if ch is None else ("▲" if ch > 0 else "▼" if ch < 0 else "■")
    if ch is None:
        delta = '<span class="delta muted">First review: no previous value</span>' if k.get("previous") is None else ''
    elif ch == 0:
        delta = f'<span class="delta muted">Unchanged since {E(D.get("previous_review","last review"))}</span>'
    else:
        delta = f'<span class="delta">{arrow} {ch:+.1f}% vs {E(D.get("previous_review","last review"))}</span>'
    rows = []
    if k.get("previous") is not None and k.get("change_pct") not in (0, 0.0): rows.append(("Previous", fmt(k["previous"], k["unit"])))
    if k.get("forecast") is not None: rows.append(("Forecast", fmt(k["forecast"], k["unit"])))
    if k.get("previous_forecast") is not None: rows.append(("Previous forecast", fmt(k["previous_forecast"], k["unit"])))
    if k.get("target") is not None: rows.append(("Target", fmt(k["target"], k["unit"])))
    if k.get("benchmark") is not None: rows.append(("Benchmark", fmt(k["benchmark"], k["unit"])))
    dl = "".join(f"<div><dt>{E(x)}</dt><dd>{E(y)}</dd></div>" for x, y in rows)
    tone = k.get("tone", "")
    return (f'<article class="kpi {tone}"><h3>{E(k["name"])}</h3><p class="val">{fmt(k["value"], k["unit"])}</p>{delta}'
            f'<dl>{dl}</dl><p class="src">{E(k.get("source",""))} · confidence {E(k.get("confidence","—"))}</p></article>')

K = {k["name"]: k for k in D["kpis"] if k.get("status", "actual") == "actual"}
views = D.get("views", {"CEO": list(K)})
tabs = "".join(f'<button role="tab" aria-selected="{str(i==0).lower()}" data-v="{E(v)}">{E(v)}</button>' for i, v in enumerate(views))
panels = "".join(f'<section class="panel" data-v="{E(v)}" {"hidden" if i else ""}><div class="grid">' + "".join(card(K[n]) for n in names if n in K) + "</div></section>" for i, (v, names) in enumerate(views.items()))
chg = "".join(f'<li class="{E(c.get("severity","info"))}"><time>{E(c.get("when",""))}</time><div><strong>{E(c["what"])}</strong><p>{E(c.get("why",""))}</p></div></li>' for c in D.get("changes", []))
drv = "".join(f'<li>{E(d["text"])}<span class="ev">{E(d.get("evidence",""))}</span></li>' for d in D.get("drivers", []))
nxt = "".join(f'<li><span class="tag">Prediction · {E(n.get("confidence",""))}</span>{E(n["text"])}<span class="ev">{E(n.get("basis",""))}</span></li>' for n in D.get("next", []))
act = "".join(f'<tr><td>{E(x["text"])}</td><td>{E(x.get("owner",""))}</td><td>{E(x.get("due",""))}</td><td>{E(x.get("impact",""))}</td><td>{"Needs approval" if x.get("approval") else "—"}</td></tr>' for x in D.get("actions", []))
src = " · ".join(f'{E(s["name"])} <span class="{ "stale" if s.get("status")=="Stale" else "ok"}">{E(s.get("status",""))}, {E(s.get("refreshed",""))}</span>' for s in D.get("sources", []))
uns = "".join(f"<li>{E(u)}</li>" for u in D.get("unsupported", []))
c = D["context"]
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(D.get("title","Executive Command Center"))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#16324F;--fog:#EDF1F5;--paper:#FFFFFF;--text:#1E2A36;--muted:#5B6875;--line:#D5DCE3;--risk:#B42318;--opp:#0E7C66;--watch:#A15C07;--graph:#2F3A45;
 box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--ink:#9CC3E6;--fog:#0F1A24;--paper:#16222E;--text:#E6ECF2;--muted:#9AA8B5;--line:#2A3A49;--risk:#F07167;--opp:#4CC9A6;--watch:#E3A64B;--graph:#C9D3DC;color-scheme:dark}}}}
:root[data-theme="dark"]{{--ink:#9CC3E6;--fog:#0F1A24;--paper:#16222E;--text:#E6ECF2;--muted:#9AA8B5;--line:#2A3A49;--risk:#F07167;--opp:#4CC9A6;--watch:#E3A64B;--graph:#C9D3DC;color-scheme:dark}}
html{{scroll-padding-top:env(safe-area-inset-top,0px)}} *,*::before,*::after{{box-sizing:inherit}}
body{{margin:0;background:var(--fog);color:var(--text);font:400 15px/1.55 "Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1120px;margin:0 auto;padding:28px 20px 60px}}
header.top{{display:flex;flex-wrap:wrap;gap:12px 32px;align-items:flex-end;justify-content:space-between;border-bottom:2px solid var(--ink);padding-bottom:16px}}
h1{{font:600 clamp(26px,4vw,38px)/1.1 "Newsreader",Georgia,serif;margin:0;color:var(--ink)}}
.ctx{{color:var(--muted);font-size:13px;max-width:52ch}} .ctx b{{color:var(--text);font-weight:600}}
h2{{font:600 22px/1.2 "Newsreader",Georgia,serif;color:var(--ink);margin:40px 0 12px}}
.q{{color:var(--muted);font-size:13px;margin:-6px 0 14px}}
[role=tablist]{{display:flex;gap:4px;margin-top:22px}}
[role=tab]{{font:500 14px "Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;padding:8px 16px;border:1px solid var(--line);background:var(--paper);color:var(--text);border-radius:6px 6px 0 0;cursor:pointer}}
[role=tab][aria-selected=true]{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
[role=tab]:focus-visible,button:focus-visible{{outline:3px solid var(--watch);outline-offset:2px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1px;background:var(--line);border:1px solid var(--line)}}
.kpi{{background:var(--paper);padding:16px 18px 14px}} .kpi h3{{margin:0;font:500 13px/1.3 "Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--muted)}}
.kpi .val{{font:600 30px/1.1 "Newsreader",Georgia,serif;margin:8px 0 4px;color:var(--text)}}
.kpi.risk .val{{color:var(--risk)}} .kpi.opp .val{{color:var(--opp)}}
.delta{{font-size:12.5px;color:var(--graph)}} .muted{{color:var(--muted)}}
dl{{display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;margin:10px 0 6px;font-size:12.5px}} dl:empty{{display:none}} dt{{color:var(--muted)}} dd{{margin:0;font-weight:600}}
.src{{font-size:11.5px;color:var(--muted);margin:6px 0 0}}
ol.ledger{{list-style:none;margin:0;padding:0;border-left:3px solid var(--ink)}}
ol.ledger li{{display:grid;grid-template-columns:110px 1fr;gap:14px;padding:10px 0 10px 16px;border-bottom:1px solid var(--line);position:relative}}
ol.ledger li::before{{content:"";position:absolute;left:-7px;top:16px;width:11px;height:11px;border-radius:50%;background:var(--muted)}}
ol.ledger li.risk::before{{background:var(--risk)}} ol.ledger li.opportunity::before{{background:var(--opp)}} ol.ledger li.watch::before{{background:var(--watch)}}
time{{font-size:12.5px;color:var(--muted);padding-top:2px}} ol.ledger p{{margin:2px 0 0;color:var(--muted);font-size:13.5px}}
ul.plain{{margin:0;padding-left:18px}} ul.plain li{{margin:8px 0;max-width:80ch}} .ev{{display:block;font-size:12.5px;color:var(--muted)}}
.tag{{display:inline-block;font-size:11.5px;font-weight:600;color:var(--watch);margin-right:8px}}
.tbl{{overflow-x:auto;border:1px solid var(--line);background:var(--paper)}} table{{border-collapse:collapse;width:100%;font-size:13.5px}}
th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}} th{{font-weight:600;color:var(--muted);font-size:12.5px}}
footer{{margin-top:40px;font-size:12.5px;color:var(--muted)}} .stale{{color:var(--risk);font-weight:600}} .ok{{color:var(--opp)}}
@media (max-width:640px){{ol.ledger li{{grid-template-columns:1fr}} main{{padding:20px 14px 48px}}}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style></head><body><main>
<header class="top"><div><h1>{E(D.get("title","Executive Command Center"))}</h1>
<p class="ctx">As of <b>{E(D["asof"])}</b> · compared with the review of <b>{E(D.get("previous_review","—"))}</b></p></div>
<p class="ctx">Business: <b>{E(c["business_model"])}</b>, {E(c["industry"])}, {E(c["scale"])} (context confidence {c["confidence"]:.0%})</p></header>
<h2>How are we doing?</h2><div role="tablist" aria-label="Executive views">{tabs}</div>{panels}
<h2>What changed since the last review?</h2><ol class="ledger">{chg}</ol>
<h2>Why did it change?</h2><ul class="plain">{drv}</ul>
<h2>What happens next?</h2><p class="q">Predictions, not facts. Each shows its basis.</p><ul class="plain">{nxt}</ul>
<h2>What should I do?</h2><div class="tbl"><table><thead><tr><th>Action</th><th>Owner</th><th>By</th><th>Expected impact</th><th>Approval</th></tr></thead><tbody>{act}</tbody></table></div>
<footer><p><strong>Not shown because the data does not support it:</strong></p><ul class="plain">{uns}</ul><p>Data sources: {src}</p></footer>
</main><script>
document.querySelectorAll('[role=tab]').forEach(t=>t.addEventListener('click',()=>{{
 document.querySelectorAll('[role=tab]').forEach(x=>x.setAttribute('aria-selected',x===t));
 document.querySelectorAll('.panel').forEach(p=>p.hidden=p.dataset.v!==t.dataset.v);}}));
</script></body></html>"""
open(a.out, "w").write(page)
print(json.dumps({"written": a.out, "views": list(views), "kpis_shown": len(K), "unsupported_listed": len(D.get("unsupported", []))}))
