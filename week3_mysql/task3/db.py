import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host="localhost",
    user=os.getenv("task3user"),
    password=os.getenv("1234"),
    database=os.getenv("TASK3_DB")
)