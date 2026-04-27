import pandas as pd
from datetime import datetime, timedelta

# Load CSV (ONLY source of truth)
df = pd.read_csv("headlines.csv")

print("\nTOTAL HEADLINES:", len(df))

# ---------------------------
# 1. Which country has most headlines?
# ---------------------------
print("\n1. Headlines per country:")
country_counts = df["country"].value_counts()
print(country_counts)

# ---------------------------
# 2. Average words per headline per country
# ---------------------------
df["word_count"] = df["title"].astype(str).apply(lambda x: len(x.split()))

print("\n2. Average headline length per country:")
avg_words = df.groupby("country")["word_count"].mean()
print(avg_words)

# ---------------------------
# 3. Headlines appearing in multiple countries
# ---------------------------
print("\n3. Cross-country duplicate headlines:")
duplicates = df.groupby("title")["country"].nunique()
multi_country = duplicates[duplicates > 1]
print(multi_country)

# ---------------------------
# 4. Most common news source
# ---------------------------
print("\n4. Top news source:")
print(df["source"].value_counts().head(1))

# ---------------------------
# 5. Last 6 hours vs older
# ---------------------------
df["publishedat"] = pd.to_datetime(df["publishedat"], errors="coerce", utc=True)

from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
six_hours_ago = now - timedelta(hours=6)

recent = df[df["publishedat"] >= six_hours_ago]
older = df[df["publishedat"] < six_hours_ago]

print("\n5. Time analysis:")
print("Recent (%):", len(recent) / len(df) * 100 if len(df) > 0 else 0)
print("Older (%):", len(older) / len(df) * 100 if len(df) > 0 else 0)

# ---------------------------
# 6. Filter headlines > 6 words
# ---------------------------
filtered = df[df["word_count"] > 6]
filtered.to_csv("filtered_headlines.csv", index=False)

print("\n6. Headlines > 6 words:", len(filtered))

# ---------------------------
# 7. Longest vs shortest average headline country
# ---------------------------
print("\n7. Longest vs shortest headlines:")
avg_length = df.groupby("country")["word_count"].mean()

print("Longest:", avg_length.idxmax())
print("Shortest:", avg_length.idxmin())