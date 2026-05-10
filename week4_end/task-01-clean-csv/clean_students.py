# =============================================================================
# Task 01 · Clean a Messy CSV [Medium]
# Goal: Load messy_students.csv, fix all 6 data quality problems,
#       add a grade column, save to clean_students.csv, and print a
#       full cleaning report showing exactly what was changed.
#
# Problems fixed:
#   1. Nulls          — drop rows where name OR score is missing after cleaning
#   2. Duplicates     — deduplicate on (name, score) after normalisation
#   3. Casing         — normalise all names to Title Case
#   4. Type coercion  — strip quotes from score strings, cast to numeric
#   5. Whitespace     — strip leading/trailing spaces from name column
#   6. Invalid values — remove rows where score < 0 or score > 100
#
# Grade logic (applied via df['score'].apply()):
#   A → score >= 90
#   B → score >= 75
#   C → score >= 50
#   F → score <  50
# =============================================================================

import pandas as pd

# ---------------------------------------------------------------------------
# Step 1: Load the raw messy CSV
# ---------------------------------------------------------------------------
df = pd.read_csv("messy_students.csv")
rows_before = len(df)
print(f"Rows loaded from messy_students.csv: {rows_before}\n")

# Keep a snapshot for the cleaning report counters
report = {
    "nulls_dropped": 0,
    "duplicates_dropped": 0,
    "invalid_scores_dropped": 0,
    "whitespace_fixed": 0,
    "casing_fixed": 0,
    "type_coerced": 0,
}

# ---------------------------------------------------------------------------
# Step 2: Fix whitespace — strip leading/trailing spaces from 'name'
#         Also treat whitespace-only strings as NaN
# ---------------------------------------------------------------------------
before_ws = df["name"].copy()
df["name"] = df["name"].str.strip()
df["name"] = df["name"].replace("", pd.NA)           # blank after strip → NaN
report["whitespace_fixed"] = (before_ws != df["name"]).sum()

# Strip score column of surrounding whitespace too (catches '  ' cells)
df["score"] = df["score"].astype(str).str.strip()
df["score"] = df["score"].replace("", pd.NA)

# ---------------------------------------------------------------------------
# Step 3: Fix type coercion — score column stored as string e.g. '85'
#         Strip single-quotes, then cast to numeric; coerce bad values → NaN
# ---------------------------------------------------------------------------
before_type = df["score"].copy()
df["score"] = df["score"].str.replace("'", "", regex=False)  # remove quote chars
df["score"] = pd.to_numeric(df["score"], errors="coerce")    # cast; bad → NaN
report["type_coerced"] = (before_type.astype(str) != df["score"].astype(str)).sum()

# ---------------------------------------------------------------------------
# Step 4: Drop rows where name or score is null (missing values)
# ---------------------------------------------------------------------------
nulls_before = df.isnull().sum().sum()
df = df.dropna(subset=["name", "score"])
nulls_after = df.isnull().sum().sum()
report["nulls_dropped"] = rows_before - len(df)

# ---------------------------------------------------------------------------
# Step 5: Fix casing — normalise names to Title Case
# ---------------------------------------------------------------------------
before_case = df["name"].copy()
df["name"] = df["name"].str.title()
report["casing_fixed"] = (before_case != df["name"]).sum()

# ---------------------------------------------------------------------------
# Step 6: Drop invalid scores — anything below 0 or above 100 is nonsensical
# ---------------------------------------------------------------------------
rows_pre_invalid = len(df)
df = df[(df["score"] >= 0) & (df["score"] <= 100)]
report["invalid_scores_dropped"] = rows_pre_invalid - len(df)

# ---------------------------------------------------------------------------
# Step 7: Drop duplicate rows — deduplicate on (name, score) after normalisation
# ---------------------------------------------------------------------------
rows_pre_dupe = len(df)
df = df.drop_duplicates(subset=["name", "score"])
report["duplicates_dropped"] = rows_pre_dupe - len(df)

# ---------------------------------------------------------------------------
# Step 8: Add grade column using df['score'].apply()
# ---------------------------------------------------------------------------
def assign_grade(score):
    """Return letter grade based on numeric score."""
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 50:
        return "C"
    else:
        return "F"

df["grade"] = df["score"].apply(assign_grade)

# ---------------------------------------------------------------------------
# Step 9: Reset index and save to clean_students.csv
# ---------------------------------------------------------------------------
df = df.reset_index(drop=True)
rows_after = len(df)

df.to_csv("clean_students.csv", index=False)
print("clean_students.csv saved.\n")

# ---------------------------------------------------------------------------
# Step 10: Print before/after row count + full cleaning report (bonus)
# ---------------------------------------------------------------------------
print("=" * 50)
print("BEFORE / AFTER ROW COUNT")
print("=" * 50)
print(f"  Before cleaning : {rows_before} rows")
print(f"  After  cleaning : {rows_after} rows")
print(f"  Total removed   : {rows_before - rows_after} rows\n")

print("=" * 50)
print("CLEANING REPORT")
print("=" * 50)
print(f"  Whitespace fixed      : {report['whitespace_fixed']} cells")
print(f"  Type coercions        : {report['type_coerced']} cells")
print(f"  Null rows dropped     : {report['nulls_dropped']} rows")
print(f"  Casing corrections    : {report['casing_fixed']} cells")
print(f"  Invalid scores dropped: {report['invalid_scores_dropped']} rows")
print(f"  Duplicate rows dropped: {report['duplicates_dropped']} rows\n")

print("=" * 50)
print("CLEANED DATA PREVIEW")
print("=" * 50)
print(df.to_string(index=False))
