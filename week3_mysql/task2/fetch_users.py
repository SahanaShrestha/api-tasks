import requests

def fetch_users():
    url = "https://jsonplaceholder.typicode.com/users"
    response = requests.get(url)
    return response.json()