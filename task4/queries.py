import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("TASK4_DB")
)

cursor = conn.cursor()

cursor.execute("""
SELECT grade, COUNT(*)
FROM students
GROUP BY grade
ORDER BY grade
""")

results = cursor.fetchall()

for row in results:
    print(row)

cursor.close()
conn.close()