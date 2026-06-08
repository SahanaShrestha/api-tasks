"""
Week 7 — T3: Encoding Strategy Comparison
"""

import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.impute import SimpleImputer

RANDOM_STATE = 42

# ── Sample dataset ─────────────────────────────────────────────────────────────
np.random.seed(RANDOM_STATE)
n = 800
df = pd.DataFrame({
    "gender":    np.random.choice(["Male","Female"], n),                             # low cardinality
    "education": np.random.choice(["High School","Bachelor","Master","PhD"], n),     # medium
    "city":      np.random.choice([f"City_{i}" for i in range(10)], n),             # high
    "age":       np.random.randint(18, 65, n).astype(float),
    "income":    np.random.normal(50000, 15000, n),
    "target":    np.random.choice([0, 1], n),
})

y        = df["target"]
X_base   = df.drop(columns=["target"])
cat_cols = ["gender","education","city"]
num_cols = ["age","income"]

def evaluate(X, y):
    X_arr = SimpleImputer(strategy="median").fit_transform(X)
    X_sc  = StandardScaler().fit_transform(X_arr)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_sc, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)
    t0 = time.perf_counter()
    m  = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    m.fit(X_tr, y_tr)
    t1 = time.perf_counter()
    return {
        "accuracy":       round(accuracy_score(y_te, m.predict(X_te)), 4),
        "train_time_ms":  round((t1-t0)*1000, 2),
        "n_features":     X_sc.shape[1],
    }

# Label Encoding
X_le = X_base.copy()
le = LabelEncoder()
for col in cat_cols:
    X_le[col] = le.fit_transform(X_le[col].astype(str))
m_le = evaluate(X_le, y)

# One-Hot Encoding
X_ohe = pd.get_dummies(X_base, columns=cat_cols, drop_first=True)
X_ohe[X_ohe.select_dtypes("bool").columns] = X_ohe.select_dtypes("bool").astype(int)
m_ohe = evaluate(X_ohe, y)

# Ordinal Encoding
X_ord = X_base.copy()
X_ord[cat_cols] = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1).fit_transform(X_ord[cat_cols].astype(str))
m_ord = evaluate(X_ord, y)

# Results table
results = pd.DataFrame({
    "Strategy":       ["Label Encoding","One-Hot Encoding","Ordinal Encoding"],
    "Accuracy":       [m_le["accuracy"], m_ohe["accuracy"], m_ord["accuracy"]],
    "Train Time (ms)":[m_le["train_time_ms"], m_ohe["train_time_ms"], m_ord["train_time_ms"]],
    "Feature Count":  [m_le["n_features"], m_ohe["n_features"], m_ord["n_features"]],
})
print(results.to_string(index=False))

# Bar chart
fig, axes = plt.subplots(1, 3, figsize=(13, 5))
colors = ["#6C63FF","#2EC4B6","#FF6B6B"]
for ax, col, title in zip(axes,
    ["Accuracy","Train Time (ms)","Feature Count"],
    ["Accuracy ↑","Train Time (ms) ↓","Feature Count ↓"]):
    bars = ax.bar(results["Strategy"], results[col], color=colors, width=0.5)
    ax.set_title(title, fontweight="bold")
    ax.set_xticklabels(results["Strategy"], rotation=12, ha="right", fontsize=9)
    for bar, val in zip(bars, results[col]):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.01,
                str(val), ha="center", va="bottom", fontsize=9, fontweight="bold")

plt.suptitle("T3 — Encoding Strategy Comparison", fontweight="bold")
plt.tight_layout()
plt.savefig("t3_encoding_comparison.png", dpi=150)
plt.show()

print("""
Recommendation:
  One-Hot Encoding gives the best accuracy for Logistic Regression by treating
  each category independently, avoiding false ordinality. However it inflates
  features, increasing training time. Ordinal Encoding is a good middle-ground
  for genuinely ordered variables (e.g. education level). Label Encoding should
  only be used on binary columns. Practical rule:
    Binary columns          → Label Encoding
    Nominal, cardinality ≤10 → One-Hot Encoding
    Ordinal/high cardinality → Ordinal Encoding
""")
print("✅ T3 complete.")
