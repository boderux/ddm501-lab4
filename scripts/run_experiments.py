import json
import random
from pathlib import Path
from fastapi.testclient import TestClient

import app.main
from pipeline.config import TARGET
from pipeline.data_ingestion import load_raw
from scripts.load_test import row_to_payload, apply_drift, apply_group_bias

profiles = [
    ("normal", {"strength": 1.0}),
    ("drifted_005", {"strength": 0.05}),
    ("drifted_015", {"strength": 0.15}),
    ("drifted_full", {"strength": 1.0}),
    ("unfair", {"strength": 1.0}),
]

results = {}
seed = 501
n_requests = 400

raw_data = load_raw().drop(columns=[TARGET])

with TestClient(app.main.app) as client:
    for name, kwargs in profiles:
        rng = random.Random(seed)
        sampled = raw_data.sample(n=n_requests, replace=True, random_state=seed)
        
        # Reset window between runs on the actual active window
        with app.main.window._lock:
            app.main.window._rows.clear()
            
        scores = []
        decisions = []

        for _, row in sampled.iterrows():
            payload = row_to_payload(row)
            if "drifted" in name:
                payload = apply_drift(payload, rng, kwargs["strength"])
            elif name == "unfair":
                payload = apply_group_bias(payload, rng)

            resp = client.post("/predict", json=payload)
            data = resp.json()
            scores.append(data["default_probability"])
            decisions.append(data["decision"])

        mon = client.get("/monitoring").json()
        n_dec = len(decisions)
        rev_pct = decisions.count("REVIEW") / n_dec * 100
        dec_pct = decisions.count("DECLINE") / n_dec * 100
        app_pct = decisions.count("APPROVE") / n_dec * 100
        mean_score = sum(scores) / len(scores)

        results[name] = {
            "mean_score": mean_score,
            "approve_pct": app_pct,
            "review_pct": rev_pct,
            "decline_pct": dec_pct,
            "monitoring": mon
        }

out_path = Path("artifacts/profile_simulation_results.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(results, indent=2))

print(f"{'Profile':<15} | {'Score Mean':<10} | {'APPROVE %':<10} | {'REVIEW %':<10} | {'DECLINE %':<10} | {'Drift Score':<12} | {'Status':<12} | {'Fairness Gap':<12}")
print("-" * 100)
for k, v in results.items():
    mon = v["monitoring"]
    ds = mon.get("drift_score")
    ds_str = f"{ds:.4f}" if ds is not None else "None"
    fg = mon.get("fairness_gap")
    fg_str = f"{fg:.4f}" if fg is not None else "None"
    status = mon.get("drift_status", "None")
    print(f"{k:<15} | {v['mean_score']:<10.4f} | {v['approve_pct']:<10.1f} | {v['review_pct']:<10.1f} | {v['decline_pct']:<10.1f} | {ds_str:<12} | {status:<12} | {fg_str:<12}")

print("\n=== PER-FEATURE PSI BREAKDOWN ===")
for k, v in results.items():
    psi_dict = {feat: round(val, 4) for feat, val in v["monitoring"].get("feature_psi", {}).items()}
    print(f"\n[{k}]")
    for feat, val in sorted(psi_dict.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat:<20}: {val:.4f}")
