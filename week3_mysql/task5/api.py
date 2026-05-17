import requests

def fetch_data():
    cities = {
        "Kathmandu": (27.7172, 85.3240),
        "Delhi": (28.6139, 77.2090),
        "Tokyo": (35.6762, 139.6503)
    }

    all_data = []

    for city, (lat, lon) in cities.items():
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"

            response = requests.get(url, timeout=10)

            # check HTTP error
            if response.status_code != 200:
                print(f"API error for {city}: {response.status_code}")
                continue

            data = response.json()

            dates = data["daily"]["time"]
            max_temps = data["daily"]["temperature_2m_max"]
            min_temps = data["daily"]["temperature_2m_min"]

            for i in range(7):
                all_data.append({
                    "city": city,
                    "date": dates[i],
                    "max_temp": max_temps[i],
                    "min_temp": min_temps[i]
                })

        except Exception as e:
            print(f"Error fetching data for {city}:", e)

    return all_data