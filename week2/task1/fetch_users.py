import requests

url = "https://jsonplaceholder.typicode.com/users"

response = requests.get(url)

# Check status code
if response.status_code == 200:
    users = response.json()

    for user in users:
        name = user["name"]
        email = user["email"]
        city = user["address"]["city"]

        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"City: {city}")
        print("-" * 30)

else:
    print("Failed to fetch data")