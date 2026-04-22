import requests
import csv
import os

# Kathmandu coordinates
LATITUDE = 27.7172
LONGITUDE = 85.3240
CITY = "Kathmandu"

# Step 1: Fetch 7-day forecast from Open-Meteo API (no API key needed)
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "daily": "temperature_2m_max",
    "timezone": "Asia/Kathmandu",
    "forecast_days": 7
}

print(f"🌤️  Fetching 7-day weather forecast for {CITY}...")
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Data fetched successfully!\n")
else:
    print(f" Failed to fetch weather data. Status: {response.status_code}")
    exit()

# Step 2: Extract dates and max temperatures
dates = data["daily"]["time"]
max_temps = data["daily"]["temperature_2m_max"]

# Step 3: Save date + max_temp to weather.csv
csv_filename = "weather.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["date", "max_temp_celsius"])
    for date, temp in zip(dates, max_temps):
        writer.writerow([date, temp])

print(f" Weather data saved to '{csv_filename}'\n")

# Print the 7-day forecast
print(" 7-Day Forecast for Kathmandu:")
print(f"{'Date':<15} {'Max Temp (°C)'}")
print("-" * 30)
for date, temp in zip(dates, max_temps):
    print(f"{date:<15} {temp}°C")

# Step 4: Find hottest and coldest day
hottest_index = max_temps.index(max(max_temps))
coldest_index = min_temps_index = max_temps.index(min(max_temps))

hottest_day = dates[hottest_index]
hottest_temp = max_temps[hottest_index]
coldest_day = dates[coldest_index]
coldest_temp = max_temps[coldest_index]

print(f"\n Hottest Day : {hottest_day} → {hottest_temp}°C")
print(f" Coldest Day : {coldest_day} → {coldest_temp}°C")

# Step 5 (Bonus): Save summary to a .txt file
summary_filename = "weather_summary.txt"
with open(summary_filename, "w", encoding="utf-8") as f:
    f.write(f"Weather Summary for {CITY}\n")
    f.write("=" * 40 + "\n\n")
    f.write(f"7-Day Forecast:\n")
    f.write(f"{'Date':<15} Max Temp (°C)\n")
    f.write("-" * 30 + "\n")
    for date, temp in zip(dates, max_temps):
        f.write(f"{date:<15} {temp}°C\n")
    f.write("\n" + "=" * 40 + "\n")
    f.write(f"Hottest Day : {hottest_day} → {hottest_temp}°C\n")
    f.write(f"Coldest Day : {coldest_day} → {coldest_temp}°C\n")

print(f"\n Summary saved to '{summary_filename}'")
print("\n Task 3 Complete! Deliverables: weather.csv + weather_summary.txt + this script")
