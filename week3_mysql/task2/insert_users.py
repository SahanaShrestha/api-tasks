from db import get_connection
from fetch_users import fetch_users

def insert_users():
    conn = get_connection()
    cursor = conn.cursor()

    users = fetch_users()

    for user in users:
        query = """
        INSERT INTO users (id, name, email, phone, city, company_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            user["id"],
            user["name"],
            user["email"],
            user["phone"],
            user["address"]["city"],
            user["company"]["name"]
        )

        cursor.execute(query, values)

    conn.commit()
    cursor.close()
    conn.close()