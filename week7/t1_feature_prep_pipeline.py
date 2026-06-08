"""
Week 7 — T1: Full Feature Preparation Pipeline
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

RANDOM_STATE = 42

# ── Load sample data ───────────────────────────────────────────────────────────
np.random.seed(RANDOM_STATE)
n = 500
df = pd.DataFrame({
    "age":          np.random.randint(18, 70, n).astype(float),
    "income":       np.random.normal(50000, 15000, n),
    "score":        np.random.uniform(0, 100, n),
    "visits":       np.random.poisson(5, n).astype(float),
    "region":       np.random.choice(["North","South","East","West"], n),
    "education":    np.random.choice(["High School","Bachelor","Master","PhD"], n),
    "employed":     np.random.choice(["Yes","No"], n),
    "row_id":       np.arange(n),        # low-value: pure identifier
    "constant_col": "same_value",        # low-value: zero variance
    "target":       np.random.choice([0, 1], n),
})
# Inject ~10% nulls
for col in ["age","income","score","region","education"]:
    mask = np.random.choice([True, False], n, p=[0.10, 0.90])
    df.loc[mask, col] = np.nan

print(f"Loaded dataset: {df.shape[0]} rows × {df.shape[1]} cols")
print(df.head())
print(f"\nMissing values:\n{df.isnull().sum()}")

# ── Step 1: Drop low-value columns ────────────────────────────────────────────
print("\n── Step 1: Dropping low-value columns ─────────────────────────────────")
drops = {}
id_like  = [c for c in df.columns if c.lower() in {"row_id","id","index","uuid","key"}]
zero_var = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
high_null= [c for c in df.columns if df[c].isnull().mean() > 0.60]
drops["Identifier columns (no predictive signal)"] = id_like
drops["Constant/zero-variance columns"]            = zero_var
drops["Columns with >60% missing values"]          = high_null

all_drops = list({c for cols in drops.values() for c in cols if c != "target"})
for reason, cols in drops.items():
    filtered = [c for c in cols if c != "target"]
    if filtered:
        print(f"  Dropping {filtered}  →  {reason}")

df.drop(columns=all_drops, inplace=True, errors="ignore")

# ── Step 2: Separate target & column types ────────────────────────────────────
y = df["target"]
X = df.drop(columns=["target"])
num_cols = X.select_dtypes(include=["number"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object","category"]).columns.tolist()
print(f"\n  Numeric: {num_cols}")
print(f"  Categorical: {cat_cols}")

# ── Step 3: Impute missing values (2 strategies) ──────────────────────────────
print("\n── Step 3: Imputing ────────────────────────────────────────────────────")
# Numeric → median (robust to outliers)
imputer_num = SimpleImputer(strategy="median")
X[num_cols] = imputer_num.fit_transform(X[num_cols])
print("  [Numeric]      MEDIAN — robust to skewed distributions")

# Categorical → most frequent (mode)
imputer_cat = SimpleImputer(strategy="most_frequent")
X[cat_cols] = imputer_cat.fit_transform(X[cat_cols])
print("  [Categorical]  MOST FREQUENT — preserves dominant category")

# ── Step 4: Encode categoricals ───────────────────────────────────────────────
print("\n── Step 4: Encoding ────────────────────────────────────────────────────")
le = LabelEncoder()
ohe_candidates = []
for col in cat_cols:
    n_unique = X[col].nunique()
    if n_unique == 2:
        X[col] = le.fit_transform(X[col].astype(str))
        print(f"  {col:20s}  unique={n_unique}  → Label Encoded (binary)")
    elif n_unique <= 10:
        ohe_candidates.append(col)
        print(f"  {col:20s}  unique={n_unique}  → One-Hot Encoded (nominal)")
    else:
        X[col] = le.fit_transform(X[col].astype(str))
        print(f"  {col:20s}  unique={n_unique}  → Label Encoded (high cardinality)")

if ohe_candidates:
    X = pd.get_dummies(X, columns=ohe_candidates, drop_first=True)

# ── Step 5: StandardScaler ────────────────────────────────────────────────────
print("\n── Step 5: Scaling ─────────────────────────────────────────────────────")
num_cols_final = X.select_dtypes(include=["number"]).columns.tolist()
scaler = StandardScaler()
X[num_cols_final] = scaler.fit_transform(X[num_cols_final])
print(f"  Scaled {len(num_cols_final)} numeric columns (mean≈0, std≈1)")

# ── Step 6: 80/20 train-test split ────────────────────────────────────────────
print("\n── Step 6: Train-Test Split ────────────────────────────────────────────")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
print(f"  X_train: {X_train.shape}  |  X_test: {X_test.shape}")
print(f"  Class balance (train): {dict(y_train.value_counts())}")

print("\n✅ T1 complete — X_train, X_test, y_train, y_test ready.")
