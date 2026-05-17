# =============================================================================
# Task 03 · Multi-Source ETL [Hard]
# Goal: Combine users and their posts from two API endpoints into one clean
#       merged DataFrame, then load to CSV and SQLite.
#
# Steps:
#   1. EXTRACT     — Fetch /users and /posts as two separate API calls
#   2. DATAFRAMES  — Create df_users and df_posts
#   3. USERS COLS  — Keep id, name, email, city (city via pd.json_normalize)
#   4. POSTS COLS  — Keep userId + title, rename userId → id to match users
#   5. TRANSFORM   — Merge on 'id' using pd.merge(df_users, df_posts, on='id')
#   6. POST COUNT  — Add post_count column via df_posts.groupby('id').size()
#   7. CLEAN       — lowercase email, strip whitespace from name/city, drop nulls
#   8. LOAD        — Save to merged_data.csv and merged.db, print top 3 active users
#
# Bonus: also fetch /todos, compute completion_rate per user, merge it in
# =============================================================================

import requests
import pandas as pd
import sqlite3
import sys


def fetch(url):
    """Fetch JSON from a URL with basic error handling."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"ERROR: Request timed out — {url}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error for {url}: {e}")
        sys.exit(1)


BASE = "https://jsonplaceholder.typicode.com"

# ---------------------------------------------------------------------------
# Step 1: EXTRACT — two separate API calls (plus bonus /todos)
# ---------------------------------------------------------------------------
print("Fetching /users ...")
users_raw = fetch(f"{BASE}/users")

print("Fetching /posts ...")
posts_raw = fetch(f"{BASE}/posts")

print("Fetching /todos (bonus) ...")
todos_raw = fetch(f"{BASE}/todos")

# ---------------------------------------------------------------------------
# Step 2: Create df_users and df_posts
# ---------------------------------------------------------------------------
df_posts = pd.DataFrame(posts_raw)
df_todos = pd.DataFrame(todos_raw)

# ---------------------------------------------------------------------------
# Step 3: From df_users keep: id, name, email, city
#         'address' is a nested dict — use pd.json_normalize to flatten it
# ---------------------------------------------------------------------------
df_users_norm = pd.json_normalize(users_raw)
df_users = df_users_norm[["id", "name", "email", "address.city"]].copy()
df_users.rename(columns={"address.city": "city"}, inplace=True)

# ---------------------------------------------------------------------------
# Step 4: From df_posts keep userId + title, rename userId → id
# ---------------------------------------------------------------------------
df_posts = df_posts[["userId", "title"]].copy()
df_posts.rename(columns={"userId": "id"}, inplace=True)

# ---------------------------------------------------------------------------
# Step 5: TRANSFORM — merge users and posts on 'id'
#         One user has many posts so this expands to multiple rows per user
# ---------------------------------------------------------------------------
df_merged = pd.merge(df_users, df_posts, on="id", how="left")

# ---------------------------------------------------------------------------
# Step 6: Add post_count column to df_users
# ---------------------------------------------------------------------------
post_counts = df_posts.groupby("id").size().reset_index(name="post_count")
df_users = pd.merge(df_users, post_counts, on="id", how="left")
df_users["post_count"] = df_users["post_count"].fillna(0).astype(int)

# ---------------------------------------------------------------------------
# Bonus: compute completion_rate per user from /todos and merge into df_users
# ---------------------------------------------------------------------------
todo_stats = (
    df_todos.groupby("userId")
    .agg(total=("completed", "count"), done=("completed", "sum"))
    .reset_index()
)
todo_stats["completion_rate"] = (todo_stats["done"] / todo_stats["total"]).round(2)
todo_stats.rename(columns={"userId": "id"}, inplace=True)
df_users = pd.merge(df_users, todo_stats[["id", "completion_rate"]], on="id", how="left")

# ---------------------------------------------------------------------------
# Step 7: CLEAN — lowercase email, strip whitespace from name and city, drop nulls
# ---------------------------------------------------------------------------
df_users["email"] = df_users["email"].str.lower().str.strip()
df_users["name"] = df_users["name"].str.strip()
df_users["city"] = df_users["city"].str.strip()
df_users.dropna(inplace=True)

# ---------------------------------------------------------------------------
# Step 8: LOAD — save to merged_data.csv and merged.db
# ---------------------------------------------------------------------------
df_users.to_csv("merged_data.csv", index=False)
print("Saved: merged_data.csv")

conn = sqlite3.connect("merged.db")
df_users.to_sql("users", conn, if_exists="replace", index=False)
df_merged.to_sql("user_posts", conn, if_exists="replace", index=False)
conn.close()
print("Saved: merged.db (tables: users, user_posts)")

# ---------------------------------------------------------------------------
# Print stats — top 3 most active users by post count
# ---------------------------------------------------------------------------
top3 = df_users.sort_values("post_count", ascending=False).head(3)

print("\n" + "=" * 55)
print("MULTI-SOURCE ETL SUMMARY")
print("=" * 55)
print(f"  Users fetched          : {len(users_raw)}")
print(f"  Posts fetched          : {len(posts_raw)}")
print(f"  Todos fetched (bonus)  : {len(todos_raw)}")
print(f"  Rows after merge+clean : {len(df_users)}")
print("\nTop 3 most active users:")
print(top3[["id", "name", "post_count", "completion_rate"]].to_string(index=False))
print("=" * 55)
