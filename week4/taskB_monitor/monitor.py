import mysql.connector
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database="monitor_db"
)

cursor = conn.cursor()

try:
    # -----------------------------
    # CREATE TABLES
    # -----------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INT PRIMARY KEY,
        userId INT,
        title TEXT,
        body TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS change_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        post_id INT,
        change_type VARCHAR(20),
        timestamp DATETIME
    )
    """)

    # -----------------------------
    # FETCH API DATA
    # -----------------------------
    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    api_data = response.json()

    # -----------------------------
    # PROCESS EACH POST
    # -----------------------------
    for post in api_data:

        cursor.execute("SELECT userId, title, body FROM posts WHERE id=%s", (post["id"],))
        existing = cursor.fetchone()

        # NEW RECORD
        if not existing:
            cursor.execute("""
                INSERT INTO posts (id, userId, title, body)
                VALUES (%s, %s, %s, %s)
            """, (post["id"], post["userId"], post["title"], post["body"]))

            cursor.execute("""
                INSERT INTO change_log (post_id, change_type, timestamp)
                VALUES (%s, %s, %s)
            """, (post["id"], "NEW", datetime.now()))

        # MODIFIED RECORD
        else:
            db_userId, db_title, db_body = existing

            if db_title != post["title"] or db_body != post["body"]:
                cursor.execute("""
                    UPDATE posts
                    SET title=%s, body=%s
                    WHERE id=%s
                """, (post["title"], post["body"], post["id"]))

                cursor.execute("""
                    INSERT INTO change_log (post_id, change_type, timestamp)
                    VALUES (%s, %s, %s)
                """, (post["id"], "MODIFIED", datetime.now()))

    conn.commit()

    # -----------------------------
    # OUTPUT 1: POSTS PER USER
    # -----------------------------
    print("\n--- Post count per user ---")
    cursor.execute("""
        SELECT userId, COUNT(*)
        FROM posts
        GROUP BY userId
    """)
    for row in cursor.fetchall():
        print(row)

    # -----------------------------
    # OUTPUT 2: CHANGE LOG
    # -----------------------------
    print("\n--- Latest change log ---")
    cursor.execute("""
        SELECT * FROM change_log
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(row)

    # -----------------------------
    # OUTPUT 3: MOST CHANGES USER
    # -----------------------------
    print("\n--- User with most changes ---")
    cursor.execute("""
        SELECT p.userId, COUNT(*) as changes
        FROM change_log c
        JOIN posts p ON c.post_id = p.id
        GROUP BY p.userId
        ORDER BY changes DESC
        LIMIT 1
    """)
    print(cursor.fetchone())

except Exception as e:
    print("Error:", e)

finally:
    cursor.close()
    conn.close()