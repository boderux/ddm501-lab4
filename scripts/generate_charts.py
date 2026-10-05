import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

charts_dir = Path("artifacts/charts")
charts_dir.mkdir(parents=True, exist_ok=True)

with open("artifacts/profile_simulation_results.json") as f:
    results = json.load(f)

# Style settings
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "Arial", "DejaVu Sans", "Helvetica"

# 1. Decision Mix Chart
profiles = ["normal", "drifted_005", "drifted_015", "drifted_full", "unfair"]
labels = ["Normal", "Drifted (0.05)", "Drifted (0.15)", "Drifted (Full)", "Unfair"]
approve = [results[p]["approve_pct"] for p in profiles]
review = [results[p]["review_pct"] for p in profiles]
decline = [results[p]["decline_pct"] for p in profiles]

x = np.arange(len(labels))
width = 0.55

fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar(x, approve, width, label="APPROVE", color="#2ecc71")
b2 = ax.bar(x, review, width, bottom=approve, label="REVIEW", color="#f39c12")
b3 = ax.bar(x, decline, width, bottom=np.array(approve) + np.array(review), label="DECLINE", color="#e74c3c")

ax.set_ylabel("Percentage of Total Decisions (%)", fontsize=11, fontweight="bold")
ax.set_title("Decision Mix Across Traffic Profiles (N = 400 per profile)", fontsize=13, fontweight="bold", pad=12)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=10)
ax.set_ylim(0, 105)
ax.legend(loc="upper right", frameon=True)

for i in range(len(labels)):
    ax.text(i, approve[i]/2, f"{approve[i]:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
    if review[i] > 10:
        ax.text(i, approve[i] + review[i]/2, f"{review[i]:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
    if decline[i] > 10:
        ax.text(i, approve[i] + review[i] + decline[i]/2, f"{decline[i]:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

plt.tight_layout()
fig.savefig(charts_dir / "decision_mix.png", dpi=200)
plt.close(fig)

# 2. Per-feature PSI Chart across Drifted Profiles
fig, ax = plt.subplots(figsize=(10, 5))
features = ["payment_ratio", "utilisation_ratio", "LIMIT_BAL", "AGE", "PAY_0", "max_delay"]
x_feat = np.arange(len(features))
w = 0.2

for idx, p in enumerate(["normal", "drifted_005", "drifted_015", "drifted_full"]):
    vals = [results[p]["monitoring"]["feature_psi"].get(f, 0.0) for f in features]
    ax.bar(x_feat + idx * w, vals, w, label=labels[idx])

ax.axhline(0.10, color="#f39c12", linestyle="--", linewidth=1.2, label="Moderate Drift Threshold (0.10)")
ax.axhline(0.25, color="#e74c3c", linestyle="--", linewidth=1.2, label="Significant Drift Threshold (0.25)")

ax.set_ylabel("Population Stability Index (PSI)", fontsize=11, fontweight="bold")
ax.set_title("PSI by Feature Across Shift Strengths (Non-uniform Sensitivity)", fontsize=13, fontweight="bold", pad=12)
ax.set_xticks(x_feat + 1.5 * w)
ax.set_xticklabels(features, rotation=15, ha="right", fontsize=10)
ax.legend(loc="upper right", frameon=True)

plt.tight_layout()
fig.savefig(charts_dir / "psi_by_feature.png", dpi=200)
plt.close(fig)

# 3. Drift Score vs Fairness Gap (Drifted vs Unfair Comparison)
fig, ax = plt.subplots(figsize=(8, 5))
comp_profiles = ["normal", "drifted_015", "unfair"]
comp_labels = ["Normal", "Drifted (0.15)", "Unfair"]
ds_vals = [results[p]["monitoring"]["drift_score"] for p in comp_profiles]
fg_vals = [results[p]["monitoring"]["fairness_gap"] for p in comp_profiles]

x_comp = np.arange(len(comp_labels))
width_comp = 0.35

ax.bar(x_comp - width_comp/2, ds_vals, width_comp, label="Aggregate Drift Score (PSI)", color="#3498db")
ax.bar(x_comp + width_comp/2, fg_vals, width_comp, label="Fairness Gap (Selection Rate)", color="#9b59b6")

ax.axhline(0.25, color="#2980b9", linestyle=":", label="Drift Alert Threshold (0.25)")
ax.axhline(0.10, color="#8e44ad", linestyle=":", label="Fairness Alert Threshold (0.10)")

ax.set_ylabel("Metric Value", fontsize=11, fontweight="bold")
ax.set_title("Distinguishing Systemic Drift vs Targeted Unfairness", fontsize=13, fontweight="bold", pad=12)
ax.set_xticks(x_comp)
ax.set_xticklabels(comp_labels, fontsize=10)
ax.legend(loc="upper left", frameon=True)

for i in range(len(comp_labels)):
    ax.text(i - width_comp/2, ds_vals[i] + 0.02, f"{ds_vals[i]:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.text(i + width_comp/2, fg_vals[i] + 0.02, f"{fg_vals[i]:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax.set_ylim(0, 1.3)
plt.tight_layout()
fig.savefig(charts_dir / "drift_vs_fairness.png", dpi=200)
plt.close(fig)

print("Charts successfully generated in artifacts/charts/")
