from fetch_news import fetch_country_data
import pandas as pd
import hashlib

countries = {
    "nepal": "np",
    "india": "in",
    "usa": "us",
    "uk": "gb",
    "australia": "au"
}

def generate_id(title, source, country):
    return hashlib.md5(f"{title}-{source}-{country}".encode()).hexdigest()

all_data = []

for country_name, code in countries.items():
    articles = fetch_country_data(code)

    for article in articles:
        title = article.get("title") or "N/A"
        source = article.get("source", {}).get("name") or "N/A"
        published = article.get("publishedAt") or "N/A"

        all_data.append({
            "id": generate_id(title, source, country_name),
            "country": country_name,
            "title": title,
            "source": source,
            "publishedat": published
        })

df = pd.DataFrame(all_data)
df = df.drop_duplicates(subset=["id"])
df.to_csv("headlines.csv", index=False)

print("Saved headlines.csv:", len(df))