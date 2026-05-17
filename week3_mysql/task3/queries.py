import mysql.connector
conn = mysql.connector.connect(
    host="localhost",
    user="task3user",
    password="1234",
    database="weather_db"
)
cursor = conn.cursor()

with open("summary.txt", "w") as f:

    # Query 1
    cursor.execute("""
        SELECT city, AVG(max_temp)
        FROM forecasts
        GROUP BY city
        ORDER BY AVG(max_temp) DESC
        LIMIT 1;
    """)
    result1 = cursor.fetchone()
    f.write(f"Highest Avg Temp City: {result1}\n")

    # Query 2
    cursor.execute("""
        SELECT city, date, max_temp
        FROM forecasts
        ORDER BY max_temp DESC
        LIMIT 1;
    """)
    result2 = cursor.fetchone()
    f.write(f"Hottest Day: {result2}\n")

    # Query 3
    cursor.execute("""
        SELECT city, date, (max_temp - min_temp)
        FROM forecasts
        WHERE (max_temp - min_temp) > 10;
    """)
    result3 = cursor.fetchall()
    f.write("High Temp Difference Days:\n")
    for row in result3:
        f.write(str(row) + "\n")

cursor.close()
conn.close()

print("Summary saved!")