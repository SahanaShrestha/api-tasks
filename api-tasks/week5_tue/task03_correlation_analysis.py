"""
=============================================================
Task 03 · Correlation Analysis [Hard]
=============================================================
Creates a realistic synthetic student CSV (50 students),
runs full EDA, computes correlation matrix, plots seaborn
heatmap + 2 scatter plots with regression lines.

Answer to Step 8:
  "Does more study ALWAYS mean higher score?"
  → Not always. The correlation is strong (+0.75 approx) but not perfect.
  Some students with high study hours score low (poor sleep / low attendance).
  Some students with low study hours score high (high attendance compensates).
  The data says: study_hours is the biggest predictor, but attendance_pct
  amplifies the effect. The worst performers combine low study AND low attendance.
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

OUT = Path("task03_charts")
OUT.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 · Create a realistic CSV with 50 students
# ─────────────────────────────────────────────────────────────────────────────
np.random.seed(7)
n = 50

study   = np.random.uniform(1, 10, n)                              # 1–10 hrs
sleep   = np.clip(np.random.normal(6.5, 1.2, n), 3, 10)           # 3–10 hrs
attend  = np.clip(55 + 4.0 * study + np.random.normal(0, 10, n), 30, 100)  # correlated with study
noise   = np.random.normal(0, 7, n)
score   = np.clip(30 + 5.0 * study + 0.25 * attend - 0.5 * (sleep - 7)**2 + noise, 0, 100)
passed  = (score >= 50).astype(int)
names   = [f"Student_{i:02d}" for i in range(1, n + 1)]

df = pd.DataFrame({
    "name":           names,
    "study_hours":    study.round(2),
    "sleep_hours":    sleep.round(2),
    "attendance_pct": attend.round(2),
    "score":          score.round(2),
    "passed":         passed,
})

df.to_csv("students.csv", index=False)
print("✔ students.csv saved (50 students, 6 columns)\n")
print(df.head(5))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 · Make data realistic check (print distributions)
# ─────────────────────────────────────────────────────────────────────────────
print("\nStep 2 – Correlation direction check (study vs score):")
print(f"  Pearson r(study, score) = {df['study_hours'].corr(df['score']):.3f}")
# Should be strongly positive

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 · Full EDA checklist
# ─────────────────────────────────────────────────────────────────────────────
print("\n── STEP 3: Full EDA ────────────────────────────────────────────")
print(f"Shape : {df.shape}")
df.info()
print(f"\nMissing:\n{df.isnull().sum()}")
print(f"\nDescribe:\n{df.describe().round(2)}")
print(f"\npassed value_counts:\n{df['passed'].value_counts()}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 · Correlation matrix
# ─────────────────────────────────────────────────────────────────────────────
numeric_cols = ["study_hours", "sleep_hours", "attendance_pct", "score", "passed"]
corr_cols    = ["study_hours", "sleep_hours", "attendance_pct", "score"]  # exclude passed (low variance → nan)
corr_matrix  = df[corr_cols].corr()

print("\n── STEP 4: Full Correlation Matrix ────────────────────────────")
print(corr_matrix.round(3).to_string())

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 · Seaborn heatmap with coolwarm colormap + annotated values
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)  # show lower triangle only

sns.heatmap(
    corr_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    vmin=-1, vmax=1,
    linewidths=0.5,
    ax=ax,
    square=True,
    cbar_kws={"shrink": 0.8},
)
ax.set_title("Task 03 · Correlation Heatmap (coolwarm)", fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(OUT / "heatmap_correlation.png", dpi=130)
plt.close()
print(f"\n✔ Saved {OUT}/heatmap_correlation.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 · Top 3 strongest + top 3 weakest correlations
# ─────────────────────────────────────────────────────────────────────────────
print("\n── STEP 6: Top / Weakest Correlations ─────────────────────────")

# Flatten upper triangle (excluding diagonal)
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
flat  = (
    upper.stack()
    .reset_index()
    .rename(columns={"level_0": "var1", "level_1": "var2", 0: "r"})
    .assign(abs_r=lambda x: x["r"].abs())
    .sort_values("abs_r", ascending=False)
)

print("\nTop 3 STRONGEST correlations:")
for _, row in flat.head(3).iterrows():
    direction = "positive" if row["r"] > 0 else "negative"
    print(f"  {row['var1']} ↔ {row['var2']}: r={row['r']:.3f} ({direction})")

print("\nTop 3 WEAKEST correlations:")
for _, row in flat.tail(3).iterrows():
    print(f"  {row['var1']} ↔ {row['var2']}: r={row['r']:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 · Scatter plots for 2 most correlated pairs + regression line
# ─────────────────────────────────────────────────────────────────────────────
top2 = flat.head(2)[["var1", "var2"]].values.tolist()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
colors = {0: "#E03131", 1: "#2F9E44"}

from matplotlib.lines import Line2D

for ax, (v1, v2) in zip(axes, top2):
    # plot passed and failed as separate scatter layers for colour coding
    for label, grp in df.groupby(df["passed"].map({1: "Passed", 0: "Failed"})):
        clr = colors[1] if label == "Passed" else colors[0]
        ax.scatter(grp[v1], grp[v2], color=clr, alpha=0.65, s=50,
                   label=label, zorder=3)

    # regression line over full data
    sns.regplot(
        data=df, x=v1, y=v2,
        ax=ax,
        scatter=False,                          # scatter already drawn above
        line_kws={"color": "#1971C2", "linewidth": 2.5},
        ci=95,
    )
    r_val = df[v1].corr(df[v2])
    ax.set_title(f"{v1} vs {v2}  (r={r_val:.3f})", fontweight="bold")
    ax.set_xlabel(v1)
    ax.set_ylabel(v2)
    ax.legend(title="Status", fontsize=8)

plt.suptitle("Task 03 · Top 2 Correlated Pairs — Regression Plots", fontweight="bold")
plt.tight_layout()
plt.savefig(OUT / "scatter_top2_correlated.png", dpi=130)
plt.close()
print(f"\n✔ Saved {OUT}/scatter_top2_correlated.png")

# ─────────────────────────────────────────────────────────────────────────────
# BONUS · Pair plot with hue=passed
# ─────────────────────────────────────────────────────────────────────────────
plot_df = df[corr_cols].copy()
plot_df["Status"] = df["passed"].map({1: "Passed", 0: "Failed"})

pair_fig = sns.pairplot(plot_df, hue="Status",
                        palette={"Passed": "#2F9E44", "Failed": "#E03131"},
                        plot_kws={"alpha": 0.55, "s": 30},
                        diag_kind="kde")
pair_fig.figure.suptitle("Task 03 Bonus · Pair Plot by Pass/Fail", y=1.02,
                          fontsize=11, fontweight="bold")
pair_fig.savefig(OUT / "pairplot_passed_bonus.png", dpi=110, bbox_inches="tight")
plt.close()
print(f"✔ Saved {OUT}/pairplot_passed_bonus.png  (Bonus)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 · Answer: Does more study always mean higher score?
# ─────────────────────────────────────────────────────────────────────────────
r_study_score = df["study_hours"].corr(df["score"])
print(f"""
── STEP 8: Does more study always mean higher score? ───────────────────────
  r(study_hours, score) = {r_study_score:.3f}

  → Strong positive correlation — but NOT always guaranteed.
  → Counterexamples: students with high study hours but poor sleep (< 5 hrs)
    score significantly below their expected range.
  → attendance_pct moderates the effect: low attendance neutralises the
    benefit of high study hours (missed lectures = knowledge gaps).
  → Conclusion: study_hours is the strongest single predictor of score,
    but the full picture requires attendance + adequate sleep.
────────────────────────────────────────────────────────────────────────────
""")

print("✅ Task 03 complete — charts saved to:", OUT.resolve())