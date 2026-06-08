"""
Week 7 — T2: Feature Engineering Challenge
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score

RANDOM_STATE = 42

# ── Load sample Uber-style dataset ────────────────────────────────────────────
np.random.seed(RANDOM_STATE)
n = 1000
base = pd.Timestamp("2023-01-01")
datetimes = [base + pd.Timedelta(minutes=int(x))
             for x in np.random.randint(0, 525600, n)]

df = pd.DataFrame({
    "pickup_datetime":  datetimes,
    "distance_km":      np.abs(np.random.exponential(8, n)),
    "fare":             np.abs(np.random.exponential(20, n)),
    "passenger_count":  np.random.randint(1, 7, n).astype(float),
    "surge_multiplier": np.random.choice([1.0, 1.5, 2.0, 2.5], n),
    "target":           np.random.choice([0, 1], n),
})
df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"])
print(f"Loaded dataset: {df.shape}")

# ── Utility ────────────────────────────────────────────────────────────────────
def quick_eval(X, y, label):
    imp = SimpleImputer(strategy="median")
    X_imp = imp.fit_transform(X.select_dtypes(include="number"))
    X_scaled = StandardScaler().fit_transform(X_imp)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_scaled, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    model.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, model.predict(X_te))
    print(f"  Accuracy [{label}]: {acc:.4f}")
    return acc

# ── Baseline ───────────────────────────────────────────────────────────────────
y = df["target"]
acc_before = quick_eval(df.drop(columns=["target","pickup_datetime"]), y, "BEFORE")

# ── Feature Engineering ────────────────────────────────────────────────────────
print("\n── Engineering features ────────────────────────────────────────────────")
df_eng = df.copy()

df_eng["day_of_week"]   = df_eng["pickup_datetime"].dt.dayofweek
df_eng["hour"]          = df_eng["pickup_datetime"].dt.hour
df_eng["is_weekend"]    = (df_eng["day_of_week"] >= 5).astype(int)
df_eng["fare_per_km"]   = df_eng["fare"] / (df_eng["distance_km"] + 1e-6)
df_eng["revenue_proxy"] = df_eng["fare"] * df_eng["passenger_count"]
df_eng["log_distance"]  = np.log1p(df_eng["distance_km"])
df_eng["fare_bin"]      = pd.qcut(df_eng["fare"], q=4, labels=False)

features = ["day_of_week","hour","is_weekend","fare_per_km","revenue_proxy","log_distance","fare_bin"]
for f in features:
    print(f"  ✅ {f}")

# ── Post-engineering accuracy ──────────────────────────────────────────────────
print()
acc_after = quick_eval(df_eng.drop(columns=["target","pickup_datetime"]), y, "AFTER ")
print(f"\n  Accuracy delta: {acc_after - acc_before:+.4f}")

# ── Log transform visualisation ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].hist(df_eng["distance_km"], bins=50, color="#6C63FF", edgecolor="white")
axes[0].set_title("distance_km  (raw — right-skewed)")
axes[1].hist(df_eng["log_distance"], bins=50, color="#2EC4B6", edgecolor="white")
axes[1].set_title("log_distance  (after log1p — more normal)")
plt.suptitle("T2 — Log Transform Effect", fontweight="bold")
plt.tight_layout()
plt.savefig("t2_log_transform.png", dpi=150)
plt.show()

print("\nWhy each feature helps:")
reasons = {
    "day_of_week":   "Weekly seasonality — Mon/Fri behave differently",
    "hour":          "Rush-hour peaks drive demand spikes",
    "is_weekend":    "Weekend leisure vs weekday commute split",
    "fare_per_km":   "Normalises fare, removes effect of trip length",
    "revenue_proxy": "Captures total trip value not just per-person fare",
    "log_distance":  "Compresses extreme distances, improves linearity",
    "fare_bin":      "Ordinal price tier easier for linear models",
}
for f, r in reasons.items():
    print(f"  {f:20s} → {r}")

print("\n✅ T2 complete.")
