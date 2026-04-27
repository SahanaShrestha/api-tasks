import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

print("API KEY LOADED:", API_KEY)  # DEBUG

def fetch_country_data(country_code):
    print("Fetching:", country_code)  # DEBUG

    url = f"https://gnews.io/api/v4/top-headlines?country={country_code}&token={API_KEY}&lang=en&max=5"

    response = requests.get(url)

    print("Status Code:", response.status_code)  # DEBUG

    data = response.json()

    print("Articles found:", len(data.get("articles", [])))  # DEBUG

    return data.get("articles", [])


# IMPORTANT: actually CALL the function
fetch_country_data("in")