import mysql.connector
from dotenv import load_dotenv
import os
import csv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

# Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS store_db")
cursor.execute("USE store_db")

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    city VARCHAR(100)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price FLOAT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

# Insert data
customers = [
    ("Alice", "Kathmandu"), ("Bob", "Pokhara"), ("Charlie", "Lalitpur"),
    ("David", "Kathmandu"), ("Eva", "Bhaktapur"), ("Frank", "Pokhara"),
    ("Grace", "Lalitpur"), ("Hannah", "Kathmandu"), ("Ian", "Bhaktapur"),
    ("Jack", "Pokhara")
]

products = [
    ("Laptop", 1000), ("Phone", 500), ("Tablet", 300),
    ("Headphones", 100), ("Keyboard", 50), ("Mouse", 25),
    ("Monitor", 200), ("Printer", 150)
]

orders = [
    (1,1,2),(2,2,1),(3,3,4),(4,1,1),(5,2,3),
    (6,4,2),(7,5,1),(8,6,5),(9,7,2),(10,8,1),
    (1,2,2),(2,3,3),(3,4,1),(4,5,2),(5,6,4),
    (6,7,1),(7,8,2),(8,1,3),(9,2,1),(10,3,2)
]

cursor.executemany("INSERT INTO customers (name, city) VALUES (%s, %s)", customers)
cursor.executemany("INSERT INTO products (name, price) VALUES (%s, %s)", products)
cursor.executemany("INSERT INTO orders (customer_id, product_id, quantity) VALUES (%s, %s, %s)", orders)

conn.commit()

# ----------------------------
# QUERIES
# ----------------------------

print("\n--- Total money spent per customer ---")
cursor.execute("""
SELECT c.name, SUM(p.price * o.quantity) AS total_spent
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
GROUP BY c.name
ORDER BY total_spent DESC
""")

results = cursor.fetchall()
for row in results:
    print(row)

# Export CSV
with open("revenue_report.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Customer", "Total Spent"])
    writer.writerows(results)

print("\n--- Most ordered product ---")
cursor.execute("""
SELECT p.name, SUM(o.quantity) AS total_qty
FROM orders o
JOIN products p ON o.product_id = p.id
GROUP BY p.name
ORDER BY total_qty DESC
LIMIT 1
""")
print(cursor.fetchone())

print("\n--- Customers with more than 2 orders ---")
cursor.execute("""
SELECT c.name, COUNT(*) as order_count
FROM orders o
JOIN customers c ON o.customer_id = c.id
GROUP BY c.name
HAVING COUNT(*) > 2
""")
for row in cursor.fetchall():
    print(row)

print("\n--- Average order value per city ---")
cursor.execute("""
SELECT c.city, AVG(p.price * o.quantity)
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
GROUP BY c.city
""")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()