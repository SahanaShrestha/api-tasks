from db import create_table, store_data
from api import fetch_data
from queries import run_queries
from export import export_to_txt, export_to_csv

def main():
    try:
        print("Starting Task 5 pipeline...\n")

        # Step 1: Prepare DB
        print("Setting up database...")
        create_table()

        # Step 2: Fetch API data
        print("Fetching weather data...")
        data = fetch_data()

        if not data:
            print("No data fetched. Exiting.")
            return

        # Step 3: Store in DB
        print("Storing data in database...")
        store_data(data)

        # Step 4: Run queries
        print("Running analysis queries...")
        results = run_queries()

        if not results:
            print("No results generated. Exiting.")
            return

        # Step 5: Export results
        print("Exporting reports...")
        export_to_txt(results)
        export_to_csv(results)

        print("\n✅ Task 5 completed successfully!")

    except Exception as e:
        print("Unexpected error in pipeline:", e)


if __name__ == "__main__":
    main()