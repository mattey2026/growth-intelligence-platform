#!/usr/bin/env python3
"""
scenario_model.py: driver-based what-if model for revenue, pipeline, pricing, and capacity.

USAGE: python scenario_model.py scenarios.json [--out results.json]

scenarios.json:
{
  "period": "FY27 H1",
  "target": 12000000,
  "base": {"reps": 40, "ramped_share": 0.85, "pipeline_per_rep": 1500000,
           "win_rate": 0.24, "avg_price_change_pct": 0, "price_elasticity": -0.5,
           "cycle_slip_share": 0.10, "existing_closed": 0},
  "scenarios": {"best": {"win_rate": 0.28, "reps": 44}, "worst": {"win_rate": 0.20, "cycle_slip_share": 0.2},
                "price_up_5": {"avg_price_change_pct": 5}}
}

Model (every term is explicit; change the drivers, not the formula):
  effective_reps     = reps × ramped_share
  pipeline           = effective_reps × pipeline_per_rep
  price_factor       = 1 + price_change%
  win_rate_adjusted  = win_rate × (1 + elasticity × price_change%)   # elasticity is an ASSUMPTION
  bookings           = existing_closed + pipeline × win_rate_adjusted × price_factor × (1 − cycle_slip_share)
Outputs each scenario's bookings, its gap to target, the pipeline needed to hit
target, the reps needed, and a one-at-a-time sensitivity (tornado) of ±10% on
each driver around the base case.
"""
import argparse, copy, json

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--out")
a = ap.parse_args()
cfg = json.load(open(a.file))
base = cfg["base"]
target = cfg.get("target")


def run(d):
    eff = d["reps"] * d.get("ramped_share", 1)
    pipe = eff * d["pipeline_per_rep"]
    pc = d.get("avg_price_change_pct", 0) / 100
    wr = max(0.0, min(1.0, d["win_rate"] * (1 + d.get("price_elasticity", 0) * pc)))
    conv = wr * (1 + pc) * (1 - d.get("cycle_slip_share", 0))
    book = d.get("existing_closed", 0) + pipe * conv
    r = {"effective_reps": round(eff, 1), "pipeline": round(pipe), "win_rate_adjusted": round(wr, 4), "bookings": round(book)}
    if target:
        r["gap_to_target"] = round(book - target)
        r["pipeline_needed"] = round((target - d.get("existing_closed", 0)) / conv) if conv > 0 else None
        r["reps_needed"] = round(r["pipeline_needed"] / (d["pipeline_per_rep"] * d.get("ramped_share", 1)), 1) if r["pipeline_needed"] else None
        r["coverage_ratio"] = round(pipe / target, 2)
    return r


out = {"period": cfg.get("period"), "target": target, "formula": __doc__.split("Model")[1].split("Outputs")[0].strip(),
       "scenarios": {"base": {"drivers": base, **run(base)}}}
for name, ov in cfg.get("scenarios", {}).items():
    d = {**base, **ov}
    out["scenarios"][name] = {"changed_drivers": ov, **run(d)}

# Tornado: shift each numeric driver ±10% (one at a time) and record the bookings swing.
torn = []
b0 = run(base)["bookings"]
for k, v in base.items():
    if isinstance(v, (int, float)) and v != 0 and k != "existing_closed":
        lo = run({**base, k: v * 0.9})["bookings"]
        hi = run({**base, k: v * 1.1})["bookings"]
        torn.append({"driver": k, "minus10pct": lo - b0, "plus10pct": hi - b0, "swing": abs(hi - lo)})
out["sensitivity_tornado"] = sorted(torn, key=lambda t: -t["swing"])
out["assumptions"] = ["Drivers are independent unless changed together in a scenario",
                      "Price elasticity is an assumption unless measured; test a range",
                      "Linear pipeline-to-bookings conversion within the period"]
print(json.dumps(out, indent=2))
if a.out:
    json.dump(out, open(a.out, "w"), indent=2)
