#!/usr/bin/env python3
"""
render_dashboard.py: Dashboard Contract → self-contained Claude Artifact HTML (Enterprise Growth Command Center).
The renderer is generic: it works for any entity whose contract validates against schemas/dashboard.schema.json.
It performs no business computation; it embeds the contract and the renderer assets.
USAGE: render_dashboard.py --contract contract.json --out dashboard.html [--no-validate]
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(os.path.dirname(HERE), "assets")
ap = argparse.ArgumentParser(); ap.add_argument("--contract", required=True); ap.add_argument("--out", required=True); ap.add_argument("--no-validate", action="store_true"); a = ap.parse_args()
C = json.load(open(a.contract))
if not a.no_validate:
    d = HERE
    for _ in range(6):
        p = os.path.join(d, "schemas", "dashboard.schema.json")
        if os.path.exists(p): break
        d = os.path.dirname(d)
    import jsonschema
    errs = list(jsonschema.Draft202012Validator(json.load(open(p))).iter_errors(C))
    if errs: print(json.dumps({"error": "contract fails schema", "errors": [f"{'/'.join(map(str, e.path))}: {e.message[:100]}" for e in errs[:10]]})); sys.exit(2)
R = lambda f: open(os.path.join(A, f), encoding="utf-8").read()
payload = json.dumps(C, ensure_ascii=False, default=str).replace("</", "<\\/")          # safe inside <script>
html = (R("command-center.template.html").replace("{{TITLE}}", f"{C['dashboard']['name']}: {C['dashboard']['entity_name']}")
        .replace("{{CSS}}", R("command-center.css")).replace("{{JS}}", R("command-center.core.js") + "\n" + R("command-center.widgets.js")).replace("{{CONTRACT}}", payload))
open(a.out, "w", encoding="utf-8").write(html)
print(json.dumps({"artifact": a.out, "bytes": len(html.encode()), "entity": C["dashboard"]["entity_name"], "persona": C["dashboard"]["persona"], "views": list(C["layout"]["views"])}))
