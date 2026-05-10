# =============================================================================
# Task 05 · Full ETL System [Hard — Month 1 Capstone]
# Goal: Build a fully automated, reusable ETL pipeline that can run every day
#       to get fresh data. Brings together Weeks 1-4: file handling, API +
#       requests, SQLite, and Pandas ETL.
#
# Must:
#   - EXTRACT from a real public API with full error handling
#   - Load into Pandas — clean nulls, duplicates, types, string issues
#   - TRANSFORM — add at least 2 calculated/enriched columns
#   - LOAD to SQLite via df.to_sql() AND export to clean CSV
#   - Write reusable functions: extract(), transform(), load() — not one big block
#
# Should:
#   - Logging — print what each step is doing and row counts
#
# Bonus:
#   - Run full pipeline twice — 2nd run must NOT create duplicate rows
#     (handled via if_exists='replace' in SQLite and dedup check on CSV)
# =============================================================================

import requests
import pandas as pd
import sqlite3
import sys
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# LOGGING HELPER — prints timestamped messages so each step is traceable
# ---------------------------------------------------------------------------
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ---------------------------------------------------------------------------
# EXTRACT — fetch posts and users from the public API with full error handling
# Returns raw JSON lists or exits with a clear message
# ---------------------------------------------------------------------------
def extract():
    BASE = "https://jsonplaceholder.typicode.com"
    endpoints = {
        "posts": f"{BASE}/posts",
        "users": f"{BASE}/users",
    }
    data = {}

    for name, url in endpoints.items():
        log(f"Fetching /{name} from {url} ...")
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data[name] = r.json()
            log(f"  → {len(data[name])} records received")
        except requests.exceptions.ConnectionError:
            log(f"ERROR: No internet / cannot reach {url}")
            sys.exit(1)
        except requests.exceptions.Timeout:
            log(f"ERROR: Request timed out — {url}")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            log(f"ERROR: HTTP {r.status_code} for {url}: {e}")
            sys.exit(1)

    return data["posts"], data["users"]


# ---------------------------------------------------------------------------
# TRANSFORM — clean and enrich the raw data
# Takes raw post and user lists, returns one clean merged DataFrame
# ---------------------------------------------------------------------------
def transform(posts_raw, users_raw):
    log("Building DataFrames ...")
    df_posts = pd.DataFrame(posts_raw)
    df_users = pd.json_normalize(users_raw)  # flattens nested address dict

    # --- Clean posts ---
    # Keep only needed columns
    df_posts = df_posts[["userId", "id", "title", "body"]].copy()

    # Strip whitespace from string columns
    df_posts["title"] = df_posts["title"].str.strip()
    df_posts["body"] = df_posts["body"].str.strip()

    # Drop nulls
    before = len(df_posts)
    df_posts.dropna(inplace=True)
    log(f"  Posts: dropped {before - len(df_posts)} null rows, {len(df_posts)} remain")

    # Drop duplicates on (userId, title) — same user posting same title
    before = len(df_posts)
    df_posts.drop_duplicates(subset=["userId", "title"], inplace=True)
    log(f"  Posts: dropped {before - len(df_posts)} duplicate rows, {len(df_posts)} remain")

    # --- Clean users ---
    df_users = df_users[["id", "name", "email", "address.city"]].copy()
    df_users.rename(columns={"address.city": "city"}, inplace=True)
    df_users["email"] = df_users["email"].str.lower().str.strip()
    df_users["name"] = df_users["name"].str.strip()
    df_users["city"] = df_users["city"].str.strip()

    # --- Merge posts + users on userId / id ---
    df_posts.rename(columns={"userId": "user_id"}, inplace=True)
    df_users.rename(columns={"id": "user_id"}, inplace=True)
    df = pd.merge(df_posts, df_users, on="user_id", how="left")
    log(f"  Merged DataFrame: {len(df)} rows, {len(df.columns)} columns")

    # --- Enrichment column 1: word_count — number of words in title ---
    df["word_count"] = df["title"].str.split().str.len()

    # --- Enrichment column 2: title_length — character count of title ---
    df["title_length"] = df["title"].str.len()

    # --- Enrichment column 3: body_line_count — lines in body text ---
    df["body_line_count"] = df["body"].str.count("\n") + 1

    # --- Filter: only keep posts with word_count >= 4 ---
    before = len(df)
    df = df[df["word_count"] >= 4]
    log(f"  After word_count filter (>=4): {len(df)} rows (dropped {before - len(df)})")

    # --- Standardise title to Title Case ---
    df["title"] = df["title"].str.title()

    # Reset index cleanly
    df.reset_index(drop=True, inplace=True)

    return df


# ---------------------------------------------------------------------------
# LOAD — save DataFrame to CSV and SQLite
# Bonus: 2nd run won't create duplicates because:
#   - CSV is overwritten fresh each run
#   - SQLite uses if_exists='replace' which drops and recreates the table
# ---------------------------------------------------------------------------
def load(df, csv_path="etl_output.csv", db_path="etl_pipeline.db"):
    # Save to CSV — overwrites on every run (no duplicate risk)
    df.to_csv(csv_path, index=False)
    log(f"Saved CSV: {csv_path} ({len(df)} rows)")

    # Save to SQLite — 'replace' drops table first so no duplicate rows ever
    conn = sqlite3.connect(db_path)
    df.to_sql("etl_posts", conn, if_exists="replace", index=False)

    # Verify row count in DB matches DataFrame
    count = pd.read_sql("SELECT COUNT(*) as total FROM etl_posts", conn).iloc[0]["total"]
    conn.close()
    log(f"Saved SQLite: {db_path} → table 'etl_posts' has {count} rows")

    return csv_path, db_path


# ---------------------------------------------------------------------------
# REPORT — print pipeline summary stats after load
# ---------------------------------------------------------------------------
def report(df, run_number):
    top3 = (
        df.groupby(["user_id", "name"])
        .size()
        .reset_index(name="post_count")
        .sort_values("post_count", ascending=False)
        .head(3)
    )

    print(f"\n{'=' * 55}")
    print(f"ETL PIPELINE SUMMARY — Run #{run_number}")
    print(f"{'=' * 55}")
    print(f"  Total rows loaded        : {len(df)}")
    print(f"  Columns                  : {list(df.columns)}")
    print(f"  Avg word count in title  : {df['word_count'].mean():.2f}")
    print(f"  Avg title length (chars) : {df['title_length'].mean():.2f}")
    print(f"\nTop 3 most active users:")
    print(top3.to_string(index=False))
    print(f"{'=' * 55}\n")


# ---------------------------------------------------------------------------
# MAIN — runs the full pipeline; call twice to prove no duplicate rows
# ---------------------------------------------------------------------------
def run_pipeline(run_number):
    log(f"===== PIPELINE RUN #{run_number} STARTED =====")

    posts_raw, users_raw = extract()
    df = transform(posts_raw, users_raw)
    load(df)
    report(df, run_number)

    log(f"===== PIPELINE RUN #{run_number} COMPLETE =====\n")


if __name__ == "__main__":
    # Run once
    run_pipeline(run_number=1)

    # Bonus: run again — SQLite uses if_exists='replace', CSV is overwritten
    # so zero duplicate rows are created on the second run
    log("Running pipeline a second time to verify no duplicate rows ...")
    run_pipeline(run_number=2)

    # Confirm SQLite row count is same after both runs (not doubled)
    conn = sqlite3.connect("etl_pipeline.db")
    final_count = pd.read_sql("SELECT COUNT(*) as total FROM etl_posts", conn).iloc[0]["total"]
    conn.close()
    log(f"Final row count in SQLite after 2 runs: {final_count} (no duplicates)")
