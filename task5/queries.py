from db import get_connection

def run_queries():
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor()

    results = {}

    try:
        # 1. Highest average max temperature city
        cursor.execute("""
        SELECT city, AVG(max_temp) AS avg_max
        FROM weather_full
        GROUP BY city
        ORDER BY avg_max DESC
        LIMIT 1
        """)
        results["highest_avg_temp"] = cursor.fetchone()

        # 2. Hottest single day
        cursor.execute("""
        SELECT city, date, max_temp
        FROM weather_full
        ORDER BY max_temp DESC
        LIMIT 1
        """)
        results["hottest_day"] = cursor.fetchone()

        # 3. Days with temperature difference > 10°C
        cursor.execute("""
        SELECT city, date, (max_temp - min_temp) AS diff
        FROM weather_full
        WHERE (max_temp - min_temp) > 10
        """)
        results["high_temp_diff"] = cursor.fetchall()

    except Exception as e:
        print("Query error:", e)
        results = None

    cursor.close()
    conn.close()

    return results