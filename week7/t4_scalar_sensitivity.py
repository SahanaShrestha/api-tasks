"""
Week 7 — T4: Scaler Sensitivity Experiment
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.impute import SimpleImputer

RANDOM_STATE = 42

# ── Sample mixed-scale dataset ─────────────────────────────────────────────────
np.random.seed(RANDOM_STATE)
n = 600
df = pd.DataFrame({
    "age":       np.random.randint(18, 65, n).astype(float),       # tens
    "income":    np.random.normal(50000, 15000, n),                 # thousands
    "score":     np.random.uniform(0, 100, n),                      # 0-100
    "balance":   np.random.normal(500000, 200000, n),               # millions
    "purchases": np.random.poisson(20, n).astype(float),
    "target":    np.random.choice([0, 1], n),
})

y = df["target"]
X = df.drop(columns=["target"])
X_imp = pd.DataFrame(SimpleImputer(strategy="median").fit_transform(X), columns=X.columns)

SCALERS = {
    "Raw (None)":     None,
    "StandardScaler": StandardScaler(),
    "MinMaxScaler":   MinMaxScaler(),
    "RobustScaler":   RobustScaler(),
}
MODELS = {
    "KNN (k=5)": KNeighborsClassifier(n_neighbors=5),
    "SVM":       SVC(kernel="rbf", random_state=RANDOM_STATE),
}

def run_experiment(X_data, y_data, label):
    rows = []
    X_tr_raw, X_te_raw, y_tr, y_te = train_test_split(
        X_data, y_data, test_size=0.2, random_state=RANDOM_STATE, stratify=y_data)
    for sname, scaler in SCALERS.items():
        if scaler:
            sc = type(scaler)()
            Xtr, Xte = sc.fit_transform(X_tr_raw), sc.transform(X_te_raw)
        else:
            Xtr, Xte = X_tr_raw.values, X_te_raw.values
        for mname, model in MODELS.items():
            m = type(model)(**model.get_params())
            m.fit(Xtr, y_tr)
            rows.append({"Dataset": label, "Scaler": sname, "Model": mname,
                         "Accuracy": round(accuracy_score(y_te, m.predict(Xte)), 4)})
    return pd.DataFrame(rows)

res_normal  = run_experiment(X_imp, y, "Normal")

# Inject 5 outliers
outlier_rows = pd.DataFrame({c: [X_imp[c].mean() + 50*X_imp[c].std()]*5 for c in X_imp.columns})
X_out = pd.concat([X_imp, outlier_rows], ignore_index=True)
y_out = pd.concat([y, pd.Series([0]*5)], ignore_index=True)
res_outlier = run_experiment(X_out, y_out, "With Outliers")

all_results = pd.concat([res_normal, res_outlier])
print(all_results.to_string(index=False))

# Grouped bar chart
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
scaler_order = list(SCALERS.keys())
colors = {"KNN (k=5)": "#6C63FF", "SVM": "#2EC4B6"}
bw = 0.35

for ax, (lbl, res) in zip(axes, [("Normal", res_normal), ("With Outliers", res_outlier)]):
    x = np.arange(len(scaler_order))
    for i, mname in enumerate(MODELS):
        accs = [res.loc[(res.Scaler==s)&(res.Model==mname), "Accuracy"].values[0] for s in scaler_order]
        bars = ax.bar(x + (i-0.5)*bw, accs, width=bw, color=colors[mname], label=mname, alpha=0.88, edgecolor="white")
        for bar, val in zip(bars, accs):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.002,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_title(f"Dataset: {lbl}", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(scaler_order, rotation=12, ha="right", fontsize=9)
    ax.set_ylabel("Accuracy"); ax.set_ylim(0, 1.08)
    ax.legend(); ax.grid(axis="y", linestyle="--", alpha=0.4)

plt.suptitle("T4 — Scaler Sensitivity: KNN vs SVM × 4 Scalers", fontweight="bold")
plt.tight_layout()
plt.savefig("t4_scaler_sensitivity.png", dpi=150)
plt.show()

print("""
Conclusion:
  Without scaling, KNN and SVM are dominated by high-magnitude features
  (e.g. balance in hundreds of thousands), ignoring low-magnitude ones.

  After outlier injection:
    MinMaxScaler  — worst affected; outliers compress all other values into
                    a tiny range, destroying variance and accuracy.
    StandardScaler — moderate impact; mean/std shift but less catastrophic.
    RobustScaler  — most stable; uses median + IQR, resistant to extremes.

  Recommendation: use RobustScaler as your default for real-world data.
  Use StandardScaler only on clean, Gaussian-ish data.
  Avoid MinMaxScaler unless outliers have already been removed.
""")
print("✅ T4 complete.")
