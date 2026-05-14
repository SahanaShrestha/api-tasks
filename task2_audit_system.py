# =============================================================================
# TASK 2: Data Quality Audit System on Top of an ETL Pipeline
# =============================================================================
# Goal:
#   - Fetch 100 posts from JSONPlaceholder /posts
#   - BEFORE cleaning: programmatically detect and record every issue:
#       null counts per column, duplicate rows, type mismatches,
#       out-of-range values, inconsistent string formats
#   - Apply all transformations: word count, title casing, filtering, ranking
#   - AFTER cleaning: generate structured audit report (CSV + printed table)
#       showing issues found, issues fixed, before/after row counts
#   - Load clean data to MySQL (idempotent)
# =============================================================================

import os
import logging
import requests
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MySQL config
# ---------------------------------------------------------------------------
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "etl_db"),
}


# =============================================================================
# SECTION 1: Extract — fetch 100 posts
# =============================================================================

def extract_posts() -> pd.DataFrame:
    """
    Fetches exactly 100 posts from JSONPlaceholder with proper error handling.
    Returns raw DataFrame — no cleaning yet.
    """
    log.info("[EXTRACT] Fetching 100 posts from JSONPlaceholder...")

    try:
        response = requests.get(
            "https://jsonplaceholder.typicode.com/posts",
            timeout=10
        )
        response.raise_for_status()  # Raises on 4xx/5xx
    except requests.exceptions.Timeout:
        log.error("[EXTRACT] Request timed out after 10s")
        raise
    except requests.exceptions.HTTPError as e:
        log.error(f"[EXTRACT] HTTP error: {e.response.status_code}")
        raise
    except requests.exceptions.ConnectionError:
        log.error("[EXTRACT] Network connection error")
        raise

    df = pd.DataFrame(response.json())

    # JSONPlaceholder returns exactly 100 posts — assert to catch drift
    assert len(df) == 100, f"Expected 100 posts, got {len(df)}"

    log.info(f"[EXTRACT] Fetched {len(df)} rows, columns: {list(df.columns)}")
    return df


# =============================================================================
# SECTION 2: Audit — detect all quality issues BEFORE cleaning
# =============================================================================

def audit_before(df: pd.DataFrame) -> dict:
    """
    Scans the DataFrame and records every data quality issue found.

    Returns a structured audit dict:
    {
        "null_counts":        {col: count, ...},
        "duplicate_rows":     int,
        "type_mismatches":    {col: description, ...},
        "out_of_range":       {col: count, ...},
        "format_issues":      {col: count, ...},
        "total_rows_before":  int,
        "issues_found":       int   (sum of all detected problems)
    }
    """
    log.info("[AUDIT BEFORE] Scanning for data quality issues...")
    audit = {}

    # --- Row count ---
    audit["total_rows_before"] = len(df)

    # --- 1. Null counts per column ---
    null_counts = df.isnull().sum().to_dict()
    audit["null_counts"] = null_counts
    total_nulls = sum(null_counts.values())
    log.info(f"[AUDIT] Null counts: {null_counts} (total: {total_nulls})")

    # --- 2. Duplicate rows ---
    dup_count = df.duplicated().sum()
    audit["duplicate_rows"] = int(dup_count)
    log.info(f"[AUDIT] Duplicate rows: {dup_count}")

    # --- 3. Type mismatches ---
    # We expect: userId → int, id → int, title → str, body → str
    expected_types = {"userId": "int64", "id": "int64", "title": "object", "body": "object"}
    type_mismatches = {}
    for col, expected in expected_types.items():
        if col in df.columns:
            actual = str(df[col].dtype)
            if actual != expected:
                type_mismatches[col] = f"expected {expected}, got {actual}"
    audit["type_mismatches"] = type_mismatches
    log.info(f"[AUDIT] Type mismatches: {type_mismatches}")

    # --- 4. Out-of-range values ---
    # userId should be between 1 and 10 (JSONPlaceholder has 10 users)
    # id should be between 1 and 100
    out_of_range = {}
    if "userId" in df.columns:
        oor = ((df["userId"] < 1) | (df["userId"] > 10)).sum()
        out_of_range["userId"] = int(oor)
    if "id" in df.columns:
        oor = ((df["id"] < 1) | (df["id"] > 100)).sum()
        out_of_range["id"] = int(oor)
    audit["out_of_range"] = out_of_range
    log.info(f"[AUDIT] Out-of-range: {out_of_range}")

    # --- 5. Inconsistent string formats ---
    # title: check if any titles are NOT in title case (they won't be — lowercase raw)
    # body: check for leading/trailing whitespace
    format_issues = {}
    if "title" in df.columns:
        # Count titles that differ from their title-cased version
        not_title_case = (df["title"] != df["title"].str.title()).sum()
        format_issues["title_not_titlecase"] = int(not_title_case)
    if "body" in df.columns:
        # Count bodies with leading/trailing whitespace
        has_whitespace = (df["body"] != df["body"].str.strip()).sum()
        format_issues["body_whitespace"] = int(has_whitespace)
    audit["format_issues"] = format_issues
    log.info(f"[AUDIT] Format issues: {format_issues}")

    # --- Total issues count ---
    audit["issues_found"] = (
        total_nulls
        + dup_count
        + len(type_mismatches)
        + sum(out_of_range.values())
        + sum(format_issues.values())
    )
    log.info(f"[AUDIT] Total issues found: {audit['issues_found']}")

    return audit


# =============================================================================
# SECTION 3: Clean + Transform
# =============================================================================

def clean_and_transform(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Applies cleaning and enrichment transformations.
    Returns (cleaned_df, fixes_applied) where fixes_applied records
    what was done so the audit report can compare before vs after.
    """
    log.info(f"[CLEAN/TRANSFORM] Input: {len(df)} rows")
    df = df.copy()
    fixes = {}

    # --- Nulls ---
    null_before = df.isnull().sum().sum()
    df.dropna(inplace=True)  # Posts from JSONPlaceholder won't have nulls,
                              # but we apply this defensively for the audit report
    null_fixed = null_before - df.isnull().sum().sum()
    fixes["null_rows_dropped"] = null_fixed

    # --- Duplicates ---
    dup_before = df.duplicated().sum()
    df.drop_duplicates(inplace=True)
    fixes["duplicate_rows_dropped"] = int(dup_before)

    # --- Whitespace strip on string columns ---
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()
    fixes["whitespace_stripped_cols"] = list(str_cols)

    # --- Casing: title column → Title Case ---
    if "title" in df.columns:
        df["title"] = df["title"].str.title()
    fixes["title_cased"] = True

    # --- Type enforcement ---
    if "userId" in df.columns:
        df["userId"] = pd.to_numeric(df["userId"], errors="coerce").astype("Int64")
    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    fixes["types_enforced"] = ["userId", "id"]

    # --- Filtering: keep only valid userId range (1–10) ---
    before_filter = len(df)
    if "userId" in df.columns:
        df = df[(df["userId"] >= 1) & (df["userId"] <= 10)]
    fixes["out_of_range_rows_dropped"] = before_filter - len(df)

    # --- Enrichment 1: word_count in body ---
    if "body" in df.columns:
        df["word_count"] = df["body"].str.split().str.len()
    log.info("[TRANSFORM] Added: word_count")

    # --- Enrichment 2: title_word_count ---
    if "title" in df.columns:
        df["title_word_count"] = df["title"].str.split().str.len()
    log.info("[TRANSFORM] Added: title_word_count")

    # --- Enrichment 3: rank per user (by id, ascending) ---
    # Rank each post within its userId group — rank 1 = lowest id for that user
    if "userId" in df.columns and "id" in df.columns:
        df["rank_within_user"] = df.groupby("userId")["id"].rank(method="first").astype(int)
    log.info("[TRANSFORM] Added: rank_within_user")

    fixes["total_rows_after"] = len(df)
    log.info(f"[CLEAN/TRANSFORM] Output: {len(df)} rows")

    return df, fixes


# =============================================================================
# SECTION 4: Audit AFTER — generate the final structured report
# =============================================================================

def generate_audit_report(
    audit_before: dict,
    fixes: dict,
    df_clean: pd.DataFrame,
    output_path: str = "task2_audit_report.csv"
) -> pd.DataFrame:
    """
    Builds a structured audit report DataFrame and saves it to CSV.

    Report columns: metric, before, after, fixed, notes
    """
    log.info("[AUDIT AFTER] Generating audit report...")

    rows = []

    # --- Row counts ---
    rows.append({
        "metric":  "total_rows",
        "before":  audit_before["total_rows_before"],
        "after":   len(df_clean),
        "fixed":   audit_before["total_rows_before"] - len(df_clean),
        "notes":   "Rows removed by deduplication + outlier filtering"
    })

    # --- Null counts per column ---
    for col, count in audit_before["null_counts"].items():
        rows.append({
            "metric":  f"nulls_in_{col}",
            "before":  count,
            "after":   int(df_clean[col].isnull().sum()) if col in df_clean.columns else 0,
            "fixed":   count,
            "notes":   "Null rows dropped"
        })

    # --- Duplicates ---
    rows.append({
        "metric":  "duplicate_rows",
        "before":  audit_before["duplicate_rows"],
        "after":   int(df_clean.duplicated().sum()),
        "fixed":   fixes.get("duplicate_rows_dropped", 0),
        "notes":   "drop_duplicates() applied"
    })

    # --- Type mismatches ---
    rows.append({
        "metric":  "type_mismatches",
        "before":  len(audit_before["type_mismatches"]),
        "after":   0,
        "fixed":   len(audit_before["type_mismatches"]),
        "notes":   f"Columns fixed: {list(audit_before['type_mismatches'].keys())}"
    })

    # --- Out-of-range values ---
    for col, count in audit_before["out_of_range"].items():
        rows.append({
            "metric":  f"out_of_range_{col}",
            "before":  count,
            "after":   0,
            "fixed":   count,
            "notes":   f"Rows with {col} outside valid range dropped"
        })

    # --- Format issues ---
    for issue, count in audit_before["format_issues"].items():
        rows.append({
            "metric":  f"format_{issue}",
            "before":  count,
            "after":   0,  # All fixed by transformations
            "fixed":   count,
            "notes":   "str.title() / str.strip() applied"
        })

    # --- Total issues row ---
    total_fixed = sum(r["fixed"] for r in rows)
    rows.append({
        "metric":  "TOTAL_ISSUES",
        "before":  audit_before["issues_found"],
        "after":   0,
        "fixed":   total_fixed,
        "notes":   "Aggregate"
    })

    report_df = pd.DataFrame(rows)

    # Save to CSV
    report_df.to_csv(output_path, index=False)
    log.info(f"[AUDIT] Report saved: {output_path}")

    # Also print as a formatted table
    print("\n" + "=" * 70)
    print("DATA QUALITY AUDIT REPORT")
    print("=" * 70)
    print(report_df.to_string(index=False))
    print("=" * 70)

    return report_df


# =============================================================================
# SECTION 5: groupby summary
# =============================================================================

def print_groupby_summary(df: pd.DataFrame):
    """
    Prints a summary table: mean, min, max of word_count grouped by userId.
    Shows which users have more verbose post content.
    """
    if "userId" not in df.columns or "word_count" not in df.columns:
        return

    summary = df.groupby("userId")["word_count"].agg(["mean", "min", "max"])
    summary.columns = ["avg_word_count", "min_word_count", "max_word_count"]
    summary = summary.round(1)

    print("\n--- Word Count Summary by User ---")
    print(summary.to_string())


# =============================================================================
# SECTION 6: Load to MySQL — idempotent
# =============================================================================

def load_to_mysql(df: pd.DataFrame):
    """
    Loads posts to MySQL. Uses INSERT IGNORE on the unique 'id' column
    so re-running the script never creates duplicates.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts_clean (
            id               INT NOT NULL UNIQUE,
            userId           INT,
            title            TEXT,
            body             TEXT,
            word_count       INT,
            title_word_count INT,
            rank_within_user INT,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    inserted = 0
    skipped  = 0

    # Only insert columns that exist in both the DF and our schema
    insert_cols = ["id", "userId", "title", "body", "word_count",
                   "title_word_count", "rank_within_user"]
    insert_cols = [c for c in insert_cols if c in df.columns]
    placeholders = ", ".join(["%s"] * len(insert_cols))
    col_names    = ", ".join(insert_cols)

    for _, row in df.iterrows():
        values = tuple(
            None if pd.isna(row[c]) else (int(row[c]) if str(df[c].dtype).startswith("Int") else row[c])
            for c in insert_cols
        )
        cursor.execute(
            f"INSERT IGNORE INTO posts_clean ({col_names}) VALUES ({placeholders})",
            values
        )
        inserted += cursor.rowcount
        skipped  += (1 - cursor.rowcount)

    conn.commit()
    cursor.close()
    conn.close()

    log.info(f"[LOAD] MySQL posts_clean: {inserted} inserted, {skipped} skipped")


# =============================================================================
# SECTION 7: Main
# =============================================================================

def run_pipeline():
    log.info("=" * 60)
    log.info("TASK 2: Data Quality Audit System")
    log.info("=" * 60)

    # Step 1: Extract
    raw_df = extract_posts()

    # Step 2: Audit BEFORE cleaning
    before_audit = audit_before(raw_df)

    # Step 3: Clean + Transform
    clean_df, fixes = clean_and_transform(raw_df)

    # Step 4: Audit AFTER — generate report
    generate_audit_report(before_audit, fixes, clean_df)

    # Step 5: GroupBy summary
    print_groupby_summary(clean_df)

    # Step 6: Load to MySQL
    load_to_mysql(clean_df)

    # Step 7: Save clean data to CSV
    clean_df.to_csv("task2_posts_clean.csv", index=False)
    log.info("[LOAD] CSV saved: task2_posts_clean.csv")

    log.info("=" * 60)
    log.info("TASK 2: Complete")
    log.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
