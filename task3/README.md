# Task 3 – Real API + Weather Analysis

> **Difficulty:** Hard | **Est. Time:** 2–3 hours  
> **Branch:** `task-3-weather` (or as assigned)

---

## 📋 Overview

This script uses the **Open-Meteo API** (free, no API key required) to fetch a **7-day weather forecast** for Kathmandu, Nepal. It saves the data to a CSV file, finds the **hottest and coldest day**, and writes a full summary to a `.txt` file.

---

## 📁 Files

| File | Description |
|------|-------------|
| `weather_analysis.py` | Main script – fetch, save, analyze, summarize |
| `weather.csv` | Generated – date + max daily temperature |
| `weather_summary.txt` | Generated (Bonus) – plain text summary report |

---

## ⚙️ Requirements

```bash
pip install requests
```

Python 3.x — `csv` and `os` are standard library modules.

---

## ▶️ How to Run

```bash
python weather_analysis.py
```

No API key needed. Open-Meteo is completely free and open.

---

## 🔄 What the Script Does (Step by Step)

1. **API Call** – GET request to `https://api.open-meteo.com/v1/forecast`
2. **Parameters used:**
   - `latitude=27.7172` (Kathmandu)
   - `longitude=85.3240` (Kathmandu)
   - `daily=temperature_2m_max`
   - `timezone=Asia/Kathmandu`
   - `forecast_days=7`
3. **Save to CSV** – Writes `date` and `max_temp_celsius` columns to `weather.csv`
4. **Analyze** – Finds the max and min temperature across the 7 days
5. **Print results** – Shows hottest and coldest day in terminal
6. **Bonus** – Saves full summary report to `weather_summary.txt`

---

## 📊 Sample Output

```
🌤️  Fetching 7-day weather forecast for Kathmandu...
✅ Data fetched successfully!

📄 Weather data saved to 'weather.csv'

📅 7-Day Forecast for Kathmandu:
Date            Max Temp (°C)
------------------------------
2025-04-22      28.4°C
2025-04-23      29.1°C
2025-04-24      27.6°C
...

🔥 Hottest Day : 2025-04-23 → 29.1°C
🧊 Coldest Day : 2025-04-24 → 27.6°C

📝 Summary saved to 'weather_summary.txt'

✅ Task 3 Complete! Deliverables: weather.csv + weather_summary.txt + this script
```

---

## 🌐 API Reference

- **Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Docs:** [https://open-meteo.com/en/docs](https://open-meteo.com/en/docs)
- **No API key required**

---

## ✅ Deliverables

- [x] `weather.csv` — 7-day forecast with date and max temperature
- [x] `weather_summary.txt` — human-readable summary (Bonus ✨)
- [x] `weather_analysis.py` — working analysis script
