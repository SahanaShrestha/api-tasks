import requests
import csv
import os

# Step 1: Fetch posts from JSONPlaceholder API
url = "https://jsonplaceholder.typicode.com/posts"
response = requests.get(url)

if response.status_code == 200:
    posts = response.json()
    print(f" Fetched {len(posts)} posts successfully.\n")
else:
    print(f" Failed to fetch posts. Status code: {response.status_code}")
    exit()

# Step 2: Save all posts to posts.csv (columns: id, title, body)
csv_filename = "posts.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["id", "title", "body"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for post in posts:
        writer.writerow({
            "id": post["id"],
            "title": post["title"],
            "body": post["body"]
        })

print(f" Saved all posts to '{csv_filename}'")

# Step 3: Read back with DictReader and filter posts where title has more than 5 words
filtered_posts = []
with open(csv_filename, "r", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        word_count = len(row["title"].split())
        if word_count > 5:
            filtered_posts.append(row)

print(f"\n Found {len(filtered_posts)} posts with title longer than 5 words:\n")
for post in filtered_posts:
    print(f"  ID {post['id']}: {post['title']}")

# Step 4: Write filtered posts to a new CSV
filtered_csv = "filtered_posts.csv"
with open(filtered_csv, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["id", "title", "body"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered_posts)

print(f"\n Filtered posts saved to '{filtered_csv}'")
print(f"   Total filtered: {len(filtered_posts)} posts")
