# =============================================================================
# TASK 1: Fault-Tolerant Multi-Source ETL Pipeline with Conflict Resolution
# =============================================================================
# Goal:
#   - Extract from two sources: JSONPlaceholder API + locally generated messy CSV
#   - Handle timeouts, retries, HTTP errors during extraction
#   - Normalize nested JSON (address.city via pd.json_normalize)
#   - Merge on shared key (email), resolve conflicts where same email has
#     different name values — API source wins (more authoritative, documented below)
#   - Apply all 6 cleaning techniques: nulls, duplicates, casing, types,
#     whitespace, outliers
#   - Load to both MySQL and CSV
#   - Idempotent: second run must NOT insert duplicate rows into MySQL
# =============================================================================

import os
import time
import random
import logging
import requests
import pandas as pd
import mysql.connector
from io import StringIO
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Logging setup — everything goes to console with timestamp + level
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load MySQL credentials from .env file
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
# SECTION 1: HTTP utility — retry wrapper with exponential back-off
# =============================================================================

def fetch_with_retry(url: str, max_retries: int = 3, timeout: int = 10) -> dict | list:
    """
    GET a URL with retry logic.
    - Retries on connection errors, timeouts, and 5xx server errors
    - Uses exponential back-off: 1s, 2s, 4s between attempts
    - Raises immediately on 4xx (client errors — no point retrying)
    """
    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"  GET {url}  (attempt {attempt}/{max_retries})")
            response = requests.get(url, timeout=timeout)

            # Raise HTTPError for 4xx/5xx — but we differentiate below
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            # Server took too long — worth retrying
            log.warning(f"  Timeout on attempt {attempt}")

        except requests.exceptions.ConnectionError:
            # DNS/network issue — retry in case it's transient
            log.warning(f"  Connection error on attempt {attempt}")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if 400 <= status < 500:
                # Client error (404, 403, etc.) — no retry, fail fast
                log.error(f"  Client error {status} — aborting retries")
                raise
            # 5xx — server-side, worth retrying
            log.warning(f"  Server error {status} on attempt {attempt}")

        # Exponential back-off before next attempt (skip sleep on last attempt)
        if attempt < max_retries:
            sleep_time = 2 ** (attempt - 1)  # 1, 2, 4 seconds
            log.info(f"  Sleeping {sleep_time}s before retry...")
            time.sleep(sleep_time)

    raise RuntimeError(f"All {max_retries} attempts failed for {url}")


# =============================================================================
# SECTION 2: Extract — API source (JSONPlaceholder /users and /posts)
# =============================================================================

def extract_api() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetches /users and /posts from JSONPlaceholder.
    Returns (users_df, posts_df) as raw DataFrames.

    /users has nested fields:  address.city, address.geo.lat, company.name etc.
    pd.json_normalize() flattens those into dot-separated column names.
    """
    log.info("[EXTRACT API] Fetching users from JSONPlaceholder...")
    raw_users = fetch_with_retry("https://jsonplaceholder.typicode.com/users")

    # pd.json_normalize flattens nested dicts — address.city becomes a column
    users_df = pd.json_normalize(raw_users)
    log.info(f"[EXTRACT API] Users fetched: {len(users_df)} rows, {len(users_df.columns)} columns")
    log.info(f"[EXTRACT API] Columns after normalize: {list(users_df.columns)}")

    log.info("[EXTRACT API] Fetching posts from JSONPlaceholder...")
    raw_posts = fetch_with_retry("https://jsonplaceholder.typicode.com/posts")
    posts_df  = pd.DataFrame(raw_posts)
    log.info(f"[EXTRACT API] Posts fetched: {len(posts_df)} rows")

    return users_df, posts_df


# =============================================================================
# SECTION 3: Extract — locally generated messy CSV source
# =============================================================================

def generate_messy_csv() -> str:
    """
    Generates a messy CSV string simulating a real-world dirty data source.
    Issues intentionally injected:
      - Duplicate rows (same email)
      - Conflicting name for an email that also exists in the API source
      - Extra whitespace in strings
      - Mixed casing in email
      - Null/empty fields
      - An outlier age value (999)
      - Wrong type in age column (string 'N/A')
    """
    csv_data = """id,name,email,age,city
1,  Alice Johnson  ,alice@example.com,28,New York
2,Bob   Smith,bob@example.com,34,  Los Angeles
3,CAROL WHITE,carol@example.com,N/A,Chicago
4,Dave Brown,dave@example.com,999,Houston
5,Eve Davis,,25,Phoenix
6,Frank Miller,frank@example.com,30,
7,  Alice Johnson  ,alice@example.com,28,New York
8,Conflict Name,Sincere@april.biz,45,FakeCity
9,,grace@example.com,22,Boston
10,Hank Wilson,hank@example.com,31,Seattle
"""
    # Row 8 uses 'Sincere@april.biz' — this email exists in JSONPlaceholder users
    # with name "Leanne Graham". We'll resolve this conflict explicitly.
    return csv_data


def extract_csv() -> pd.DataFrame:
    """
    Reads the messy CSV from the generated string.
    In a real pipeline this would be: pd.read_csv('path/to/file.csv')
    """
    log.info("[EXTRACT CSV] Reading messy CSV source...")
    csv_string = generate_messy_csv()
    df = pd.read_csv(StringIO(csv_string))
    log.info(f"[EXTRACT CSV] CSV loaded: {len(df)} rows")
    return df


# =============================================================================
# SECTION 4: Normalize & Merge with Conflict Resolution
# =============================================================================

def merge_with_conflict_resolution(
    users_df: pd.DataFrame,
    csv_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merges API users and CSV users on 'email' (case-insensitive).

    CONFLICT RESOLUTION STRATEGY:
    -----------------------------------------------------------------------
    When the same email exists in both sources with a different 'name':
    → API source WINS.
    Rationale: JSONPlaceholder /users is treated as the system-of-record
    (authoritative master data). The CSV is a secondary/operational source
    that may have typos, outdated names, or user-entered errors.
    This is documented as a business rule and applied deterministically.
    -----------------------------------------------------------------------

    Merge type: outer join so we keep users that appear in only one source.
    Suffix convention: _api for API columns, _csv for CSV columns.
    """
    log.info("[MERGE] Starting merge on normalized email key...")

    # --- Normalize email to lowercase for case-insensitive join ---
    users_df = users_df.copy()
    csv_df   = csv_df.copy()
    users_df["email"] = users_df["email"].str.lower().str.strip()
    csv_df["email"]   = csv_df["email"].str.lower().str.strip()

    # --- Select only the columns we care about from each source ---
    # API users: id, name, email, address.city (normalized column name)
    api_cols = ["id", "name", "email"]

    # address.city comes from pd.json_normalize — it's literally named "address.city"
    if "address.city" in users_df.columns:
        users_df = users_df.rename(columns={"address.city": "city"})

    # Keep relevant columns
    api_slim = users_df[["id", "name", "email", "city"]].copy() if "city" in users_df.columns \
               else users_df[["id", "name", "email"]].copy()

    csv_slim = csv_df[["name", "email", "age", "city"]].copy() if "age" in csv_df.columns \
               else csv_df[["name", "email"]].copy()

    # --- Outer merge on email ---
    merged = pd.merge(
        api_slim,
        csv_slim,
        on="email",
        how="outer",
        suffixes=("_api", "_csv")
    )
    log.info(f"[MERGE] After outer join: {len(merged)} rows")

    # --- Conflict resolution: name_api wins over name_csv ---
    # coalesce: if name_api is not null, use it; otherwise fall back to name_csv
    merged["name"] = merged["name_api"].combine_first(merged["name_csv"])

    # --- Conflict resolution: city_api wins over city_csv similarly ---
    if "city_api" in merged.columns and "city_csv" in merged.columns:
        merged["city"] = merged["city_api"].combine_first(merged["city_csv"])
    elif "city_api" in merged.columns:
        merged["city"] = merged["city_api"]
    elif "city_csv" in merged.columns:
        merged["city"] = merged["city_csv"]

    # --- Drop the raw suffixed columns — we now have clean resolved columns ---
    drop_cols = [c for c in merged.columns if c.endswith("_api") or c.endswith("_csv")]
    merged.drop(columns=drop_cols, inplace=True)

    log.info(f"[MERGE] After conflict resolution: {len(merged)} rows, columns: {list(merged.columns)}")
    return merged


# =============================================================================
# SECTION 5: Cleaning — all 6 techniques
# =============================================================================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies all 6 cleaning techniques in sequence:
    1. Null handling
    2. Duplicate removal
    3. Casing normalization
    4. Type enforcement
    5. Whitespace stripping
    6. Outlier removal
    """
    log.info(f"[CLEAN] Input: {len(df)} rows")
    df = df.copy()

    # --- 1. Nulls ---
    # Drop rows where email is null — email is the join key, can't do anything with it
    before = len(df)
    df.dropna(subset=["email"], inplace=True)
    log.info(f"[CLEAN] Nulls: dropped {before - len(df)} rows with null email")

    # Fill null name with 'Unknown'
    df["name"] = df["name"].fillna("Unknown")

    # Fill null city with 'Unknown'
    if "city" in df.columns:
        df["city"] = df["city"].fillna("Unknown")

    # Fill null age with median (computed after type coercion below)
    # We'll handle this after type coercion in step 4

    # --- 2. Duplicates ---
    before = len(df)
    df.drop_duplicates(subset=["email"], keep="first", inplace=True)
    log.info(f"[CLEAN] Duplicates: dropped {before - len(df)} duplicate email rows")

    # --- 3. Casing ---
    # Name → Title Case
    df["name"] = df["name"].str.title()
    # Email → lowercase (already done during merge, belt-and-suspenders)
    df["email"] = df["email"].str.lower()
    # City → Title Case
    if "city" in df.columns:
        df["city"] = df["city"].str.title()
    log.info("[CLEAN] Casing: name→Title, email→lower, city→Title")

    # --- 4. Types ---
    if "age" in df.columns:
        # Coerce non-numeric age values ('N/A', strings) to NaN, then to float
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        # Now fill nulls with median
        median_age = df["age"].median()
        df["age"] = df["age"].fillna(median_age)
        df["age"] = df["age"].astype(int)
        log.info(f"[CLEAN] Types: age coerced to int, nulls filled with median ({int(median_age)})")

    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)

    # --- 5. Whitespace ---
    # Strip leading/trailing whitespace from all string columns
    str_cols = df.select_dtypes(include=["object", "str"]).columns
    for col in str_cols:
        df[col] = df[col].str.strip()
    log.info(f"[CLEAN] Whitespace: stripped {list(str_cols)}")

    # --- 6. Outliers ---
    # Age outlier: anything above 120 or below 0 is biologically impossible
    if "age" in df.columns:
        before = len(df)
        df = df[(df["age"] >= 0) & (df["age"] <= 120)]
        log.info(f"[CLEAN] Outliers: removed {before - len(df)} rows with age outside [0, 120]")

    log.info(f"[CLEAN] Output: {len(df)} rows")
    return df


# =============================================================================
# SECTION 6: Load — MySQL (idempotent) + CSV
# =============================================================================

def get_mysql_connection():
    """Returns a live mysql.connector connection using DB_CONFIG."""
    return mysql.connector.connect(**DB_CONFIG)


def ensure_table_exists(conn):
    """
    Creates the merged_users table if it doesn't exist.
    Using CREATE TABLE IF NOT EXISTS — safe to call on every run.
    email is UNIQUE — this is what enforces idempotency on INSERT.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merged_users (
            id         INT,
            name       VARCHAR(255),
            email      VARCHAR(255) NOT NULL UNIQUE,  -- UNIQUE prevents duplicates
            city       VARCHAR(255),
            age        INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    log.info("[LOAD] Table 'merged_users' ensured in MySQL")


def load_to_mysql(df: pd.DataFrame):
    """
    Inserts rows into MySQL using INSERT IGNORE — if a row with the same
    email already exists (UNIQUE constraint), that row is silently skipped.
    This makes the pipeline fully idempotent: run it 10 times, same result.
    """
    conn = get_mysql_connection()
    ensure_table_exists(conn)
    cursor = conn.cursor()

    # Build column list dynamically — only insert columns that exist in both
    # the DataFrame and the table schema
    table_cols = ["id", "name", "email", "city", "age"]
    df_cols    = [c for c in table_cols if c in df.columns]

    inserted = 0
    skipped  = 0

    for _, row in df.iterrows():
        values = tuple(
            None if pd.isna(row[c]) else row[c]
            for c in df_cols
        )
        placeholders = ", ".join(["%s"] * len(df_cols))
        col_names    = ", ".join(df_cols)

        # INSERT IGNORE: skips silently if UNIQUE key (email) already exists
        sql = f"INSERT IGNORE INTO merged_users ({col_names}) VALUES ({placeholders})"
        cursor.execute(sql, values)

        if cursor.rowcount == 1:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cursor.close()
    conn.close()

    log.info(f"[LOAD] MySQL: {inserted} rows inserted, {skipped} rows skipped (duplicates)")


def load_to_csv(df: pd.DataFrame, path: str = "task1_output.csv"):
    """Saves the final DataFrame to CSV without the index."""
    df.to_csv(path, index=False)
    log.info(f"[LOAD] CSV saved: {path}  ({len(df)} rows)")


# =============================================================================
# SECTION 7: Main pipeline — orchestrates all steps
# =============================================================================

def run_pipeline():
    log.info("=" * 60)
    log.info("TASK 1: Starting Multi-Source ETL Pipeline")
    log.info("=" * 60)

    # Step 1: Extract from both sources simultaneously
    # In production you'd use threading/asyncio; here we call sequentially
    # (JSONPlaceholder is fast enough that concurrent calls add no real value
    #  in a demo setting — but the structure is ready to swap in ThreadPoolExecutor)
    users_df, posts_df = extract_api()
    csv_df = extract_csv()

    # Step 2: Merge with conflict resolution
    merged_df = merge_with_conflict_resolution(users_df, csv_df)

    # Step 3: Clean — all 6 techniques
    clean_df = clean_data(merged_df)

    # Step 4: Load to MySQL and CSV
    load_to_mysql(clean_df)
    load_to_csv(clean_df, path="task1_output.csv")

    log.info("=" * 60)
    log.info("TASK 1: Pipeline complete")
    log.info("=" * 60)

    # Print a quick preview
    print("\n--- Final DataFrame Preview ---")
    print(clean_df.to_string(index=False))


if __name__ == "__main__":
    run_pipeline()
