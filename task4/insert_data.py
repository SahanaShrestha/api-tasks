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

students = [
    ('Asha', 'Math', 85),
    ('Ravi', 'Science', 72),
    ('Sita', 'English', 90),
    ('Kiran', 'Math', 45),
    ('Anil', 'Science', 55),
    ('Maya', 'English', 38),
    ('John', 'Math', 67),
    ('Sara', 'Science', 92),
    ('Ram', 'English', 48),
    ('Nina', 'Math', 77),
    ('Paul', 'Science', 60),
    ('Lina', 'English', 82),
    ('Tom', 'Math', 30),
    ('Jerry', 'Science', 50),
    ('Priya', 'English', 88)
]

cursor.executemany(
    "INSERT INTO students (name, subject, score) VALUES (%s, %s, %s)",
    students
)

conn.commit()
print("Data inserted!")

cursor.close()
conn.close()