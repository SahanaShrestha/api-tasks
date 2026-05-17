import csv
import os

def export_to_txt(results):
    try:
        os.makedirs("output", exist_ok=True)

        with open("output/report.txt", "w") as f:
            f.write("Weather Data Analysis Report\n")
            f.write("="*40 + "\n\n")

            # 1. Highest avg temp
            f.write(f"Highest Avg Temp City: {results['highest_avg_temp']}\n\n")

            # 2. Hottest day
            f.write(f"Hottest Day: {results['hottest_day']}\n\n")

            # 3. High temp difference
            f.write("Days with Temp Difference > 10°C:\n")
            for row in results["high_temp_diff"]:
                f.write(str(row) + "\n")

        print("TXT report created.")

    except Exception as e:
        print("Error writing TXT:", e)


def export_to_csv(results):
    try:
        os.makedirs("output", exist_ok=True)

        with open("output/report.csv", "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow(["Type", "City", "Date", "Value"])

            # Highest avg
            city, avg = results["highest_avg_temp"]
            writer.writerow(["Highest Avg Temp", city, "-", avg])

            # Hottest day
            city, date, temp = results["hottest_day"]
            writer.writerow(["Hottest Day", city, date, temp])

            # Temp diff rows
            for city, date, diff in results["high_temp_diff"]:
                writer.writerow(["Temp Diff >10", city, date, diff])

        print("CSV report created.")

    except Exception as e:
        print("Error writing CSV:", e)