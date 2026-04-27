import requests

API_KEY = "a48eb87ffd9102eba6f35bf6024d034c"

def fetch_country_data(country_code):
    url = f"https://gnews.io/api/v4/top-headlines?country={country_code}&token={API_KEY}&lang=en&max=10"
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error:", response.text)
        return []

    data = response.json()
    return data.get("articles", [])