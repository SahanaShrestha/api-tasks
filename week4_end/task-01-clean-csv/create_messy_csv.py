# =============================================================================
# Task 01 · Clean a Messy CSV [Medium]
# Goal: Create messy_students.csv manually with deliberate data quality issues,
#       then verify it loads with Pandas and surfaces all problems.
#
# Problems deliberately introduced:
#   1. Missing values       — missing score or name in some rows
#   2. Duplicate rows       — same student appears more than once
#   3. Inconsistent casing  — mix of UPPER, lower, Title case in names
#   4. Score as string      — scores wrapped in quotes e.g. '85'
#   5. Extra whitespace     — leading/trailing spaces in name column
#   6. Invalid scores       — negative values that make no sense (< 0)
# =============================================================================

import pandas as pd
import io

# ---------------------------------------------------------------------------
# Step 1: Define raw CSV content with all 6 problems baked in
# ---------------------------------------------------------------------------
raw_csv = """id,name,score
1,Alice Johnson,88
2,  bob smith  ,72
3,CHARLIE BROWN,95
4,diana prince,
5,Edward Norton,'85'
6,frank castle,-10
7,  Grace Hopper,60
8,henry ford,45
9,Ivy Lee,102
10,alice johnson,88
11,BOB SMITH,72
12,,55
13,Karen Page,'90'
14,luke cage,  
15,Matt Murdock,78
16,  natasha romanoff  ,83
17,oliver queen,-5
18,percy jackson,67
19,Quinn Fabray,'73'
20,  ,88
"""

# ---------------------------------------------------------------------------
# Step 2: Write raw CSV to disk — this IS the messy file
# ---------------------------------------------------------------------------
with open("messy_students.csv", "w") as f:
    f.write(raw_csv.strip())

print("messy_students.csv written to disk.\n")

# ---------------------------------------------------------------------------
# Step 3: Load with Pandas and surface all problems
# ---------------------------------------------------------------------------
df = pd.read_csv("messy_students.csv")

print("=" * 50)
print("df.info() — dtypes and null counts")
print("=" * 50)
df.info()

print("\n" + "=" * 50)
print("df.isnull().sum() — missing values per column")
print("=" * 50)
print(df.isnull().sum())

print("\n" + "=" * 50)
print("First 20 rows (raw, no cleaning yet)")
print("=" * 50)
print(df.to_string())
