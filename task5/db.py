import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("TASK3_DB")  # reuse weather_db
        )
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None


def create_table():
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_full (
            id INT AUTO_INCREMENT PRIMARY KEY,
            city VARCHAR(50),
            date DATE,
            max_temp FLOAT,
            min_temp FLOAT
        )
        """)
        conn.commit()
        print("Table ready.")
    except Exception as e:
        print("Error creating table:", e)

    cursor.close()
    conn.close()

def store_data(data):
    conn = get_connection()
    if conn is None:
        return

    cursor = conn.cursor()


    try:
        cursor.execute("DELETE FROM weather_full")
        insert_query = """
        INSERT INTO weather_full (city, date, max_temp, min_temp)
        VALUES (%s, %s, %s, %s)
        """

        values = [
            (item["city"], item["date"], item["max_temp"], item["min_temp"])
            for item in data
        ]

        cursor.executemany(insert_query, values)
        conn.commit()

        print(f"{cursor.rowcount} rows inserted.")

    except Exception as e:
        print("Error inserting data:", e)

    cursor.close()
    conn.close()