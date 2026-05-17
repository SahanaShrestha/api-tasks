# =============================================================================
# Task 02 · API → Clean → Save [Hard]
# Goal: Build a complete ETL pipeline — fetch real API data, clean it with
#       Pandas, and load the result to both CSV and SQLite.
#
# Steps:
#   1. EXTRACT  — Fetch all 100 posts from jsonplaceholder.typicode.com/posts
#   2. LOAD     — Load JSON response into a Pandas DataFrame
#   3. TRANSFORM— Keep only columns: userId, id, title, body
#   4. ADD COL  — Add word_count column using .str.split().str.len()
#   5. FILTER   — Keep only rows where word_count >= 4
#   6. STANDARDISE — title to Title Case, strip whitespace from body
#   7. LOAD OUT — Save to clean_posts.csv (no index) and posts.db via df.to_sql()
#   8. PRINT    — total posts fetched, posts after filter, top 3 users by post count
#
# Bonus: error handling on API call + validate all userId values are integers
# =============================================================================

import requests
import pandas as pd
import sqlite3
import sys

# ---------------------------------------------------------------------------
# Step 1: EXTRACT — fetch all 100 posts from the public API
# ---------------------------------------------------------------------------
API_URL = "https://jsonplaceholder.typicode.com/posts"

try:
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()  # raises HTTPError for 4xx/5xx responses
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to the API. Check your internet connection.")
    sys.exit(1)
except requests.exceptions.Timeout:
    print("ERROR: API request timed out after 10 seconds.")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    print(f"ERROR: API returned an error: {e}")
    sys.exit(1)

data = response.json()
total_fetched = len(data)
print(f"Posts fetched from API: {total_fetched}")

# ---------------------------------------------------------------------------
# Step 2: Load JSON into a Pandas DataFrame
# ---------------------------------------------------------------------------
df = pd.DataFrame(data)

# ---------------------------------------------------------------------------
# Bonus: Validate all userId values are integers before proceeding
# ---------------------------------------------------------------------------
invalid_user_ids = df[~df["userId"].apply(lambda x: isinstance(x, int))]
if not invalid_user_ids.empty:
    print(f"WARNING: {len(invalid_user_ids)} rows have non-integer userId values.")
    print(invalid_user_ids[["userId", "id"]].to_string(index=False))
else:
    print("Validation passed: all userId values are integers.")

# ---------------------------------------------------------------------------
# Step 3: TRANSFORM — keep only required columns
# ---------------------------------------------------------------------------
df = df[["userId", "id", "title", "body"]]

# ---------------------------------------------------------------------------
# Step 4: Add word_count column — count words in title
# ---------------------------------------------------------------------------
df["word_count"] = df["title"].str.split().str.len()

# ---------------------------------------------------------------------------
# Step 5: Filter — keep only posts where word_count >= 4
# ---------------------------------------------------------------------------
df = df[df["word_count"] >= 4]
total_after_filter = len(df)

# ---------------------------------------------------------------------------
# Step 6: Standardise — title to Title Case, strip whitespace from body
# ---------------------------------------------------------------------------
df["title"] = df["title"].str.title()
df["body"] = df["body"].str.strip()

# ---------------------------------------------------------------------------
# Step 7: LOAD — save to clean_posts.csv and to SQLite posts.db
# ---------------------------------------------------------------------------

# Save to CSV, no index column
df.to_csv("clean_posts.csv", index=False)
print("Saved: clean_posts.csv")

# Save to SQLite — replace table if it already exists
conn = sqlite3.connect("posts.db")
df.to_sql("posts", conn, if_exists="replace", index=False)
conn.close()
print("Saved: posts.db (table: posts)")

# ---------------------------------------------------------------------------
# Step 8: Print stats — total fetched, after filter, top 3 users by post count
# ---------------------------------------------------------------------------
top3_users = (
    df.groupby("userId")
    .size()
    .reset_index(name="post_count")
    .sort_values("post_count", ascending=False)
    .head(3)
)

print("\n" + "=" * 45)
print("ETL PIPELINE SUMMARY")
print("=" * 45)
print(f"  Total posts fetched      : {total_fetched}")
print(f"  Posts after filter (>=4) : {total_after_filter}")
print(f"  Posts dropped            : {total_fetched - total_after_filter}")
print("\nTop 3 users by post count:")
print(top3_users.to_string(index=False))
print("=" * 45)
