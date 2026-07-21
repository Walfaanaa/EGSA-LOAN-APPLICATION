import streamlit as st
import sqlite3
import pandas as pd

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="EGSA Loan Management System",
    page_icon="💰",
    layout="wide"
)

DB_NAME = "loan_applications.db"

ADMIN_PASSWORD = "admin123"

# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():

    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# =====================================================
# CREATE TABLE
# =====================================================

def init_db():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT,

        national_id TEXT,

        phone TEXT,

        staff_status TEXT,

        monthly_salary REAL,

        loan_amount REAL,

        duration INTEGER,

        interest_rate REAL,

        interest_amount REAL,

        monthly_payment REAL,

        total_payment REAL,

        repayment_date TEXT,

        loan_end_date TEXT,

        guarantor_name TEXT,

        guarantor_id TEXT,

        guarantor_phone TEXT,

        support_letter BLOB,

        photo BLOB,

        submitted_date TEXT,

        status TEXT DEFAULT 'Pending',

        admin_comment TEXT,

        notified INTEGER DEFAULT 0

    )
    """)

    conn.commit()

    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

conn = init_db()
