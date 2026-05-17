import requests
import mysql.connector
from datetime import datetime

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="task3user",
    password="1234",
    database="weather_db"
)
cursor = conn.cursor()

# Cities (lat, lon)
cities = {
    "Kathmandu": (27.7172, 85.3240),
    "Delhi": (28.6139, 77.2090),
    "Tokyo": (35.6762, 139.6503)
}

for city, (lat, lon) in cities.items():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    
    response = requests.get(url)
    data = response.json()

    dates = data["daily"]["time"]
    max_temps = data["daily"]["temperature_2m_max"]
    min_temps = data["daily"]["temperature_2m_min"]

    for i in range(7):
        cursor.execute("""
            INSERT INTO forecasts (city, date, max_temp, min_temp)
            VALUES (%s, %s, %s, %s)
        """, (city, dates[i], max_temps[i], min_temps[i]))

conn.commit()
cursor.close()
conn.close()

print("Data inserted successfully!")