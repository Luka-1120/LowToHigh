from database import get_db_connection
import os

# Absolute path
from database import DB_PATH
print("Python is using DB:", DB_PATH)

# გამოიტანოს ყველა მომხმარებელი
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, first_name, last_name, email, phone, created_at FROM users")
rows = cursor.fetchall()
conn.close()

if rows:
    print("\nRegistered users:")
    for row in rows:
        print(f"ID: {row['id']}, Name: {row['first_name']} {row['last_name']}, Email: {row['email']}, Phone: {row['phone']}, Created: {row['created_at']}")
else:
    print("No users found in the database.")
