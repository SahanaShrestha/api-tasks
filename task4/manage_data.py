import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def assign_grade(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 50:
        return 'D'
    else:
        return 'F'

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("TASK4_DB")
)

cursor = conn.cursor()

# Update grades
cursor.execute("SELECT id, score FROM students")
rows = cursor.fetchall()

for row in rows:
    student_id, score = row
    grade = assign_grade(score)

    cursor.execute(
        "UPDATE students SET grade=%s WHERE id=%s",
        (grade, student_id)
    )

# Delete failed students
cursor.execute("DELETE FROM students WHERE score < 50")

# Add passed column if not exists
cursor.execute("ALTER TABLE students ADD COLUMN passed BOOLEAN")

# Update passed status
cursor.execute("""
UPDATE students
SET passed = CASE
    WHEN score >= 50 THEN TRUE
    ELSE FALSE
END
""")

conn.commit()
print("Data managed successfully!")

cursor.close()
conn.close()