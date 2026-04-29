from db import get_connection

def query_books_after_2000():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM books
        WHERE year > 2000
        ORDER BY rating DESC
    """)

    result = cursor.fetchall()
    conn.close()
    return result


def query_fiction_above_4():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM books
        WHERE genre='Fiction'
        AND rating > 4.0
    """)

    result = cursor.fetchall()
    conn.close()
    return result


def average_rating():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(rating) FROM books
    """)

    result = cursor.fetchone()
    conn.close()
    return result


def count_by_genre():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT genre, COUNT(*)
        FROM books
        GROUP BY genre
    """)

    result = cursor.fetchall()
    conn.close()
    return result