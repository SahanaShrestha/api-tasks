# =============================================================================
# TASK 3: Modular, Logged ETL System with Full Enrichment and Idempotency
# =============================================================================
# Goal:
#   - Four strictly separated, independently callable functions:
#       extract(), clean(), transform(), load()
#   - Full error handling (try/except, timeout, status code checks) in extract()
#   - At least 3 engineered columns in transform()
#   - groupby() summary: mean, min, max by at least one categorical column
#   - Logging throughout — every function logs input/output row counts
#   - Load to both CSV (index=False) and MySQL — fully idempotent
# =============================================================================

import os
import logging
import requests
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging — module-level logger used by all four pipeline functions
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(funcName)s → %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MySQL config from .env
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
# FUNCTION 1: extract()
# =============================================================================

def extract(
    url: str = "https://jsonplaceholder.typicode.com/posts",
    timeout: int = 10,
    max_retries: int = 3
) -> pd.DataFrame:
    """
    Extracts raw data from a public API.
    Independently callable — takes a URL, returns a raw DataFrame.

    Error handling:
    - requests.exceptions.Timeout      → logged + retried
    - requests.exceptions.ConnectionError → logged + retried
    - response.raise_for_status()      → 4xx raises immediately, 5xx retried
    - After max_retries exhausted      → raises RuntimeError

    Returns:
        pd.DataFrame — raw, unmodified API response as a DataFrame
    """
    log.info(f"Starting extraction from: {url}")

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"  Attempt {attempt}/{max_retries}...")
            response = requests.get(url, timeout=timeout)

            # Raises HTTPError for 4xx/5xx
            response.raise_for_status()

            data = response.json()

            # Validate we got something back
            if not data:
                raise ValueError("API returned empty response body")

            df = pd.DataFrame(data)

            log.info(f"  Extraction successful → {len(df)} rows, {len(df.columns)} columns: {list(df.columns)}")
            return df

        except requests.exceptions.Timeout as e:
            log.warning(f"  Timeout on attempt {attempt}: {e}")
            last_exception = e

        except requests.exceptions.ConnectionError as e:
            log.warning(f"  ConnectionError on attempt {attempt}: {e}")
            last_exception = e

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if 400 <= status < 500:
                # 4xx → client error, no point retrying (wrong URL, auth, etc.)
                log.error(f"  HTTP {status} client error — aborting (not retrying 4xx)")
                raise
            log.warning(f"  HTTP {status} server error on attempt {attempt}")
            last_exception = e

        except ValueError as e:
            log.error(f"  Data validation error: {e}")
            raise

    # All attempts exhausted
    raise RuntimeError(
        f"extract() failed after {max_retries} attempts. Last error: {last_exception}"
    )


# =============================================================================
# FUNCTION 2: clean()
# =============================================================================

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies data cleaning to a raw DataFrame.
    Independently callable — takes a DataFrame, returns a cleaned DataFrame.

    Cleaning steps applied:
    1. Drop exact duplicate rows
    2. Drop rows with null in critical columns (id, userId)
    3. Strip whitespace from all string columns
    4. Enforce correct dtypes (userId, id → int)
    5. Filter out-of-range userId (must be 1–10 for this API)
    6. Normalize title/body text (strip only — title case applied in transform)

    Logging: reports input row count, rows dropped at each step, output row count.

    Returns:
        pd.DataFrame — cleaned DataFrame
    """
    log.info(f"Starting cleaning → input: {len(df)} rows")
    df = df.copy()

    # Step 1: Remove exact duplicate rows
    before = len(df)
    df.drop_duplicates(inplace=True)
    dropped = before - len(df)
    log.info(f"  Duplicates removed: {dropped}  (rows remaining: {len(df)})")

    # Step 2: Drop rows where primary key columns are null
    critical_cols = [c for c in ["id", "userId"] if c in df.columns]
    before = len(df)
    df.dropna(subset=critical_cols, inplace=True)
    dropped = before - len(df)
    log.info(f"  Null critical-column rows dropped: {dropped}  (rows remaining: {len(df)})")

    # Step 3: Strip whitespace from all object/string columns
    str_cols = df.select_dtypes(include="object").columns.tolist()
    for col in str_cols:
        df[col] = df[col].str.strip()
    log.info(f"  Whitespace stripped from: {str_cols}")

    # Step 4: Type enforcement
    for col in ["id", "userId"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=[c for c in ["id", "userId"] if c in df.columns], inplace=True)
    for col in ["id", "userId"]:
        if col in df.columns:
            df[col] = df[col].astype(int)
    log.info("  Types enforced: id → int, userId → int")

    # Step 5: Out-of-range filter
    before = len(df)
    if "userId" in df.columns:
        df = df[(df["userId"] >= 1) & (df["userId"] <= 10)]
    dropped = before - len(df)
    log.info(f"  Out-of-range rows dropped: {dropped}  (rows remaining: {len(df)})")

    log.info(f"Cleaning complete → output: {len(df)} rows")
    return df


# =============================================================================
# FUNCTION 3: transform()
# =============================================================================

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies enrichment and feature engineering to cleaned data.
    Independently callable — takes cleaned DataFrame, returns enriched DataFrame.

    Engineered columns (3 minimum required):
    -----------------------------------------------------------------------
    1. word_count          : number of words in 'body' — measures post verbosity
    2. title_word_count    : number of words in 'title'
    3. body_char_count     : character length of 'body' — secondary size metric
    4. user_post_rank      : rank of each post within its user (1 = first post)
    5. verbosity_category  : 'Short' / 'Medium' / 'Long' based on word_count quartiles
    6. title              : converted to Title Case
    -----------------------------------------------------------------------

    Also prints a groupby() summary: word_count stats grouped by userId.

    Returns:
        pd.DataFrame — enriched DataFrame
    """
    log.info(f"Starting transform → input: {len(df)} rows")
    df = df.copy()

    # --- Enrichment 1: word_count (body) ---
    if "body" in df.columns:
        df["word_count"] = df["body"].str.split().str.len()
        log.info(f"  Engineered: word_count (range: {df['word_count'].min()}–{df['word_count'].max()})")

    # --- Enrichment 2: title_word_count ---
    if "title" in df.columns:
        df["title"] = df["title"].str.title()  # Normalize casing while we're here
        df["title_word_count"] = df["title"].str.split().str.len()
        log.info(f"  Engineered: title_word_count (range: {df['title_word_count'].min()}–{df['title_word_count'].max()})")

    # --- Enrichment 3: body_char_count ---
    if "body" in df.columns:
        df["body_char_count"] = df["body"].str.len()
        log.info(f"  Engineered: body_char_count (range: {df['body_char_count'].min()}–{df['body_char_count'].max()})")

    # --- Enrichment 4: user_post_rank ---
    # Rank posts within each user group by id (ascending) — post 1 for user 1, etc.
    if "userId" in df.columns and "id" in df.columns:
        df["user_post_rank"] = df.groupby("userId")["id"].rank(method="first").astype(int)
        log.info("  Engineered: user_post_rank")

    # --- Enrichment 5: verbosity_category ---
    # Categorize posts by body word count quartiles
    if "word_count" in df.columns:
        q33 = df["word_count"].quantile(0.33)
        q66 = df["word_count"].quantile(0.66)
        df["verbosity_category"] = pd.cut(
            df["word_count"],
            bins=[-1, q33, q66, float("inf")],
            labels=["Short", "Medium", "Long"]
        ).astype(str)
        log.info(f"  Engineered: verbosity_category (thresholds: {int(q33)}, {int(q66)})")
        log.info(f"  Distribution: {df['verbosity_category'].value_counts().to_dict()}")

    # --- groupby() Summary Table ---
    # Mean, min, max of word_count grouped by userId
    if "userId" in df.columns and "word_count" in df.columns:
        summary = df.groupby("userId")["word_count"].agg(
            mean_word_count="mean",
            min_word_count="min",
            max_word_count="max",
            post_count="count"
        ).round(1)

        print("\n" + "=" * 55)
        print("  GroupBy Summary: Word Count by User ID")
        print("=" * 55)
        print(summary.to_string())
        print("=" * 55)

    log.info(f"Transform complete → output: {len(df)} rows, {len(df.columns)} columns")
    return df


# =============================================================================
# FUNCTION 4: load()
# =============================================================================

def load(
    df: pd.DataFrame,
    csv_path: str   = "task3_posts_final.csv",
    table_name: str = "posts_enriched"
) -> None:
    """
    Loads enriched data to both CSV and MySQL.
    Independently callable — takes a DataFrame and destination params.

    Idempotency mechanism:
    - Table has UNIQUE constraint on 'id'
    - Uses INSERT IGNORE → duplicate ids are silently skipped on second run
    - This means the database state is identical whether you run once or 10 times

    CSV: saved with index=False as required.

    Returns: None (side-effect function)
    """
    log.info(f"Starting load → {len(df)} rows to MySQL table '{table_name}' and CSV '{csv_path}'")

    # --- CSV ---
    df.to_csv(csv_path, index=False)  # index=False — no row number column in output
    log.info(f"  CSV saved: {csv_path}  ({len(df)} rows, {len(df.columns)} columns)")

    # --- MySQL ---
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # DDL — create table if it doesn't exist
        # id is UNIQUE — the enforcement point for idempotency
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id                 INT NOT NULL UNIQUE,
                userId             INT,
                title              TEXT,
                body               TEXT,
                word_count         INT,
                title_word_count   INT,
                body_char_count    INT,
                user_post_rank     INT,
                verbosity_category VARCHAR(10),
                created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        log.info(f"  MySQL table '{table_name}' ensured")

        # Columns to insert — only those that exist in both DF and schema
        schema_cols = [
            "id", "userId", "title", "body", "word_count",
            "title_word_count", "body_char_count", "user_post_rank",
            "verbosity_category"
        ]
        insert_cols  = [c for c in schema_cols if c in df.columns]
        placeholders = ", ".join(["%s"] * len(insert_cols))
        col_names    = ", ".join(insert_cols)

        inserted = 0
        skipped  = 0

        for _, row in df.iterrows():
            values = []
            for c in insert_cols:
                val = row[c]
                # Handle pandas NA/NaN and nullable integer types
                if pd.isna(val):
                    values.append(None)
                elif hasattr(val, 'item'):
                    # numpy scalar → python native
                    values.append(val.item())
                else:
                    values.append(val)

            cursor.execute(
                f"INSERT IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})",
                tuple(values)
            )

            if cursor.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

        conn.commit()
        cursor.close()
        conn.close()

        log.info(f"  MySQL: {inserted} rows inserted, {skipped} rows skipped (idempotent duplicates)")

    except mysql.connector.Error as e:
        log.error(f"  MySQL error: {e}")
        raise

    log.info("Load complete")


# =============================================================================
# Pipeline runner — orchestrates the four functions in sequence
# =============================================================================

def run_pipeline():
    """
    Orchestrates extract → clean → transform → load.
    Each step receives the output of the previous step.
    Any step can be called independently for testing.
    """
    log.info("=" * 60)
    log.info("TASK 3: Modular ETL Pipeline — Starting")
    log.info("=" * 60)

    # Step 1
    raw_df = extract(url="https://jsonplaceholder.typicode.com/posts")

    # Step 2
    clean_df = clean(raw_df)

    # Step 3
    enriched_df = transform(clean_df)

    # Step 4
    load(enriched_df, csv_path="task3_posts_final.csv", table_name="posts_enriched")

    log.info("=" * 60)
    log.info("TASK 3: Pipeline complete")
    log.info("=" * 60)

    # Final preview
    print("\n--- Enriched Data Sample (first 5 rows) ---")
    display_cols = ["id", "userId", "title", "word_count", "verbosity_category", "user_post_rank"]
    display_cols = [c for c in display_cols if c in enriched_df.columns]
    print(enriched_df[display_cols].head().to_string(index=False))


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    run_pipeline()

    # -------------------------------------------------------------------------
    # To test individual functions independently (run in a REPL or test file):
    # -------------------------------------------------------------------------
    # from task3_modular_etl import extract, clean, transform, load
    #
    # df_raw   = extract()                        # just extract
    # df_clean = clean(df_raw)                    # just clean
    # df_enr   = transform(df_clean)              # just transform
    # load(df_enr, csv_path="test_out.csv")       # just load
    # -------------------------------------------------------------------------
