# =============================================================================
# Task 04 · Transform & Enrich [Hard]
# Goal: Take clean_students.csv from Task 01 and enrich it with multiple
#       new calculated columns using advanced Pandas transformations.
#
# Steps:
#   1. LOAD        — Load clean_students.csv into a DataFrame
#   2. GRADE       — Add grade column: A(>=90), B(>=75), C(>=60), D(>=50), F(<50)
#   3. PASSED      — Add passed column: True if score >= 50, False otherwise
#   4. CATEGORY    — Add score_category: 'High'(>=80), 'Medium'(50-79), 'Low'(<50)
#   5. RANK        — Add rank column: highest score = rank 1 using .rank(ascending=False)
#   6. GROUPBY     — Print count, mean, min, max score per grade using groupby()
#   7. SORT        — Sort final DataFrame by rank, reset index
#   8. SAVE        — Save to enriched_students.csv, print top 5 ranked students
#
# Bonus: pivot_table() — grade vs subject vs average score
#        (since clean_students.csv has no subject col, we generate mock subjects)
# =============================================================================

import pandas as pd
import numpy as np
import os
import sys

# ---------------------------------------------------------------------------
# Step 1: Load clean_students.csv from Task 01
#         Script looks in current dir; also checks ../task-01-clean-csv/
# ---------------------------------------------------------------------------
csv_path = "clean_students.csv"
fallback = os.path.join("..", "task-01-clean-csv", "clean_students.csv")

if not os.path.exists(csv_path):
    if os.path.exists(fallback):
        csv_path = fallback
        print(f"Using fallback path: {csv_path}")
    else:
        print("ERROR: clean_students.csv not found.")
        print("Run Task 01's clean_students.py first to generate it.")
        sys.exit(1)

df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} rows from {csv_path}\n")

# ---------------------------------------------------------------------------
# Step 2: Add grade column using apply() with a named function
#         Grading: A>=90, B>=75, C>=60, D>=50, F<50
# ---------------------------------------------------------------------------
def assign_grade(score):
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"

df["grade"] = df["score"].apply(assign_grade)

# ---------------------------------------------------------------------------
# Step 3: Add passed column — True if score >= 50, False otherwise
# ---------------------------------------------------------------------------
df["passed"] = df["score"] >= 50

# ---------------------------------------------------------------------------
# Step 4: Add score_category column
#         High >= 80, Medium 50-79, Low < 50
# ---------------------------------------------------------------------------
def assign_category(score):
    if score >= 80:
        return "High"
    elif score >= 50:
        return "Medium"
    else:
        return "Low"

df["score_category"] = df["score"].apply(assign_category)

# ---------------------------------------------------------------------------
# Step 5: Add rank column — highest score gets rank 1
#         method='min' means ties get the same rank
# ---------------------------------------------------------------------------
df["rank"] = df["score"].rank(ascending=False, method="min").astype(int)

# ---------------------------------------------------------------------------
# Step 6: Group by grade — print count, mean, min, max score per grade
# ---------------------------------------------------------------------------
grade_summary = df.groupby("grade")["score"].agg(
    count="count",
    mean_score="mean",
    min_score="min",
    max_score="max"
).round(2)

print("=" * 50)
print("GRADE SUMMARY (groupby)")
print("=" * 50)
print(grade_summary.to_string())
print()

# ---------------------------------------------------------------------------
# Bonus: pivot_table — grade vs subject vs average score
#        clean_students.csv has no subject column so we assign mock subjects
#        deterministically using modulo so it's reproducible
# ---------------------------------------------------------------------------
subjects = ["Math", "Science", "English"]
df["subject"] = [subjects[i % len(subjects)] for i in range(len(df))]

pivot = pd.pivot_table(
    df,
    values="score",
    index="grade",
    columns="subject",
    aggfunc="mean"
).round(2)

print("=" * 50)
print("BONUS: Pivot Table — Grade vs Subject vs Avg Score")
print("=" * 50)
print(pivot.to_string())
print()

# ---------------------------------------------------------------------------
# Step 7: Sort by rank ascending, reset index
# ---------------------------------------------------------------------------
df = df.sort_values("rank").reset_index(drop=True)

# ---------------------------------------------------------------------------
# Step 8: Save to enriched_students.csv and print top 5 ranked students
# ---------------------------------------------------------------------------
df.to_csv("enriched_students.csv", index=False)
print("Saved: enriched_students.csv")

print("\n" + "=" * 50)
print("TOP 5 RANKED STUDENTS")
print("=" * 50)
print(df[["rank", "name", "score", "grade", "passed", "score_category"]].head(5).to_string(index=False))
print("=" * 50)
