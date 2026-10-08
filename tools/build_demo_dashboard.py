"""Build the demo Enterprise Growth Command Center: demo provider → T0 builder → renderer.
Usage: python tools/build_demo_dashboard.py [--persona sales_head] [--entity Sanofi] [--out examples/enterprise-growth-command-center.html]"""
import argparse, subprocess, sys, os, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("--persona", default="sales_head"); ap.add_argument("--entity", default="Sanofi")
ap.add_argument("--out", default=os.path.join(ROOT, "examples", "enterprise-growth-command-center.html")); a = ap.parse_args()
S = os.path.join(ROOT, "scripts"); t = tempfile.mkdtemp()
run = lambda *x: subprocess.run([sys.executable, *x], check=True)
run(os.path.join(S, "demo_provider.py"), "--entity", a.entity, "--out", os.path.join(t, "bundle.json"))
run(os.path.join(S, "dashboard_builder.py"), "--bundle", os.path.join(t, "bundle.json"), "--persona", a.persona, "--out", os.path.join(t, "contract.json"), "--validate")
run(os.path.join(ROOT, "scripts", "render_dashboard.py"), "--contract", os.path.join(t, "contract.json"), "--out", a.out)
print("Open in a browser:", a.out)
