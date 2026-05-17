# Task 2 – Fetch & Save to CSV

> **Difficulty:** Medium | **Est. Time:** ~1 hour  
> **Branch:** `task-2-csv`

---

## 📋 Overview

This script fetches all posts from the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/posts), saves them to a CSV file, reads the CSV back, filters posts whose **title contains more than 5 words**, and saves those filtered results to a second CSV.

---

## 📁 Files

| File | Description |
|------|-------------|
| `fetch_posts.py` | Main script – fetches, saves, filters, and exports |
| `posts.csv` | Generated – all 100 posts (id, title, body) |
| `filtered_posts.csv` | Generated – only posts with title > 5 words |

---

## ⚙️ Requirements

```bash
pip install requests
```

Python 3.x — `csv` is part of the standard library, no extra install needed.

---

## ▶️ How to Run

```bash
python fetch_posts.py
```

---

## 🔄 What the Script Does (Step by Step)

1. **Fetch** – GET request to `https://jsonplaceholder.typicode.com/posts`
2. **Check status** – Confirms `status_code == 200`
3. **Save to CSV** – Writes all 100 posts to `posts.csv` with columns: `id`, `title`, `body`
4. **Read back** – Uses `csv.DictReader` to read `posts.csv`
5. **Filter** – Keeps only posts where `len(title.split()) > 5`
6. **Export** – Saves filtered posts to `filtered_posts.csv`

---

## 📊 Sample Output

```
✅ Fetched 100 posts successfully.

📄 Saved all posts to 'posts.csv'

🔍 Found 68 posts with title longer than 5 words:

  ID 1: sunt aut facere repellat provident occaecati excepturi optio
  ...

✅ Filtered posts saved to 'filtered_posts.csv'
   Total filtered: 68 posts
```

---

## ✅ Deliverables

- [x] `posts.csv` — all posts saved
- [x] `filtered_posts.csv` — filtered posts (title > 5 words)
- [x] `fetch_posts.py` — working script
