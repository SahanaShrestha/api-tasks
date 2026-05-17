from db import get_connection

def query_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users ORDER BY name")

    for row in cursor.fetchall():
        print(row)

    conn.close()

def query_same_city():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT city, COUNT(*)
    FROM users
    GROUP BY city
    HAVING COUNT(*) > 1
    """

    cursor.execute(query)

    for row in cursor.fetchall():
        print(row)

    conn.close()