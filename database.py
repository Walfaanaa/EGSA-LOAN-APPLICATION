# update_db.py
# This script safely adds 'monthly_payment' column to your database if missing.

import sqlite3

DB_PATH = "loan_applications.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Add the column if not already in the table
try:
    cur.execute("ALTER TABLE applications ADD COLUMN monthly_payment REAL")
    print("✅ 'monthly_payment' column added successfully.")
except sqlite3.OperationalError:
    print("ℹ️ Column 'monthly_payment' already exists — no changes made.")

conn.commit()
conn.close()
